import AutoTracking
import FindContourAnalysis
from CalculationLog import calculation_log
import datetime
import math

CODE_VER = '0.1.2'

def get_autoTracking_Results(directory_path, exec_mode):
    '''
    追尾→特徴量抽出関数   
    ・パラメータ：dirpath : str
                    ディレクトリパス
                  exec_mode : str
                      起動モード、DEBUGでデバッグモード、文字列等出力

　　・返り値：特徴量クラス : str(json)
          'dirPath' : str
              渡されたディレクトリパス
          'solidity[U]' : float
              各画像での最大面積輪郭のconvex_hull_area / area比の最小値、ノズルの凹凸具合を示す。
          'arc_solidity[u]' : float
              各画像での最大面積輪郭のconvex_hull_arclength / arclength比の最大値、ノズルの凹凸具合を示す。              
          'separated_delay[us]': float
              液滴分離検知タイミングのディレイ時間[us]
          'faced_delay[us]' : float
              液滴吐出開始検知タイミングのディレイ時間[us]
          'regament_max_delay[us]' : float
              リガメント長さ最大のディレイ時間[us]
          'max_regament_length[pix]' : float
              最大リガメント長さ[pix]
          'main_average_velocity[pix/us]' : float
              平均メイン液滴速度[pix/us]
          'main_velocity_stddiv[pix/us]' : float
              メイン液滴速度の標準偏差
          'main_angle[degrees]' : float
              メイン液滴吐出角度[degrees]
          'satellite_average_velocity[pix/us]' : float
              平均サテライト液滴速度[pix/us]
          'satellite_velocity_varience[pix/us]' : float
              サテライト液滴速度の標準偏差
          'satellite_angle[degrees]' : float
              サテライト液滴吐出角度[degrees]
          'main_linearity_error[pix]' : float
              メイン液滴吐出軌跡の直線フィット結果からの最大ズレ[pix]
          'satellite_linearity_error[pix]' : float
              サテライト液滴吐出軌跡の直線フィット結果からの最大ズレ[pix]
          'most_freq_Y[pix]' : int
              吐出開始前ノズル輪郭の最大頻出Y座標
    '''
    DEBUG_MODE = 'DEBUG'
    flag_is_debugmode = exec_mode == DEBUG_MODE
    if flag_is_debugmode:
        calculation_log('analyse dir path = {}'.format(directory_path))
        calculation_log('exec_mode = {}'.format(exec_mode))
    areaThresh = 2000
    arclengthThresh = 25
    flag_contour_select_was_done = False
    if flag_is_debugmode:
        calculation_log('contour selection function is calling')
        
    try:
        contour_rsts = FindContourAnalysis.analyse_Images_List(
            directoryPath = directory_path,
            min_area_thresh = 10,
            binarize_thresh=128,
            auto_binarize = True,
            mkdir=flag_is_debugmode,
            draw_contour = flag_is_debugmode,
            draw_convexhull = flag_is_debugmode,
            draw_coords = flag_is_debugmode,
            exportImage = flag_is_debugmode,
            draw_reg_Detected = flag_is_debugmode,
            area_mirgin_detectSeparation = areaThresh,
            arc_length_mirgin_detectSeparation = arclengthThresh,
            DEBUG = flag_is_debugmode)
        flag_contour_select_was_done = True
        if exec_mode == DEBUG_MODE:
            calculation_log('contour selection was done')

    except:
        if exec_mode == DEBUG_MODE:
            calculation_log('contour_selection was failure.')
        result = {
            "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
            "dirPath":directory_path,
            'condition' : 'contour selection was failure.' 
        }
    
    if flag_contour_select_was_done:
        flag_tracking_was_done = False
        try:
            trackingResults = AutoTracking.auto_Tracking(
                dirPath = directory_path,
                rsts = contour_rsts,
                area_mirgin_detectSeparation = areaThresh,
                arc_length_mirgin_detectSeparation = arclengthThresh,
                auto_binarize = True,
                draw_Tracking_Results = flag_is_debugmode,
                draw_Fitting_Line = flag_is_debugmode,
                DEBUG = flag_is_debugmode)  
            flag_tracking_was_done = True
            if exec_mode == DEBUG_MODE:
                calculation_log('auto_tracking was done')
        except:
            if exec_mode == DEBUG_MODE:
                calculation_log('auto_tracking was failed')
            result = {
                "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
                "dirPath":directory_path,
                'condition' : 'auto_tracking was failure.'
            }
        if flag_tracking_was_done:
            try:               
                THRESH_VALUES_VER = '0.1.1'
                pix_per_um = 3.20
                velocity_upperthresh = 8.5
                velocity_lowerthresh = 4.5
                Solidity_upperthresh = 1.016
                velocity_septhresh = 6.5
                sep_thresh = 300.0
                #90%の吐出が下記角度差範囲に入る
                diff_angle_thresh = 1.403
                
                directory_path = directory_path.split('/')[-1]
                num_first_contours = contour_rsts.get_NumContours_at_First()
                solidity = contour_rsts.get_cva_a_ratio()
                arc_solidity = contour_rsts.get_cval_al_ratio()
                separated_delay = contour_rsts.get_separated_delay(areaThresh, arclengthThresh, contour_rsts.get_dropletFaced_delay(areaThresh)[1])[1]
                faced_delay = contour_rsts.get_dropletFaced_delay(areaThresh)[1]
                max_regament_length_delay = contour_rsts.get_maximum_regament_length(10)[0]
                max_regament_length = contour_rsts.get_maximum_regament_length(10)[1]
                main_average_velocity = trackingResults.Get_Main_Velocity()[0]
                main_velocity_stdiv = trackingResults.Get_Main_Velocity()[1]
                main_angle = trackingResults.Get_Main_Angle_degrees()
                satellite_average_velocity = trackingResults.Get_Satellite_Velocity()[0]
                satellite_velocity_stdiv = trackingResults.Get_Satellite_Velocity()[1]
                satellite_angle = trackingResults.Get_Satellite_Angle_degrees()
                main_average_velocity_stdized = main_average_velocity * pix_per_um
                satellite_average_velocity_stdized = satellite_average_velocity * pix_per_um
                diff_angle = abs(main_angle - satellite_angle)
                
                result = {
                    "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
                    "dirPath":directory_path,
                    "num_contours_at_first":num_first_contours,
                    "solidity[U]":solidity,
                    "arc_solidity[u]":arc_solidity,
                    "separated_delay[us]":separated_delay,
                    "faced_delay[us]":faced_delay,
                    "regament_max_delay[us]":max_regament_length_delay,
                    "max_regament_length[pix]":max_regament_length,
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
                    "most_freq_Y[pix]":contour_rsts.get_freq_YandNum()[1],
                    "CODE_VER":CODE_VER,
                    "abnormal_ejaction":str(num_first_contours > 1),
                    "main_velocity_is_too_fast":str(main_average_velocity_stdized > velocity_upperthresh),
                    "main_velocity_is_too_slow":str(main_average_velocity_stdized < velocity_lowerthresh),
                    "nozzle_is_needed_to_clean":str(solidity > Solidity_upperthresh),
                    "suspicious_visco-elasticity":str(separated_delay > sep_thresh and main_average_velocity_stdized > velocity_septhresh),
                    "angle-diff_is_too_large":str(diff_angle > diff_angle_thresh),
                    "THRESH_VALUES_VER":THRESH_VALUES_VER,
                }
#                result = {
#                    'test':"test"
#                }
                if exec_mode == DEBUG_MODE:
                    calculation_log(result)
            except:
                if exec_mode == DEBUG_MODE:
                    calculation_log('get_feature_params was failure.')
                result = {
                    "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
                    "dirPath":directory_path,
                    'condition' : 'get_feature_params was failure.'
                }
    return result