import Analysis_Contours_List_Class
import Tracking_Result_Elem_Class
import Tracking_Results_Class
#pythonほぼ標準ライブラリインポート
import glob
import os
import sys
import shutil
import math
#numpyインポート
import numpy as np
#OpenCVインポート
import cv2
from CalculationLog import calculation_log

#コードバージョン
AUTO_TRACKING_VER = '0.0.8'

def get_code_ver():
    '''
    コードバージョン取得関数
    
    argments:なし
    
    return
    =============
    AUTO_TRACKING_VER : str
        自動追尾コードバージョン
    
    '''
    return AUTO_TRACKING_VER

#輪郭群抽出結果→液滴追尾結果クラス生成関数
def auto_Tracking(dirPath,#フォルダパス, str
                  rsts,#解析する輪郭群、analysis_result_list class
                  draw_Tracking_Results,#追尾結果の出力
                  draw_Fitting_Line,#フィッティング結果の描画,
                  DEBUG#デバッグモード指定
                 ):
    """
    輪郭群抽出結果から液滴追尾結果を生成する関数
    
    Parameters
    ----------
    dirPath : str
        入力画像を格納するディレクトリパス。
    rsts : FindContourAnalysis.Analysis_Results_Listクラス
        解析対象の輪郭抽出結果群。
    draw_Tracking_Results : bool
        追尾結果の出力の有無、初期値False
    draw_Fitting_Line : bool
        フィッティング結果の描画、初期値False

    Returns
    -------
    tracking_Results : Tracking_Resultsクラス
        追尾結果。
    
    """
    
    if DEBUG:
        calculation_log('Auto_Tracking module was called.')
    #結果格納クラス宣言
    tracking_Results = Tracking_Results_Class.Tracking_Results()
    #輪郭格納データ配列のインデックス宣言
    #analysisResultsリストの2つめにて指定。
    index_delay = 0 #ディレイのインデックス
    index_Cnt = 1 #輪郭リストのインデックス
    
    #メイン液滴の追尾
    if rsts.flag_faced_is_detected == True:
        #追尾対象の抽出
        rstsMain = [rst for rst in rsts.analysisResults if rst.delay >= rsts.delay_faced]
        #ディレイ順に昇順ソート
        rstsMain.sort(key = lambda rst:rst.delay)
        #検出開始時のメイン液滴座標のディレイと座標格納、面積最大の輪郭にて       
        tracking_Results.Set_MainXY(rstsMain[0].delay, rstsMain[0].contours[0].main_X, rstsMain[0].contours[0].main_Y)
        #追尾対象のディレイ写真が2枚以上の場合
        if len(rstsMain)>1:
            #追尾検出2枚目の検出
            if len(rstsMain[1].contours) > 1:
                #対象輪郭が2つ以上の場合、初回の結果との距離順にソート。ソート後、最近傍のメイン液滴を格納。
                rstsMain[1].contours.sort(key = lambda rst : (rst.main_X - tracking_Results.results[0].main_X) ** 2 + (rst.main_Y - tracking_Results.results[0].main_Y)**2)
            #追尾検出2枚目のディレイと座標格納
            tracking_Results.Set_MainXY(rstsMain[1].delay, rstsMain[1].contours[0].main_X, rstsMain[1].contours[0].main_Y)
            #追尾検出3枚目以降
            for i in range(2, len(rstsMain)):
                #ソート基準座標の計算
                #ディレイ比計算
                delayRatio = (rstsMain[i].delay - rstsMain[i-2].delay) / (rstsMain[i-1].delay - rstsMain[i-2].delay)
                #予想基準座標算出
                ptEval_X = tracking_Results.results[-2].main_X + delayRatio * (tracking_Results.results[-1].main_X - tracking_Results.results[-2].main_X)
                ptEval_Y = tracking_Results.results[-2].main_Y + delayRatio * (tracking_Results.results[-1].main_Y - tracking_Results.results[-2].main_Y)
                #予想Y座標が画像Y座標最大値より大きい場合は追尾打ち切り
                if ptEval_Y >= rstsMain[i].contours[0].imgYMax:
                    break
                #評価輪郭数0の場合は打ち切り
                if len(rstsMain[i].contours) == 0:
                    break
                #評価点が2点以上の場合の処理
                if len(rstsMain[i].contours) > 1:
                    #評価基準点と各輪郭のメイン液滴座標距離順に輪郭群をソート。ソート後、最近傍のメイン液滴を格納。
                    rstsMain[i].contours.sort(key = lambda rst : (rst.main_X - ptEval_X) ** 2 + (rst.main_Y - ptEval_Y)**2)
                #最近傍座標が画像際下端より下に来た場合は打ち切り
                if rstsMain[i].contours[0].main_Y > rstsMain[i].contours[0].imgYMax:
                    break
                #最近傍座標が一つ前の結果より上に来た場合は打ち切り
                if rstsMain[i].contours[0].main_Y < tracking_Results.results[-1].main_Y:
                    break
                #検出結果の格納
                tracking_Results.Set_MainXY(rstsMain[i].delay, rstsMain[i].contours[0].main_X, rstsMain[i].contours[0].main_Y)

    if DEBUG:
        calculation_log('main_tracking was completed.')
    #サテライト液滴の追尾
    flag_sat_is_trackable = True
    if rsts.flag_separated_is_detected == True:
        #追尾対象の抽出
        rstsSatellite = [rst for rst in rsts.analysisResults if rst.delay >= rsts.delay_separated]
        #ディレイ順に昇順ソート
        rstsSatellite.sort(key = lambda rst:rst.delay)
        #1枚目の輪郭数カウント、2以上でソート
        if len(rstsSatellite[0].contours) > 1:
            #面積順で輪郭リストをソート、降順
            rstsSatellite[0].contours.sort(key=lambda cnt: cnt.area, reverse = True)
            #対象輪郭の抽出、面積最大→ノズルの検出
            rstBase = rstsSatellite[0].contours[0]
            #satelliteのY座標がノズルのY座標より下に来るもののみ抽出
            rstAdd = [rst for rst in rstsSatellite[0].contours if rst.satellite_Y >= rstBase.main_Y]
            if len(rstAdd) == 0:
                flag_sat_is_trackable = False                
            if len(rstAdd) == 1:
                rstAdd
            else:
                #一つ前の結果からの距離順にて昇順ソート。
                rstAdd.sort(key = lambda rst : (rst.satellite_Y - rstBase.main_Y)**2)

        if flag_sat_is_trackable:
            #1枚目輪郭の結果格納
            tracking_Results.Set_SatelliteXY(rstsSatellite[0].delay, rstAdd[0].satellite_X, rstAdd[0].satellite_Y)
            #追尾対象のディレイ写真が2枚以上の場合
            if len(rstsSatellite) >1:
                #追尾検出2枚目の検出
                #2枚目に格納されている輪郭情報が2以上の場合
                if len(rstsSatellite[1].contours) > 1:
                    #サテライト液滴X座標がnanではないものを抽出。
                    lstSat = list(filter(lambda rst: not math.isnan(rst.satellite_X), tracking_Results.results))
                    #satelliteのY座標が一つ前のY座標より下に来るもののみ抽出
                    rstAdd = [rst for rst in rstsSatellite[1].contours if rst.satellite_Y >= lstSat[-1].satellite_Y]
                    print(len(rstAdd))
                    if len(rstAdd) > 0:
                        #一つ前の結果からの距離順にて昇順ソート。
                        rstAdd.sort(key = lambda rst : (rst.satellite_X - lstSat[-1].satellite_X) ** 2 + (rst.satellite_Y - lstSat[-1].satellite_Y)**2)
                    else:
                        rstAdd = sorted(lstSat, key=lambda rst : (rst.satellite_X - lstSat[-1].satellite_X) ** 2 + (rst.satellite_Y - lstSat[-1].satellite_Y)**2)
                else:
                    #対象の輪郭が1つの場合、そのまま結果の格納用オブジェクトをコピー
                    rstAdd = rstsSatellite[1].contours                
                #サテライト液滴追尾結果の格納
                tracking_Results.Set_SatelliteXY(rstsSatellite[1].delay, rstAdd[0].satellite_X, rstAdd[0].satellite_Y)
                print('2nd added')

                #追尾検出3枚目以降            
                for i in range(2, len(rstsSatellite)):
                    #i枚目の輪郭格納結果数が0であれば打ち切り
                    if len(rstsSatellite[i].contours) == 0:
                        break

                    #すでに格納されている結果から、satellite_X座標がnanではないものを抽出。
                    lstSat = list(filter(lambda rst: not math.isnan(rst.satellite_X), tracking_Results.results))     
                    #ひとつ前の結果のサテライトY座標より下にサテライトY座標がくるもののみを抽出
                    rstAdd = [rst for rst in rstsSatellite[i].contours if rst.satellite_Y >= lstSat[-1].satellite_Y]
                    #抽出結果数が0であれば打ち切り
                    if len(rstAdd) == 0:
                        break
                    #抽出結果を、ひとつ前のサテライト座標からの距離順に昇順ソート→最も近いものをサテライト液滴として採用。
                    rstAdd.sort(key = lambda rst : (rst.satellite_X - lstSat[-1].satellite_X) ** 2 + (rst.satellite_Y - lstSat[-1].satellite_Y)**2)
                    #サテライト検出結果を格納
                    tracking_Results.Set_SatelliteXY(rstsSatellite[i].delay, rstAdd[0].satellite_X, rstAdd[0].satellite_Y)

    if DEBUG:
        calculation_log('satellite_tracking was completed.')
    
    #格納結果をディレイ時間に対して昇順でソート
    tracking_Results.results.sort(key = lambda rst: rst.delay)

    if DEBUG:
        calculation_log('results objects were sorted with rst.delay.')

    #追尾結果の描画指定の場合
    if draw_Tracking_Results:
        #追尾結果描画関数の呼び出し
        drawTrackingResult(dirPath=dirPath, trackingRsts=tracking_Results, draw_Fitting_Line = draw_Fitting_Line, DEBUG = DEBUG)        
    #指定したディレクトリパスをprint（!!!後ほどコメントアウト!!!）
    print(dirPath)
    #追尾結果を返す
    return tracking_Results


def drawTrackingResult(dirPath,
                       trackingRsts,
                       draw_Fitting_Line,
                       DEBUG):
    '''
    追尾結果描画関数。privateメソッド。
    指定ディレクトリ内に「tracikngRsts」ディレクトリを生成し、その中に
    対応する追尾結果を描画する。
    画像は.jpgのみ。
    
    Parameters
    ----------
    dirPath : str
        描画対象画像格納フォルダ
    trackingRsts : Tracking_Resultsクラス
        描画対象結果格納追尾結果クラス
    draw_Fitting_Line : bool
        フィッティング結果描画の有無を指定
    DEBUG : bool
        デバッグモード指定
            
    Return
    ----------
        なし
    
    '''
    extension = '.jpg'
    pathes = glob.glob(dirPath + "/*"+extension)
    if os.path.exists(dirPath + "/trackingRsts"):
        delPathes = glob.glob(dirPath + "/trackingRsts/*.jpg")
        for f in delPathes:
            os.remove(f)       
    os.makedirs(dirPath + "/trackingRsts", exist_ok = True)
    if DEBUG:
        calculation_log('mkdir at {}/trackingRsts'.format(dirPath))
    
    signature_size = 5
          
    for i in range(len(pathes)):
        f = pathes[i]
        #画像データの読み込み、opencv→numpyデータアレイ化
        im = cv2.imread(f)
        
        #ファイル名からディレイ時間を読み取り
        delay = 0.0
        max_delay_description_field_length = 10
        j = max_delay_description_field_length
        flag_delay_is_get = False
        while j > len(extension):
            try:
                delay = float(f[-j:-len(extension)])
                flag_delay_is_get = True
                break
            except:
                j = j - 1
        
        if not flag_delay_is_get:
            delay = -1.0
       
        if (float)(delay) in [(float)(de.delay) for de in trackingRsts.results if not math.isnan(de.main_X)]:
            x = [rst for rst in trackingRsts.results if (float)(rst.delay) == (float)(delay)][0].main_X
            y = [rst for rst in trackingRsts.results if (float)(rst.delay) == (float)(delay)][0].main_Y
            im = cv2.rectangle(im,((int)(x-signature_size),(int)(y-signature_size)),((int)(x+signature_size),(int)(y+signature_size)),\
                               (0,0,255),3)
            
        if (float)(delay) in [(float)(de.delay) for de in trackingRsts.results if not math.isnan(de.satellite_X)]:
            x = [rst for rst in trackingRsts.results if  (float)(rst.delay) == (float)(delay)][0].satellite_X
            y = [rst for rst in trackingRsts.results if  (float)(rst.delay) == (float)(delay)][0].satellite_Y
            im = cv2.rectangle(im,((int)(x-signature_size),(int)(y-signature_size)),((int)(x+signature_size),(int)(y+signature_size)),\
                               (255,0,0),3)
        if draw_Fitting_Line== True:
            lineMainResults, lineSatelliteResults = trackingRsts.get_Main_vector_slope_intercept(), trackingRsts.get_Satellite_vector_slope_intercept()
            if not any([math.isnan(value) for value in lineMainResults]):
                im = cv2.line(im,
                              ((int)(lineMainResults[5]), 0), 
                              ((int)(lineMainResults[4]*im.shape[0] + lineMainResults[5]), im.shape[0]),
                              (64, 64, 128), 1)
                predMainX = (int)(lineMainResults[0] * delay + lineMainResults[1])
                predMainY = (int)(lineMainResults[2] * delay + lineMainResults[3])
                im = cv2.circle(im, (predMainX, predMainY), signature_size, (64,64,128), 1)
            if not any([math.isnan(value) for value in lineSatelliteResults]):
                im = cv2.line(im,
                              ((int)(lineSatelliteResults[5]), 0),
                              ((int)(lineSatelliteResults[4]*im.shape[0] + lineSatelliteResults[5]), im.shape[0]), 
                              (128, 64, 64), 1)
                predSatX = (int)(lineSatelliteResults[0] * delay + lineSatelliteResults[1])
                predSatY = (int)(lineSatelliteResults[2] * delay + lineSatelliteResults[3])
                im = cv2.circle(im, (predSatX, predSatY), signature_size, (128,64,64), 2)
        savePath = dirPath + "/trackingRsts/" + os.path.splitext(os.path.basename(f))[0] + "_drawTRResults.jpg"
        cv2.imwrite(savePath, im)
        
        if DEBUG:
            calculation_log('tracking result file is exported at {}'.format(savePath))

    return None

    

