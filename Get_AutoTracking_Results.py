import AutoTracking
import FindContourAnalysis

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
    if exec_mode == DEBUG_MODE:
        print(directory_path)
        print(exec_mode)
    areaThresh = 2000
    arclengthThresh = 25
    flag_contour_select_was_done = False
    if exec_mode == DEBUG_MODE:
        print('contour selection function is calling')

    try:
        contour_rsts = FindContourAnalysis.analyse_Images_List(
            directoryPath = directory_path,
            min_area_thresh = 10,
            binarize_thresh=128,
            auto_binarize = True,
            mkdir=False,
            draw_contour = False,
            draw_convexhull = False,
            draw_coords = True,
            exportImage = False,
            draw_reg_Detected = False,
            area_mirgin_detectSeparation = areaThresh,
            arc_length_mirgin_detectSeparation = arclengthThresh)
        flag_contour_select_was_done = True
        if exec_mode == DEBUG_MODE:
            print('contour selection was done')

    except:
        if exec_mode == DEBUG_MODE:
            print('contour_selection was failure.')
        result = {
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
                draw_Tracking_Results = False,
                draw_Fitting_Line = False)  
            flag_tracking_was_done = True
            if exec_mode == DEBUG_MODE:
                print('auto_tracking was done')
        except:
            if exec_mode == DEBUG_MODE:
                print('auto_tracking was failure.')
            result = {
                'condition' : 'auto_tracking was failure.'
            }
        if flag_tracking_was_done:
            try:    
                result = {
                    'dirPath':directory_path,
                    'solidity[U]':contour_rsts.get_cva_a_ratio(),
                    'arc_solidity[u]':contour_rsts.get_cval_al_ratio(),
                    'separated_delay[us]':contour_rsts.get_separated_delay(areaThresh, arclengthThresh, contour_rsts.get_dropletFaced_delay(areaThresh)[1])[1],
                    'faced_delay[us]':contour_rsts.get_dropletFaced_delay(areaThresh)[1],
                    'regament_max_delay[us]':contour_rsts.get_maximum_regament_length(10)[0],
                    'max_regament_length[pix]':contour_rsts.get_maximum_regament_length(10)[1],
                    'main_average_velocity[pix/us]':trackingResults.Get_Main_Velocity()[0],
                    'main_velocity_stddiv[pix/us]':trackingResults.Get_Main_Velocity()[1],
                    'main_angle[degrees]':trackingResults.Get_Main_Angle_degrees(),
                    'satellite_average_velocity[pix/us]':trackingResults.Get_Satellite_Velocity()[0],
                    'satellite_velocity_stddiv[pix/us]':trackingResults.Get_Satellite_Velocity()[1],
                    'satellite_angle[degrees]':trackingResults.Get_Satellite_Angle_degrees(),
                    'main_linearity_error[pix]':trackingResults.Get_MainXY_Fit_Error_Min_Max_Range()[1] - trackingResults.Get_MainXY_Fit_Error_Min_Max_Range()[0],
                    'satellite_linearity_error[pix]':trackingResults.Get_SatelliteXY_Fit_Error_Min_Max_Range()[1] - trackingResults.Get_SatelliteXY_Fit_Error_Min_Max_Range()[0],
                    'most_freq_Y[pix]':contour_rsts.get_freq_YandNum()[1],
                }
                if exec_mode == DEBUG_MODE:
                    print('get_feature_params was done')   
                    print('dirP:{}'.format(directory_path))
                    print('cva:{}'.format(contour_rsts.get_cva_a_ratio())) 
                    print('cval:{}'.format(contour_rsts.get_cval_al_ratio()))
                    print('sepdelay:{}'.format(contour_rsts.get_separated_delay(areaThresh, arclengthThresh, contour_rsts.get_dropletFaced_delay(areaThresh)[1])[1]))
                    print('facdelay:{}'.format(contour_rsts.get_dropletFaced_delay(areaThresh)[1]))
                    print('regMaxD:{}'.format(contour_rsts.get_maximum_regament_length(10)[0]))
                    print('regMaxL:{}'.format(contour_rsts.get_maximum_regament_length(10)[1]))
                    print('aveVelMain:{}'.format(trackingResults.Get_Main_Velocity()[0]))
                    print('divVelMain:{}'.format(trackingResults.Get_Main_Velocity()[1]))
                    print('angleMain:{}'.format(trackingResults.Get_Main_Angle_degrees()))
                    print('aveVelSat:{}'.format(trackingResults.Get_Satellite_Velocity()[0]))
                    print('divVelSat:{}'.format(trackingResults.Get_Satellite_Velocity()[1]))
                    print('angleSat:{}'.format(trackingResults.Get_Satellite_Angle_degrees()))
                    print('mainEr:{}'.format(trackingResults.Get_MainXY_Fit_Error_Min_Max_Range()[1] - trackingResults.Get_MainXY_Fit_Error_Min_Max_Range()[0]))
                    print('satEr:{}'.format(trackingResults.Get_SatelliteXY_Fit_Error_Min_Max_Range()[1] - trackingResults.Get_SatelliteXY_Fit_Error_Min_Max_Range()[0]))
                    print('freqY:{}'.format(contour_rsts.get_freq_YandNum()[1]))
            except:
                if exec_mode == DEBUG_MODE:
                    print('get_feature_params was failure.')
                result = {
                    'condition' : 'get_feature_params was failure.'
                }
    return result