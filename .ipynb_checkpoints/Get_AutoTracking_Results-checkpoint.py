import AutoTracking
import FindContourAnalysis
from CalculationLog import calculation_log
import datetime
import math

INPUT_PARAMS_VER = '0.1.0' #入力パラメータバージョン、2020.10.21

#輪郭抽出前処理に関する入力パラメータ
auto_binarize = True #大津の二値化による自動閾値判定
binarize_thresh = 128 #二値化閾値（auto_binarize = Falseの時）
#輪郭抽出に関するパラメータ
min_area_thresh = 10 #輪郭面積最小値（最小面積以下の輪郭はノイズと判定）
#輪郭解析に関する入力パラメータ
areaThresh_faced = 500 #吐出開始検出時凸包面積差分閾値
areaThresh_separated = 2000 #サテライト液尾分離検出時凸包面積差分閾値
arclengthThresh = 25 #サテライト液尾分離検出時輪郭長差分閾値
solidity_ratio_thresh = 1.5 #サテライト液尾分離検出solidity比閾値
noise_remove_topological_dist_thresh = 20 #輪郭ノイズ除去時位相空間上ノイズ距離
noise_remove_area_thresh = 40 #輪郭ノイズ除去時面積上限値


THRESH_VALUES_VER = '0.1.3' #閾値パラメータバージョン、2020.10.21

#吐出状態判定時閾値
velocity_upperthresh = 8.5 #吐出速度上限[m/s]
velocity_lowerthresh = 4.5 #吐出速度下限[m/s]
Solidity_upperthresh = 1.016 #ノズル輪郭Solidity値上限、上限以上のSolidityで異物判定
velocity_septhresh = 6.5 #粘弾性判定、速度閾値。閾値以上で候補吐出に入れる。
sep_thresh = 300.0 #粘弾性判定、液滴分離閾値。閾値以上で候補吐出に入れる。velocity > velocity_septhresh かつ sep_delay > sep_threshで粘弾性の疑い。 
diff_angle_thresh = 1.753 #メイン - サテライト液滴吐出角度差閾値（90%の吐出が下記角度差範囲に入る値を採用）
pix_mirgin = 20 #逸脱吐出検出判定

#解析拡張パラメータ
num_div_velocity_layer = 5 #液滴速度測定区分数


#デバッグモード指定文字列、exec_mdoe == DEBUG_MODEでデバッグモード処理
DEBUG_MODE = 'DEBUG'

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
        contour_rsts = FindContourAnalysis.analyse_Images_List(
            directoryPath = directory_path,
            min_area_thresh = min_area_thresh,
            binarize_thresh = binarize_thresh,
            auto_binarize = auto_binarize,
            area_mirgin_detect_faced = areaThresh_faced,
            area_mirgin_detect_separation = areaThresh_separated,
            arc_length_mirgin_detect_separation = arclengthThresh,
            solidity_mirgin_detect_separation = solidity_ratio_thresh,
            noise_remove_topological_dist_thresh = noise_remove_topological_dist_thresh,
            noise_remove_area_thresh = noise_remove_area_thresh,
            mkdir = flag_is_debugmode,
            draw_contour = flag_is_debugmode,
            draw_convexhull = flag_is_debugmode,
            draw_coords = flag_is_debugmode,
            exportImage = flag_is_debugmode,
            draw_reg_Detected = flag_is_debugmode,
            DEBUG = flag_is_debugmode)
        if flag_is_debugmode:
            calculation_log('noise remove was done.')
        #成功であれば、flagをTrueに。
        flag_contour_select_was_done = True
        if flag_is_debugmode:
            calculation_log('contour selection was done')
    
    #輪郭抽出失敗時処理
    except:
        if flag_is_debugmode:
            calculation_log('contour_selection was failure.')
        result = {
            "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
            "dirPath":directory_path,
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
                "dirPath":directory_path,
                'condition' : 'auto_tracking was failure.'
            }
        
        #疑似追尾成功→特徴量計算
        if flag_tracking_was_done:
            try:                              
                #出力用の値の整理
                #ファイル名取得
                directory_path = directory_path.split('/')[-1]
                if flag_is_debugmode:
                    calculation_log('dir_path is {}'.format(directory_path))
                #1枚目輪郭数取得               
                num_first_contours = contour_rsts.num_contours_at_first
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
                diff_angle = abs(main_angle - satellite_angle)
                if flag_is_debugmode:
                    calculation_log('diff_angle is {}'.format(diff_angle))
                #逸脱液滴検出
                flag_exotic_droplet = str(contour_rsts.Check_exotic_droplet_exists(trackingResults, pix_mirgin))
                if flag_is_debugmode:
                    calculation_log('flag exotic droplet is {}'.format(flag_exotic_droplet))
                #5分割領域ごとの各液滴速度、標準偏差取得
                y_max = contour_rsts.analysisResults[0][1][0].imgYMax
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
                        "layered_main_{}_ave[pix/us]".format(i):main_vel_res[0],
                        "layered_main_{}_stdiv[pix/us]".format(i):main_vel_res[1],
                        "layered_sat_{}_ave[pix/us]".format(i):sat_vel_res[0],
                        "layered_sat_{}_ave[pix/us]".format(i):sat_vel_res[1],                        
                    })
                    if flag_is_debugmode:
                        calculation_log('dic_elem_{} was generated as {}'.format(i, vel_add_dics[i]))
                
                #dictionaryへの出力
                result = {
                    "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
                    "file_name":directory_path,
                    "camera_resolution[um/pix]":camera_resolution,
                    "API_VER":API_VER,
                    "num_contours_at_first":num_first_contours,
                    "solidity[U]":solidity,
                    "arc_solidity[u]":arc_solidity,
                    "flag_droplet_faced":str(flag_droplet_faced),
                    "faced_delay[us]":faced_delay,
                    "flag_droplet_separated":str(flag_droplet_separated),
                    "separated_delay[us]":separated_delay,
                    "max_regament_delay[us]":max_regament_length_delay,
                    "max_regament_length[pix]":max_regament_length,
                    "most_freq_Y[pix]":contour_rsts.freq_Y,
                    "CONTOUR_CODE_VER":FindContourAnalysis.get_code_ver(),
                    "main_average_velocity[pix/us]":main_average_velocity,
                    "main_average_velocity[m/s]":main_average_velocity_stdized,
                    "main_velocity_stddiv[pix/us]":main_velocity_stdiv,
                    "main_angle[degrees]":main_angle,
                    "satellite_average_velocity[pix/us]":satellite_average_velocity,
                    "satellite_average_velocity[m/s]":satellite_average_velocity_stdized,
                    "satellite_velocity_stddiv[pix/us]":satellite_velocity_stdiv,
                    "satellite_angle[degrees]":satellite_angle,
                    "main-satellite_angle_diff[degrees]":diff_angle,
                    "main_linearity_error[pix]":trackingResults.Get_MainXY_Fit_Error_Min_Max_Range()[1] - trackingResults.Get_MainXY_Fit_Error_Min_Max_Range()[0],
                    "satellite_linearity_error[pix]":trackingResults.Get_SatelliteXY_Fit_Error_Min_Max_Range()[1] - trackingResults.Get_SatelliteXY_Fit_Error_Min_Max_Range()[0],
                    "AUTO_TRACKING_CODE_VER":AutoTracking.get_code_ver(),
                    "anormaly_ejections_at_first_image":str(num_first_contours > 1),
                    "main_velocity_is_too_fast":str(main_average_velocity_stdized > velocity_upperthresh),
                    "main_velocity_is_too_slow":str(main_average_velocity_stdized < velocity_lowerthresh),
                    "nozzle_needs_to_be_clean":str(solidity > Solidity_upperthresh),
                    "suspicious_visco-elasticity":str(separated_delay > sep_thresh and main_average_velocity_stdized > velocity_septhresh),
                    "angle-diff_is_too_large":str(diff_angle > diff_angle_thresh),
                    "exotic-droplet_exists":str(flag_exotic_droplet),
                    "THRESH_VALUES_VER":THRESH_VALUES_VER,
                    "RESERVED0":"aaa",
                    "RESERVED1":"aaa",
                    "RESERVED2":"aaa",
                    "RESERVED3":"aaa",
                    "RESERVED4":"aaa",
                }
                if flag_is_debugmode:
                    calculation_log('json elem was exported.')
                #5分割各液滴速度 - 標準偏差結果追記
                for dic_elem in vel_add_dics:
                    result.update(dic_elem)
                if flag_is_debugmode:
                    calculation_log(result)
            #計算失敗時処理
            except:
                if flag_is_debugmode:
                    calculation_log('get_feature_params was failure.')
                result = {
                    "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
                    "dirPath":directory_path,
                    'condition' : 'get_feature_params was failure.'
                }
    return result