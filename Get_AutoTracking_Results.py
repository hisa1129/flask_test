import AutoTracking
import Analysis_Results_Class
import Generate_Contour_Elem
import FindContourAnalysis
from CalculationLog import calculation_log
import datetime
import math
import numpy as np
import os
import cv2
import glob

INPUT_PARAMS_VER = '0.1.2' #入力パラメータバージョン、2020.10.21

auto_binarize = True #大津の二値化による自動閾値判定
binarize_thresh = 128 #二値化閾値（auto_binarize = Falseの時）
min_area_thresh = 1 #輪郭面積最小値（最小面積以下の輪郭はノイズと判定）
#輪郭解析に関する入力パラメータ
areaThresh_faced = 1500 #吐出開始検出時凸包面積差分閾値
areaThresh_separated = 2000 #サテライト液尾分離検出時凸包面積差分閾値
arclengthThresh = 25 #サテライト液尾分離検出時輪郭長差分閾値
solidity_ratio_thresh = 1.5 #サテライト液尾分離検出solidity比閾値
noise_remove_topological_dist_thresh = 20 #輪郭ノイズ除去時位相空間上ノイズ距離
noise_remove_area_thresh = 40 #輪郭ノイズ除去時面積上限値

#輪郭抽出前処理に関する入力パラメータ
input_params_dic = {
    "auto_binarize":auto_binarize,
    "binarize_thresh":binarize_thresh,
    "min_area_thresh":min_area_thresh,
    "areaThresh_faced":areaThresh_faced,
    "areaThresh_separated":areaThresh_separated,
    "arclengthThresh":arclengthThresh,
    "solidity_ratio_thresh":solidity_ratio_thresh,
    "noise_remove_topological_dist_thresh":noise_remove_topological_dist_thresh,
    "noise_remove_area_thresh":noise_remove_area_thresh,
}

THRESH_VALUES_VER = '0.1.3' #閾値パラメータバージョン、2020.10.21

#吐出状態判定時閾値
velocity_upperthresh = 8.5 #吐出速度上限[m/s]
velocity_lowerthresh = 4.5 #吐出速度下限[m/s]
Solidity_upperthresh = 1.016 #ノズル輪郭Solidity値上限、上限以上のSolidityで異物判定
velocity_septhresh = 6.5 #粘弾性判定、速度閾値。閾値以上で候補吐出に入れる。
sep_thresh = 300.0 #粘弾性判定、液滴分離閾値。閾値以上で候補吐出に入れる。velocity > velocity_septhresh かつ sep_delay > sep_threshで粘弾性の疑い。 
diff_angle_thresh = 1.753 #メイン - サテライト液滴吐出角度差閾値（90%の吐出が下記角度差範囲に入る値を採用）
pix_mirgin = 20 #逸脱吐出検出判定

thresh_values_dic = {
    "velocity_upperthresh":velocity_upperthresh,
    "velocity_lowerthresh":velocity_lowerthresh,
    "Solidity_upperthresh":Solidity_upperthresh,
    "velocity_septhresh":velocity_septhresh,
    "sep_thresh":sep_thresh,
    "diff_angle_thresh":diff_angle_thresh,
    "pix_mirgin":pix_mirgin,
}


#解析拡張パラメータ
num_div_velocity_layer = 5 #液滴速度測定区分数


#デバッグモード指定文字列、exec_mdoe == DEBUG_MODEでデバッグモード処理
DEBUG_MODE = 'DEBUG'

def comparison_images(file1_path, file2_path, exec_mode = DEBUG_MODE, delay = 100):
    flag_debug_mode = exec_mode == DEBUG_MODE 
    image1_contours = Generate_Contour_Elem.analyse_Image(delay,
                                                          file1_path,
                                                          input_params_dic['min_area_thresh'],
                                                          input_params_dic['binarize_thresh'],
                                                          input_params_dic['auto_binarize'],
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode)

    image2_contours = Generate_Contour_Elem.analyse_Image(delay,
                                                          file2_path,
                                                          input_params_dic['min_area_thresh'],
                                                          input_params_dic['binarize_thresh'],
                                                          input_params_dic['auto_binarize'],
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode,
                                                          flag_debug_mode)
    ret_result = {
        "diff_main_X" : str(image1_contours.max_mainX - image2_contours.max_mainX),
        "diff_main_Y" : str(image1_contours.max_mainY - image2_contours.max_mainY),
        "diff_satellite_X" : str(image1_contours.satellite_suspicious_X - image2_contours.satellite_suspicious_X),
        "diff_satellite_Y" : str(image1_contours.satellite_suspicious_Y - image2_contours.satellite_suspicious_Y),
        "diff_regament_length" : str(image1_contours.max_reg_length_in_delay - image2_contours.max_reg_length_in_delay),
    }
    
    return ret_result
    

def get_autoTracking_Results(directory_path, camera_resolution, API_VER, exec_mode):
    '''
    追尾→特徴量抽出関数   
    ・パラメータ：dirpath : str
                    ディレクトリパス
                camera_resolution : float
                    カメラ分解能、[um/pix]
                exec_mode : str
                    起動モード、DEBUGでデバッグモード、文字列等出力


    '''
    
    flag_is_debugmode = (exec_mode == DEBUG_MODE) #デバッグモードの指定確認。
    if flag_is_debugmode:
        calculation_log('analyse dir path = {}'.format(directory_path))
        calculation_log('exec_mode = {}'.format(exec_mode))
    flag_contour_select_was_done = False
    if flag_is_debugmode:
        calculation_log('contour selection function is calling')

    #輪郭抽出計算の実施。
    try:
        contour_rsts, flag_image_modified_deeply = FindContourAnalysis.analyse_Images_List(
            directoryPath = directory_path,
            min_area_thresh = input_params_dic["min_area_thresh"],
            binarize_thresh = input_params_dic["binarize_thresh"],
            auto_binarize = input_params_dic["auto_binarize"],
            area_mirgin_detect_faced = input_params_dic["areaThresh_faced"],
            area_mirgin_detect_separation = input_params_dic["areaThresh_separated"],
            arc_length_mirgin_detect_separation = input_params_dic["arclengthThresh"],
            solidity_mirgin_detect_separation = input_params_dic["solidity_ratio_thresh"],
            noise_remove_topological_dist_thresh = input_params_dic["noise_remove_topological_dist_thresh"],
            noise_remove_area_thresh = input_params_dic["noise_remove_area_thresh"],
            mkdir = flag_is_debugmode,
            draw_contour = flag_is_debugmode,
            draw_convexhull = flag_is_debugmode,
            draw_coords = flag_is_debugmode,
            exportImage = flag_is_debugmode,
            draw_reg_Detected = flag_is_debugmode,
            DEBUG = flag_is_debugmode)
        
        flag_contour_select_was_done = True
        if flag_is_debugmode:
            calculation_log('contour selection was done')
        if contour_rsts is None:
            result = {
                "analysis_date_time":nan_to_minus1(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')),
                "file_name":nan_to_minus1(directory_path),
                "condition":"num_files are not more than 2.",
                "camera_resolution[um/pix]":nan_to_minus1(camera_resolution),
                "API_VER":nan_to_minus1(API_VER),
                "CONTOUR_CODE_VER":nan_to_minus1(FindContourAnalysis.get_code_ver()),
                "AUTO_TRACKING_CODE_VER":nan_to_minus1(AutoTracking.get_code_ver()),
                "THRESH_VALUES_VER":THRESH_VALUES_VER,
            }
            return result        
        
    #輪郭抽出失敗時処理
    except:
        if flag_is_debugmode:
            calculation_log('contour_selection was failure.')
        result = {
            "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
            "filename":directory_path.split('/')[-1],
            'condition' : 'contour selection was failure.' 
        }
    
    #輪郭抽出成功→疑似追尾実行
    if flag_contour_select_was_done:
        flag_tracking_was_done = False
        #疑似追尾実施。
        try:
            trackingResults = AutoTracking.auto_Tracking(
                dirPath = directory_path,
                rsts = contour_rsts,
                draw_Tracking_Results = flag_is_debugmode,
                draw_Fitting_Line = flag_is_debugmode,
                DEBUG = flag_is_debugmode)  
            flag_tracking_was_done = True
            if flag_is_debugmode:
                calculation_log('auto_tracking was done')
        #疑似追尾失敗時処理
        except:
            if flag_is_debugmode:
                calculation_log('auto_tracking was failed')
            result = {
                "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
                "filename":directory_path.split('/')[-1],
                'condition' : 'auto_tracking was failure.'
            }
        
        ##以下、吐出開始、分離検知ディレイ修正コマンド
        ##テスト版につきしばらく実行しない。
        
        #疑似追尾成功→特徴量計算
        if flag_tracking_was_done:
            try:                              
                #出力用の値の整理
                #ファイル名取得
                directory_path_show = directory_path.split('/')[-1]
                if flag_is_debugmode:
                    calculation_log('dir_path is {}'.format(directory_path_show))
                
                #1枚目輪郭数取得               
                num_first_contours = (float)(sum(contour_rsts.num_contours_at_first))/(float)(len(contour_rsts.num_contours_at_first))
                if flag_is_debugmode:
                    calculation_log('num_first_contours is {}'.format(num_first_contours))
                #solidity値取得
                solidity = contour_rsts.solidity
                if flag_is_debugmode:
                    calculation_log('solidity is {}'.format(solidity))
                #arc_solidity値取得
                arc_solidity = contour_rsts.arc_solidity
                if flag_is_debugmode:
                    calculation_log('arc_solidity is {}'.format(arc_solidity))
                #液滴吐出開始検知有無およびディレイ取得
                flag_droplet_faced, faced_delay = contour_rsts.flag_faced_is_detected, contour_rsts.delay_faced
                if flag_is_debugmode:
                    calculation_log('faced_delay is {} and flag_droplet_faced is {}'.format(faced_delay, flag_droplet_faced))
                #液滴分離検知有無およびディレイ取得                
                flag_droplet_separated, separated_delay = contour_rsts.flag_separated_is_detected, contour_rsts.delay_separated
                if flag_is_debugmode:
                    calculation_log('separated delay is {} and flag_separated_delay is {}'.format(separated_delay, flag_droplet_separated))
                #最大リガメント長さおよびディレイ取得
                max_regament_length_delay, max_regament_length = contour_rsts.delay_max_regament_detected, contour_rsts.max_regament_length
                if flag_is_debugmode:
                    calculation_log('max_remament_length_delay is {} and the length is {}'.format(max_regament_length_delay, max_regament_length))
                #メイン液滴平均速度および標準偏差取得               
                main_average_velocity, main_velocity_stdiv = trackingResults.Get_Main_Velocity()
                if flag_is_debugmode:
                    calculation_log('main_ave_velocity is {} and main_velocity_stdiv is {}'.format(main_average_velocity, main_velocity_stdiv))
                #メイン液滴角度取得 
                main_angle = trackingResults.Get_Main_Angle_degrees()
                if flag_is_debugmode:
                    calculation_log('main_angle is {}'.format(main_angle))
                #サテライト液滴平均速度および標準偏差取得 
                satellite_average_velocity, satellite_velocity_stdiv = trackingResults.Get_Satellite_Velocity()
                if flag_is_debugmode:
                    calculation_log('satellite_ave_velocity is {} and satellite_velocity_stdiv is {}'.format(satellite_average_velocity, satellite_velocity_stdiv))
                #サテライト液滴角度取得
                satellite_angle = trackingResults.Get_Satellite_Angle_degrees()
                if flag_is_debugmode:
                    calculation_log('satellite_angle is {}'.format(satellite_angle))
                #実メイン液滴速度取得
                main_average_velocity_stdized = main_average_velocity * camera_resolution
                if flag_is_debugmode:
                    calculation_log('main_ave_vel_stdized is {}'.format(main_average_velocity_stdized))
                #実サテライト液滴速度取得
                satellite_average_velocity_stdized = satellite_average_velocity * camera_resolution
                if flag_is_debugmode:
                    calculation_log('satellite_ave_vel_stdized is {}'.format(satellite_average_velocity_stdized))
                #メイン-サテライト液滴角度差取得
                diff_angle = abs(inf_to_value(main_angle) - inf_to_value(satellite_angle))
                if flag_is_debugmode:
                    calculation_log('diff_angle is {}'.format(diff_angle))
                #逸脱液滴検出
                flag_exotic_droplet, max_exotic_area = contour_rsts.Check_exotic_droplet_exists(
                    trackingResults,
                    thresh_values_dic['pix_mirgin'])
                if flag_is_debugmode:
                    calculation_log('flag exotic droplet is {}'.format(flag_exotic_droplet))
                #5分割領域ごとの各液滴速度、標準偏差取得
                y_max = contour_rsts.analysisResults[0].contours[0].imgYMax
                if flag_is_debugmode:
                    calculation_log('y_max = {}'.format(y_max))
                y_diff = (float)(y_max) / (float)(num_div_velocity_layer)
                if flag_is_debugmode:
                    calculation_log('y_diff = {}'.format(y_diff))
                vel_add_dics = []
                for i in range(num_div_velocity_layer):
                    base = i * y_diff
                    top = (i + 1) * y_diff
                    main_vel_res = trackingResults.Get_Main_Velocity(base, top)
                    sat_vel_res = trackingResults.Get_Satellite_Velocity(base,top)
                    vel_add_dics.append({
                        "layered_main_{}_ave[pix/us]".format(i):nan_to_minus1(main_vel_res[0]),
                        "layered_main_{}_stdiv[pix/us]".format(i):nan_to_minus1(main_vel_res[1]),
                        "layered_sat_{}_ave[pix/us]".format(i):nan_to_minus1(sat_vel_res[0]),
                        "layered_sat_{}_ave[pix/us]".format(i):nan_to_minus1(sat_vel_res[1]),                        
                    })
                    if flag_is_debugmode:
                        calculation_log('dic_elem_{} was generated as {}'.format(i, vel_add_dics[i]))
                
                #以下、テストコード
                leg_ref = (nan_to_minus1(contour_rsts.delay_separated) - nan_to_minus1(contour_rsts.delay_faced)) * nan_to_minus1(main_average_velocity)
                leg_eval_ratio = nan_to_minus1(leg_ref) / nan_to_minus1(max_regament_length)
                print("leg_ref_is calculated")
                if nan_to_minus1(leg_eval_ratio) < 0:
                    leg_eval_ratio = -1
                contour_rsts.modify_faced_delay_and_freq_Y(trackingResults)
                contour_rsts.modify_separated_delay(trackingResults)
                print('modified_calculated')
                try:
                    max_main_angle_disturbance = max([abs(angle_elem - main_angle) for angle_elem in contour_rsts.get_main_angle_list(trackingResults)])
                    max_satellite_angle_disturbance = max([abs(angle_elem - satellite_angle) for angle_elem in contour_rsts.get_satellite_angle_list(trackingResults)])
                except:
                    max_main_angle_disturbance = -1
                    max_satellite_angle_disturbance = - 1
                try:
                    if flag_is_debugmode:
                        print('draw start, directory_path is {}'.format(directory_path))
                        if not os.path.exists(directory_path + "/drawModifiedNozzleXY"):
                            print('makedirs start for {}'.format(directory_path + "/drawModifiedNozzleXY"))
                            os.makedirs(directory_path + "/drawModifiedNozzleXY", exist_ok = True)
                            if flag_is_debugmode:
                                calculation_log('mkdir at {}/drawModifiedNozzleXY'.format(directory_path))
                        print("globbing")
                        pathes = glob.glob(directory_path + "/*.jpg")
                        print("globed")
                        signature_size = 5
                        print("path is {}".format(pathes[0]))
                        im = cv2.imread(pathes[0])
                        print("imread")
                        x = contour_rsts.modified_freq_X
                        y = contour_rsts.modified_freq_Y
                        im = cv2.rectangle(im,((int)(x-signature_size),(int)(y-signature_size)),((int)(x+signature_size),(int)(y+signature_size)),\
                               (0,0,255),3)
                        print('imdrawn')
                        savePath = directory_path + "/drawModifiedNozzleXY/" + os.path.splitext(os.path.basename(pathes[0]))[0] + "_modifiedXY.jpg"
                        print('export succeed.')
                        cv2.imwrite(savePath, im)
                        del im
                except:
                    calculation_log('drawing_modofied_XY_failure')
                    
                #テストコード、ここまで
                    
                #dictionaryへの出力
                result = {
                    "analysis_date_time":nan_to_minus1(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')),
                    "file_name":nan_to_minus1(directory_path_show),
                    "condition":"calculation was done.",
                    "camera_resolution[um/pix]":nan_to_minus1(camera_resolution),
                    "API_VER":nan_to_minus1(API_VER),
                    "ave_num_contours_before_separation":nan_to_minus1(num_first_contours),
                    "solidity[U]":nan_to_minus1(solidity),
                    "arc_solidity[u]":nan_to_minus1(arc_solidity),
                    "flag_droplet_faced":nan_to_minus1(flag_droplet_faced),
                    "faced_delay[us]":nan_to_minus1(faced_delay),
                    "flag_droplet_separated":nan_to_minus1(flag_droplet_separated),
                    "separated_delay[us]":nan_to_minus1(separated_delay),
                    "max_regament_delay[us]":nan_to_minus1(max_regament_length_delay),
                    "max_regament_length[pix]":nan_to_minus1(max_regament_length),
                    "most_freq_Y[pix]":nan_to_minus1(contour_rsts.freq_Y),
                    "CONTOUR_CODE_VER":nan_to_minus1(FindContourAnalysis.get_code_ver()),
                    "main_average_velocity[pix/us]":nan_to_minus1(main_average_velocity),
                    "main_average_velocity[m/s]":nan_to_minus1(main_average_velocity_stdized),
                    "main_velocity_stddiv[pix/us]":nan_to_minus1(main_velocity_stdiv),
                    "main_angle[degrees]":nan_to_minus1(inf_to_value(main_angle)),
                    "satellite_average_velocity[pix/us]":nan_to_minus1(satellite_average_velocity),
                    "satellite_average_velocity[m/s]":nan_to_minus1(satellite_average_velocity_stdized),
                    "satellite_velocity_stddiv[pix/us]":nan_to_minus1(satellite_velocity_stdiv),
                    "satellite_angle[degrees]":nan_to_minus1(inf_to_value(satellite_angle)),
                    "main-satellite_angle_diff[degrees]":nan_to_minus1(diff_angle),
                    "main_linearity_error[pix]":nan_to_minus1(
                        inf_to_value(trackingResults.Get_MainXY_Fit_Error_Min_Max_Range()[1]) - inf_to_value(trackingResults.Get_MainXY_Fit_Error_Min_Max_Range()[0])),
                    "satellite_linearity_error[pix]":nan_to_minus1(
                        inf_to_value(trackingResults.Get_SatelliteXY_Fit_Error_Min_Max_Range()[1]) - inf_to_value(trackingResults.Get_SatelliteXY_Fit_Error_Min_Max_Range()[0])),
                    "AUTO_TRACKING_CODE_VER":nan_to_minus1(AutoTracking.get_code_ver()),
                    "anormaly_ejections_at_first_image":nan_to_minus1(num_first_contours > 1.5),
                    "main_velocity_is_too_fast":nan_to_minus1(main_average_velocity_stdized > thresh_values_dic['velocity_upperthresh']),
                    "main_velocity_is_too_slow":nan_to_minus1(main_average_velocity_stdized < thresh_values_dic['velocity_lowerthresh']),
                    "nozzle_needs_to_be_clean":nan_to_minus1(solidity > thresh_values_dic['Solidity_upperthresh']),
                    "suspicious_visco-elasticity":nan_to_minus1((separated_delay > thresh_values_dic["sep_thresh"]) and (main_average_velocity_stdized > thresh_values_dic["velocity_septhresh"])),
                    "angle-diff_is_too_large":nan_to_minus1((diff_angle > thresh_values_dic["diff_angle_thresh"]) if not math.isnan(diff_angle) else True),
                    "exotic-droplet_exists":nan_to_minus1(flag_exotic_droplet),
                    "THRESH_VALUES_VER":THRESH_VALUES_VER,
                    "RESERVED0":"layered_main_4_ave : leg_eval_ratio, layered_main_4_stdiv : max_exotic_area, layered_sat_4_ave : flag_image_modified_deeply, layered_sat_4_stdiv : max_main_angle_disturbance, layered_main_3_ave : max_satellite_angle_disturbance, layered_main_3_stdiv : modified_delay_faced, layered_sat_3_ave : modified_delay_separated, layered_sat_3_stdiv : modified_freq_Y, layered_main_2_ave : modified_freq_X",
                    "RESERVED1":"aaa",
                    "RESERVED2":"aaa",
                    "RESERVED3":"aaa",
                    "RESERVED4":"aaa",
                }
                #result = add_message(result)
                
                if flag_is_debugmode:
                    calculation_log('json elem was exported.')
                #5分割各液滴速度 - 標準偏差結果追記
                for dic_elem in vel_add_dics:
                    result.update(dic_elem)
                result.update({
                    "layered_main_4_ave[pix/us]":nan_to_minus1(inf_to_value(leg_eval_ratio)),
                    "layered_main_4_stdiv[pix/us]":nan_to_minus1(max_exotic_area),
                    "layered_sat_4_ave[pix/us]":1 if flag_image_modified_deeply else 0,
                    "layered_sat_4_stdiv[pix/us]":nan_to_minus1(max_main_angle_disturbance),
                    "layered_main_3_ave[pix/us]":nan_to_minus1(max_satellite_angle_disturbance),
                    "layered_main_3_stdiv[pix/us]":nan_to_minus1(contour_rsts.modified_delay_faced),
                    "layered_sat_3_ave[pix/us]":nan_to_minus1(contour_rsts.modified_delay_separated),
                    "layered_sat_3_stdiv[pix/us]":nan_to_minus1(contour_rsts.modified_freq_Y),
                    "layered_main_2_ave[pix/us]":nan_to_minus1(contour_rsts.modified_freq_X),
                })
                if flag_is_debugmode:
                    calculation_log(result)
            #計算失敗時処理
            except:
                if flag_is_debugmode:
                    calculation_log('get_feature_params was failure.')
                result = {
                    "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
                    "filename":directory_path,
                    'condition' : 'get_feature_params was failure.'
                }
    return result

def nan_to_minus1(check_object):
    ret_value = None
    if type(check_object) is None:
        ret_value = "None"
    elif (type(check_object) is float) or (type(check_object) is int):
        ret_value = -1 if math.isnan(check_object) else check_object
    elif (type(check_object) is np.bool_):
        ret_value = (bool)(check_object)
    else:
        ret_value = check_object
    return ret_value

def inf_to_value(check_float):
    ret_value = None
    if check_float == -float('inf'):
        ret_value = -1000
    elif check_float == float('inf'):
        ret_value = 1000
    else:
        ret_value = check_float
    return ret_value

def add_message(result):
    sentences_reserved1 = []
    sentences_reserved2 = []
    sentences_reserved3 = []
    sentences_reserved4 = []
    if result["anormaly_ejections_at_first_image"]:
        sentences_reserved1.append("suspicious of doublet_droplet or mistize satellite")
    if result["main_velocity_is_too_fast"]:
        sentences_reserved2.append("main velocity too fast")
    elif result["main_velocity_is_too_slow"]:
        sentences_reserved2.append("main velocity too slow")
    if result["nozzle_needs_to_be_clean"]:
        sentences_reserved3.append("suspicious of abnormal deposits on the nozzle")
    if result["suspicious_visco-elasticity"]:
        sentences_reserved4.append("suspicious of too large viscosity or visco-elasticity. please confirm liquid composition")
    if result["angle-diff_is_too_large"]:
        sentences_reserved1.append("difference between main and satellite droplet angle too large")
    if result["exotic-droplet_exists"]:
        sentences_reserved1.append("suspicisous of scattered-ejaction")
    
    result.update({
        "RESERVED1":', '.join(sentences_reserved1),
        "RESERVED2":', '.join(sentences_reserved2),
        "RESERVED3":', '.join(sentences_reserved3),
        "RESERVED4":', '.join(sentences_reserved4),
    })
    
    return result
        
        
    