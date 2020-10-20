#FindContourAnalysis.pyファイルをインポート
import FindContourAnalysis
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


#輪郭群抽出結果→液滴追尾結果クラス生成関数
def auto_Tracking(
    dirPath,#フォルダパス, str
    rsts,#解析する輪郭群、analysis_result_list class
    area_mirgin_detectFaced = 1000,#液滴吐出開始検出閾値[pix]
    area_mirgin_detectSeparation = 2000,#液滴分離検出閾値[pix]
    arc_length_mirgin_detectSeparation = 10,
    auto_binarize = True,#大津の二値化採用
    draw_Tracking_Results = False,#追尾結果の出力
    draw_Fitting_Line = False,#フィッティング結果の描画,
    DEBUG = False
):
    """
    輪郭群抽出結果から液滴追尾結果を生成する関数
    
    Parameters
    ----------
    dirPath : str
        入力画像を格納するディレクトリパス。
    rsts : FindContourAnalysis.Analysis_Results_Listクラス
        解析対象の輪郭抽出結果群。
    area_mirgin_detectFaced : int
        液滴吐出開始検出閾値[pix]、面積にて指定。初期値1000
    area_mirgin_detectSeparation : int
        液滴分離検出閾値[pix]、面積にて指定。初期値2000
    arc_length_mirgin_detectSeparation : int
        液滴分離検出閾値[pix]、輪郭長さにて指定、初期値10
    auto_binarize : bool
        大津の二値化採用、初期値True
    draw_Tracking_Results : bool
        追尾結果の出力の有無、初期値False
    draw_Fitting_Line : bool
        フィッティング結果の描画、初期値False

    Returns
    -------
    tracking_Results : Tracking_Resultsクラス
        追尾結果。
    
    """
    
    #固定位置に現れるノイズ輪郭の除去
    rsts.Remove_Noise(thresh=20)
    #液滴吐出開始の検出
    flagFacedDetected, delayFaced = rsts.get_dropletFaced_delay(area_mirgin_detectSeparation=area_mirgin_detectFaced)
    #液滴分離検出
    flagSeparatedIsDetected, delaySeparated  = rsts.get_separated_delay(
        area_mirgin_detectSeparation=area_mirgin_detectSeparation,
        arc_length_mirgin_detectSeparation = arc_length_mirgin_detectSeparation,
        faced_delay = delayFaced)
    #返り値の宣言
    tracking_Results = Tracking_Results()
    if DEBUG:
        calculation_log('delay_faced is {} us, and delay_separated is {} us'.format(delayFaced, delaySeparated))
    #輪郭格納データ配列のインデックス宣言
    #analysisResultsリストの2つめにて指定。
    index_delay = 0 #ディレイのインデックス
    index_Cnt = 1 #輪郭リストのインデックス
    
    #メイン液滴の追尾
    if flagFacedDetected == True:
        #追尾対象の抽出
        rstsMain = [rst for rst in rsts.analysisResults if rst[0] >= delayFaced]
        #ディレイ順に昇順ソート
        rstsMain.sort(key = lambda rst:rst[index_delay])
        #検出開始タイミングで面積順に降順ソート
        rstsMain[0][index_Cnt].sort(key = lambda cnt:cnt.area, reverse=True)
        #検出開始時のメイン液滴座標のディレイと座標格納、面積最大の輪郭にて       
        tracking_Results.Set_MainXY(rstsMain[0][index_delay], rstsMain[0][index_Cnt][0].main_X, rstsMain[0][index_Cnt][0].main_Y)
        #追尾対象のディレイ写真が2枚以上の場合
        if len(rstsMain)>1:
            #追尾検出2枚目の検出
            if len(rstsMain[1][index_Cnt]) > 1:
                #対象輪郭が2つ以上の場合、初回の結果との距離順にソート。ソート後、最近傍のメイン液滴を格納。
                rstsMain[1][index_Cnt].sort(key = lambda rst : (rst.main_X - tracking_Results.results[0].main_X) ** 2 + (rst.main_Y - tracking_Results.results[0].main_Y)**2)
            #追尾検出2枚目のディレイと座標格納
            tracking_Results.Set_MainXY(rstsMain[1][index_delay], rstsMain[1][index_Cnt][0].main_X, rstsMain[1][index_Cnt][0].main_Y)
            #追尾検出3枚目以降
            for i in range(2, len(rstsMain)):
                #ソート基準座標の計算
                #ディレイ比計算
                delayRatio = (rstsMain[i][index_delay] - rstsMain[i-2][index_delay]) / (rstsMain[i-1][index_delay] - rstsMain[i-2][index_delay])
                #予想基準座標算出
                ptEval_X = tracking_Results.results[-2].main_X + delayRatio * (tracking_Results.results[-1].main_X - tracking_Results.results[-2].main_X)
                ptEval_Y = tracking_Results.results[-2].main_Y + delayRatio * (tracking_Results.results[-1].main_Y - tracking_Results.results[-2].main_Y)
                #予想Y座標が画像Y座標最大値より大きい場合は追尾打ち切り
                if ptEval_Y >= rstsMain[i][index_Cnt][0].imgYMax:
                    break
                #評価点が2点以上の場合の処理
                if len(rstsMain[i][index_Cnt]) > 1:
                    #評価基準点と各輪郭のメイン液滴座標距離順に輪郭群をソート。ソート後、最近傍のメイン液滴を格納。
                    rstsMain[i][index_Cnt].sort(key = lambda rst : (rst.main_X - ptEval_X) ** 2 + (rst.main_Y - ptEval_Y)**2)
                #最近傍座標が画像際下端より下に来た場合は打ち切り
                if rstsMain[i][index_Cnt][0].main_Y > rstsMain[i][index_Cnt][0].imgYMax:
                    break
                #最近傍座標が一つ前の結果より上に来た場合は打ち切り
                if rstsMain[i][index_Cnt][0].main_Y < tracking_Results.results[-1].main_Y:
                    break
                #検出結果の格納
                tracking_Results.Set_MainXY(rstsMain[i][index_delay], rstsMain[i][index_Cnt][0].main_X, rstsMain[i][index_Cnt][0].main_Y)

    #サテライト液滴の追尾
    if flagSeparatedIsDetected == True:
        #追尾対象の抽出
        rstsSatellite = [rst for rst in rsts.analysisResults if rst[index_delay] >= delaySeparated]
        #ディレイ順に昇順ソート
        rstsSatellite.sort(key = lambda rst:rst[index_delay])
        #1枚目の輪郭数カウント、2以上でソート
        if len(rstsSatellite[0][index_Cnt]) > 1:
            #面積順で輪郭リストをソート、降順
            rstsSatellite[0][index_Cnt].sort(key=lambda cnt: cnt.area, reverse = True)
            #対象輪郭の抽出、面積最大→ノズルの検出
            rstBase = rstsSatellite[0][index_Cnt][0]
            #Y座標のみでノズルY座標からの距離順ソート。X座標を含むと最大輪郭のノイズを拾うことがあるためY座標のみで実施。
            rstsSatellite[0][index_Cnt].sort(key = lambda cnt2: (rstBase.main_Y - cnt2.satellite_Y) ** 2)
        #1枚目輪郭の結果格納
        tracking_Results.Set_SatelliteXY(rstsSatellite[0][index_delay], rstsSatellite[0][index_Cnt][0].satellite_X, rstsSatellite[0][index_Cnt][0].satellite_Y)
        #追尾対象のディレイ写真が2枚以上の場合
        if len(rstsSatellite) >1:
            #追尾検出2枚目の検出
            #2枚目に格納されている輪郭情報が2以上の場合
            if len(rstsSatellite[1][index_Cnt]) > 1:
                #サテライト液滴X座標がnanではないものを抽出。
                lstSat = list(filter(lambda rst: not math.isnan(rst.satellite_X), tracking_Results.results))
                #satelliteのY座標が一つ前のY座標より下に来るもののみ抽出
                rstAdd = [rst for rst in rstsSatellite[1][index_Cnt] if rst.satellite_Y >= lstSat[-1].satellite_Y]
                #一つ前の結果からの距離順にて昇順ソート。
                rstAdd.sort(key = lambda rst : (rst.satellite_X - lstSat[-1].satellite_X) ** 2 + (rst.satellite_Y - lstSat[-1].satellite_Y)**2)
            else:
                #対象の輪郭が1つの場合、そのまま結果の格納用オブジェクトをコピー
                rstAdd = rstsSatellite[1][index_Cnt]                
            #サテライト液滴追尾結果の格納
            tracking_Results.Set_SatelliteXY(rstsSatellite[1][index_delay], rstAdd[0].satellite_X, rstAdd[0].satellite_Y)

            #追尾検出3枚目以降            
            for i in range(2, len(rstsSatellite)):
                #i枚目の輪郭格納結果数が0であれば打ち切り
                if len(rstsSatellite[i][index_Cnt]) == 0:
                    break

                #すでに格納されている結果から、satellite_X座標がnanではないものを抽出。
                lstSat = list(filter(lambda rst: not math.isnan(rst.satellite_X), tracking_Results.results))     
                #ひとつ前の結果のサテライトY座標より下にサテライトY座標がくるもののみを抽出
                rstAdd = [rst for rst in rstsSatellite[i][index_Cnt] if rst.satellite_Y >= lstSat[-1].satellite_Y]
                #抽出結果数が0であれば打ち切り
                if len(rstAdd) == 0:
                    break
                #抽出結果を、ひとつ前のサテライト座標からの距離順に昇順ソート→最も近いものをサテライト液滴として採用。
                rstAdd.sort(key = lambda rst : (rst.satellite_X - lstSat[-1].satellite_X) ** 2 + (rst.satellite_Y - lstSat[-1].satellite_Y)**2)
                #サテライト検出結果を格納
                tracking_Results.Set_SatelliteXY(rstsSatellite[i][index_delay], rstAdd[0].satellite_X, rstAdd[0].satellite_Y)
    
    #格納結果をディレイ時間に対して昇順でソート
    tracking_Results.results.sort(key = lambda rst: rst.delay)
    #追尾結果の描画指定の場合
    if draw_Tracking_Results:
        #追尾結果描画関数の呼び出し
        drawTrackingResult(dirPath=dirPath, trackingRsts=tracking_Results, draw_Fitting_Line = draw_Fitting_Line, DEBUG = DEBUG)        
    #指定したディレクトリパスをprint（!!!後ほどコメントアウト!!!）
    print(dirPath)
    #追尾結果を返す
    return tracking_Results

#追尾結果格納クラス
class Tracking_Result_Elem:
    '''
    追尾結果格納クラス。外部からの直接アクセスはしない。
    Tracking_Resultsクラスからのみアクセス。
    
    Attribute
    ----------
    delay : float
        結果に対応するディレイ時間[us]
    main_X : float
        検出メイン液滴のX座標[pix]、初期値nan
    main_Y : float
        検出メイン液滴のY座標[pix]、初期値nan
    satellite_X : float
        検出サテライト液滴のX座標[pix]、初期値nan
    satellite_Y : float
        検出サテライト液滴のY座標[pix]、初期値nan    
    '''
    
    def __init__(self, delay):
        '''
        コンストラクタ
        delay値を引数から格納。
        delay以外のアトリビュートを全てnanにて初期値宣言
        
        Parameters
        ----------
        delay : float
            生成する結果に対応するdelay時間[us]
        
        Returns
        -------
        なし
        '''

        self.delay = delay
        self.main_X = math.nan
        self.main_Y = math.nan
        self.satellite_X = math.nan
        self.satellite_Y = math.nan
    
    def set_mainXY(self, main_X, main_Y):
        '''
        メイン液滴結果の格納関数
        
        Parameters
        ----------
        main_X : float
            メイン液滴X座標[pix]
        main_Y : float
            メイン液滴Y座標[pix]
        
        Returns
        -------
        なし       
        '''
        
        self.main_X = main_X
        self.main_Y = main_Y
    
    def set_satelliteXY(self, satellite_X, satellite_Y):
        '''
        サテライト液滴結果の格納関数
        
        Parameters
        ----------
        satellite_X : float
            サテライト液滴X座標[pix]
        satellite_Y : float
            サテライト液滴Y座標[pix]
        
        Returns
        -------
        なし       
        '''
        
        self.satellite_X = satellite_X
        self.satellite_Y = satellite_Y
    
    def dist_mainXY_satelliteXY(self):
        '''
        メイン - サテライト液滴座標の距離算出関数
        
        Parameters
        ----------
        なし
        
        Returns        
        -------
        dist_value : float
            メイン液滴 - サテライト液滴の距離[pix]
        '''
        
        #座標間距離の計算
        dist_value = math.sqrt((self.main_X - self.satellite_X)**2 + (self.main_Y - self.satellite_Y)**2)
        return dist_value

    
#追尾結果列格納クラス
class Tracking_Results:
    '''
    メイン - サテライト液滴座標群格納クラス
    
    Attribute
    ----------
    results : List<Tracking_Result_Elem>
        液滴座標追尾結果リスト
    
    '''
    
    def __init__(self):
        '''
        コンストラクタ
        resultsアトリビュートを宣言。
        '''
        
        self.results = []
        
    def Set_MainXY(self, delay, main_X, main_Y):
        '''
        メイン液滴座標の格納関数。
        すでにresults内に対応するdelayがある場合はそのリストに対して結果を格納。
        delayが無い場合は新たに要素を生成・追加して結果を格納。
        
        Parameters
        ----------
        delay : float
            格納する結果に対応するdelay時間[us]
        main_X : float
            メイン液滴X座標[pix]
        main_Y : float
            メイン液滴Y座標[pix]
        '''
        
        #引数のディレイ値が結果リストにあるかを参照する
        if not delay in [lst.delay for lst in self.results]:
            #存在しない場合は、新たに要素を生成
            tmpRst = Tracking_Result_Elem(delay)
            #要素をリストに追加
            self.results.append(tmpRst)
        
        #ビューにて対象ディレイの要素アドレスを参照する（この段階では必ずリスト内に指定要素がただ1つ存在する）。
        operating_elem = list(filter(lambda rst: rst.delay == delay, self.results))[0]
        #対象要素に、引数値を格納する。
        operating_elem.set_mainXY(main_X, main_Y)
        #resultsリストをdelay値にて昇順ソート
        self.results.sort(key = lambda rst:rst.delay)
        
    def Set_SatelliteXY(self, delay, satellite_X, satellite_Y):
        '''
        サテライト液滴座標の格納関数。
        すでにresults内に対応するdelayがある場合はそのリストに対して結果を格納。
        delayが無い場合は新たに要素を生成・追加して結果を格納。
        
        Parameters
        ----------
        delay : float
            格納する結果に対応するdelay時間[us]
        main_X : float
            メイン液滴X座標[pix]
        main_Y : float
            メイン液滴Y座標[pix]
        '''

        #引数のディレイ値が結果リストにあるかを参照する
        if not delay in [lst.delay for lst in self.results]:
            #存在しない場合は、新たに要素を生成
            tmpRst = Tracking_Result_Elem(delay)
            #要素をリストに追加           
            self.results.append(tmpRst) 

        #ビューにて対象ディレイの要素アドレスを参照する（この段階では必ずリスト内に指定要素がただ1つ存在する）。
        operating_elem = list(filter(lambda rst: rst.delay == delay, self.results))[0]
        #対象要素に、引数値を格納する。
        operating_elem.set_satelliteXY(satellite_X, satellite_Y)
        #resultsリストをdelay値にて昇順ソート
        self.results.sort(key = lambda rst:rst.delay)

    
    def Get_Main_Velocity(self, pixHigh = 0, pixLow = 1080):
        '''
        平均メイン液滴速度計算関数。
        計算対象データ数0 or 1でnan
        
        Parameters
        ----------
        pixHigh : int
            計算対象とするY座標上限値
        pixLow : int
            計算対象とするY座標下限値
            
        Return
        ----------
        ave : float
            平均メイン液滴速度値[pix/us]
        std : float
            標準偏差値[pix/us]
            ※不偏分散ではなく、母分散として取得している。
        
        '''
        
        lst = [l for l in self.results if not (math.isnan(l.main_X) or l.main_Y < pixHigh or l.main_Y > pixLow)]
        if len(lst) < 2:
            return math.nan, math.nan
        else:
            velElems = []
            for i in range(len(lst) - 1):
                diffDelay = lst[i+1].delay - lst[i].delay
                diffCoord = math.sqrt((lst[i+1].main_X - lst[i].main_X)**2 + (lst[i+1].main_Y - lst[i].main_Y)**2)
                velElems.append(diffCoord/diffDelay)
            ave = sum(velElems) / len(velElems)
            stdDev = sum([math.sqrt((ave - vel)**2 / len(velElems))  for vel in velElems])
        return ave, stdDev
    
    def Get_Satellite_Velocity(self, pixHigh = 0, pixLow = 1080):
        '''
        平均サテライト液滴速度計算関数。
        計算対象データ数0 or 1でnan
        
        Parameters
        ----------
        pixHigh : int
            計算対象とするY座標上限値
        pixLow : int
            計算対象とするY座標下限値
            
        Return
        ----------
        ave : float
            平均サテライト液滴速度値[pix/us]
        std : float
            標準偏差値[pix/us]
            ※不偏分散ではなく、母分散として取得している。
        
        '''
        
        lst = [l for l in self.results if not (math.isnan(l.satellite_X) or l.satellite_Y < pixHigh or l.satellite_Y > pixLow)]
        if len(lst) < 2:
            return math.nan, math.nan
        else:
            velElems = []
            for i in range(len(lst) - 1):
                diffDelay = lst[i+1].delay - lst[i].delay
                diffCoord = math.sqrt((lst[i+1].satellite_X - lst[i].satellite_X)**2 + (lst[i+1].satellite_Y - lst[i].satellite_Y)**2)
                velElems.append(diffCoord/diffDelay)            
            ave = sum(velElems) / len(velElems)
            stdDev = sum([math.sqrt((ave - vel)**2 / len(velElems)) for vel in velElems])
        return ave, stdDev
    
    def get_Main_vector_slope_intercept(self, pixHigh = 0, pixLow = 1080):
        '''
        メイン液滴の再近似直線取得関数
        近似は、delay - main_X、delay - main_Y、main_Y - main_X特性にて取得。
        各パラメータはそれぞれ、
            pred_main_X(delay) = slopeMainX_delay * delay + interceptMainX_delay
            pred_main_Y(delay) = slopeMainY_delay * delay + interceptMainY_delay
            pred_main_X(Y)     = slopeMainX_MainY * Y + interceptMainX_MainY
        という式にてフィッティングした結果となる。
        
        Parameters
        ----------
        pixHigh : int
            計算対象とするY座標上限値
        pixLow : int
            計算対象とするY座標下限値
            
        Return
        ----------
        retvalues : [float] (len(retvalues = 6))
            idx = 0
                slopeMainX_delay : float
                    main_X座標 - delay特性傾き[pix/us]
            idx = 1
                interceptMainX_delay : float
                    main_X座標 - delay特性切片[pix]
            idx = 2
                slopeMainY_delay ; float
                    main_Y座標 - delay特性傾き[pix/us]
            idx = 3
                interceptMainY_delay : float
                    main_Y座標 - delay特性切片[pix]
            idx = 4
                slopeMainX_MainY : float
                    main_X座標 - main_Y座標特性傾き[pix/pix]
            idx = 5
                interceptMainX_MainY : float
                    main_X座標 - main_Y特性切片[pix]        
        '''
        
        #計算対象リストの抽出
        #計算対象条件は、not (「メイン液滴X座標がnan」または「Y座標がpixHighより小さい」または「Y座標がpixLowより大きい」)
        lst = [l for l in self.results if not (math.isnan(l.main_X) or l.main_Y < pixHigh or l.main_Y > pixLow)]       
        #計算対象リスト要素数が0 or 1では計算不可能なので、nanを返す
        if len(lst) < 2:
            retValues = [math.nan, math.nan, math.nan, math.nan, math.nan, math.nan]
        #計算対象リスト要素数が2以上の場合
        else:
            #ディレイ値、メインX座標、メインY座標の平均値を取得
            aveDelay = sum(map(lambda rst: rst.delay, lst))/len(lst)
            aveMainX = sum(map(lambda rst: rst.main_X, lst))/len(lst)
            aveMainY = sum(map(lambda rst: rst.main_Y, lst))/len(lst)   

            #ディレイ値、メインX座標、メインY座標の分散値を取得
            sumVarianceSq_delay = sum(map(lambda rst: (rst.delay - aveDelay)**2, lst))
            sumVarianceSq_mainX = sum(map(lambda rst: (rst.main_X - aveMainX)**2, lst))
            sumVarianceSq_mainY = sum(map(lambda rst: (rst.main_Y - aveMainY)**2, lst))
            
            #メインX - delay、メインY - delay、メインX - メインY座標の共分散を取得
            sumCoVariance_mainX_delay = sum(map(lambda rst: (rst.delay - aveDelay)*(rst.main_X - aveMainX), lst))
            sumCoVariance_mainY_delay = sum(map(lambda rst: (rst.delay - aveDelay)*(rst.main_Y - aveMainY), lst))
            sumCoVariance_mainX_mainY = sum(map(lambda rst: (rst.main_X - aveMainX)*(rst.main_Y - aveMainY), lst))
            
            #「傾き = 共分散 / 分散」から傾きを取得 
            slopeMainX_delay = sumCoVariance_mainX_delay/sumVarianceSq_delay
            slopeMainY_delay = sumCoVariance_mainY_delay/sumVarianceSq_delay
            slopeMainX_MainY = sumCoVariance_mainX_mainY/sumVarianceSq_mainY
            
            #「切片 = 平均 - 傾き / 平均」から切片を取得
            interceptMainX_delay = aveMainX - slopeMainX_delay * aveDelay
            interceptMainY_delay = aveMainY - slopeMainY_delay * aveDelay   
            interceptMainX_MainY = aveMainX - slopeMainX_MainY * aveMainY
            
            #値をリストに格納
            retValues = [slopeMainX_delay, interceptMainX_delay, slopeMainY_delay, interceptMainY_delay, slopeMainX_MainY, interceptMainX_MainY]
        return retValues
    
    def get_Satellite_vector_slope_intercept(self, pixHigh = 0, pixLow = 1080):
        '''
        サテライト液滴の再近似直線取得関数
        近似は、delay - sattelite_X、delay - satellite_Y、satellite_Y - satellite_X特性にて取得。
        各パラメータはそれぞれ、
            pred_satellite_X(delay) = slopeSatelliteX_delay * delay + interceptSatelliteX_delay
            pred_satellite_Y(delay) = slopeSatelliteY_delay * delay + interceptSatelliteY_delay
            pred_satellite_X(Y)     = slopeSatelliteX_SatelliteY * Y + interceptSatelliteX_SatelliteY
        という式にてフィッティングした結果となる。
        
        Parameters
        ----------
        pixHigh : int
            計算対象とするY座標上限値
        pixLow : int
            計算対象とするY座標下限値
            
        Return
        ----------
        retValues : [float] (len(retValues) = 6)
            idx = 0
                slopeSatelliteX_delay : float
                    satellite_X座標 - delay特性傾き[pix/us]
            idx = 1
                interceptSatelliteX_delay : float
                    satellite_X座標 - delay特性切片[pix]
            idx = 2
                slopeSatelliteY_delay : float
                    satellite_Y座標 - delay特性傾き[pix/us]
            idx = 3
                interceptSatelliteY_delay : float
                    satellite_Y座標 - delay特性切片[pix]
            idx = 4
                slopeSatelliteX_SatelliteY : float
                    satellite_X座標 - satellite_Y座標特性傾き[pix/pix]
            idx = 5
                interceptSatelliteX_SatelliteY : float
                    satellite_X座標 - satellite_Y特性切片[pix]        
        '''
 
        #計算対象リストの抽出
        #計算対象条件は、not (「メイン液滴X座標がnan」または「Y座標がpixHighより小さい」または「Y座標がpixLowより大きい」)
        lst = [l for l in self.results if not (math.isnan(l.satellite_X) or l.satellite_Y < pixHigh or l.satellite_Y > pixLow)]
        #計算対象リスト要素数が0 or 1では計算不可能なので、nanを返す
        if len(lst) < 2:
            retValues = [math.nan, math.nan, math.nan, math.nan, math.nan, math.nan]
        #計算対象リスト要素数が2以上の場合
        else:           
            #ディレイ値、メインX座標、メインY座標の平均値を取得
            aveDelay = sum(map(lambda rst: rst.delay, lst))/len(lst)
            aveSatelliteX = sum(map(lambda rst: rst.satellite_X, lst))/len(lst)
            aveSatelliteY = sum(map(lambda rst: rst.satellite_X, lst))/len(lst)   
            
            #ディレイ値、メインX座標、メインY座標の分散値を取得
            sumVarianceSq_delay = sum(map(lambda rst: (rst.delay - aveDelay)**2, lst))
            sumVarianceSq_satelliteX = sum(map(lambda rst: (rst.satellite_X - aveSatelliteX)**2, lst))
            sumVarianceSq_satelliteY = sum(map(lambda rst: (rst.satellite_Y - aveSatelliteY)**2, lst))
            
            #メインX - delay、メインY - delay、メインX - メインY座標の共分散を取得
            sumCoVariance_satelliteX_delay = sum(map(lambda rst: (rst.delay - aveDelay)*(rst.satellite_X - aveSatelliteX), lst))
            sumCoVariance_satelliteY_delay = sum(map(lambda rst: (rst.delay - aveDelay)*(rst.satellite_Y - aveSatelliteY), lst))
            sumCoVariance_satelliteX_satelliteY = sum(map(lambda rst: (rst.satellite_Y - aveSatelliteY)*(rst.satellite_X - aveSatelliteX), lst))
            
            #「傾き = 共分散 / 分散」から傾きを取得 
            slopeSatelliteX_delay = sumCoVariance_satelliteX_delay/sumVarianceSq_delay
            slopeSatelliteY_delay = sumCoVariance_satelliteY_delay/sumVarianceSq_delay
            slopeSatelliteX_satelliteY = sumCoVariance_satelliteX_satelliteY/sumVarianceSq_satelliteY
            
            #「切片 = 平均 - 傾き / 平均」から切片を取得            
            interceptSatelliteX_delay = aveSatelliteX - slopeSatelliteX_delay * aveDelay
            interceptSatelliteY_delay = aveSatelliteY - slopeSatelliteY_delay * aveDelay   
            interceptSatelliteX_satelliteY = aveSatelliteX - slopeSatelliteX_satelliteY * aveSatelliteY
            
            #値をリストに格納
            retValues = [slopeSatelliteX_delay, interceptSatelliteX_delay, slopeSatelliteY_delay, interceptSatelliteY_delay, \
                         slopeSatelliteX_satelliteY, interceptSatelliteX_satelliteY]
        return retValues
    
    def Get_Main_Angle_degrees(self, pixHigh = 0, pixLow = 1080):
        '''
        メイン液滴飛翔角度計算関数
        鉛直下向きを0°として、反時計回りに角度を定義。
        
        Parameters
        ----------
        pixHigh : int
            計算対象とするY座標上限値[pix]
        pixLow : int
            計算対象とするY座標下限値[pix]
            
        Return
        ----------
        retValue : float
            メイン液滴飛翔方向[degrees]
        '''
        
        #計算対象リストの抽出
        #計算対象条件は、not (「メイン液滴X座標がnan」または「Y座標がpixHighより小さい」または「Y座標がpixLowより大きい」)
        lst = [l for l in self.results if not (math.isnan(l.main_X) or l.main_Y < pixHigh or l.main_Y > pixLow)]       
        #計算対象リスト要素数が0 or 1では計算不可能なので、nanを返す
        if len(lst) < 2:
            retValue = math.nan
        #計算対象リスト要素数が2以上の場合
        else:
            #メイン液滴傾き取得
            fit_result_slope = self.get_Main_vector_slope_intercept(pixHigh, pixLow)[4]
            #math.atan(slope)にて角度[rad]を取得、math.degrees()にて角度[rad]→角度[degrees]の変換
            retValue = math.degrees(math.atan(fit_result_slope))        
        return retValue

    def Get_Satellite_Angle_degrees(self, pixHigh = 0, pixLow = 1080):
        '''
        サテライト液滴飛翔角度計算関数
        鉛直下向きを0°として、反時計回りに角度を定義。
        
        Parameters
        ----------
        pixHigh : int
            計算対象とするY座標上限値[pix]
        pixLow : int
            計算対象とするY座標下限値[pix]
            
        Return
        ----------
        retValue : float
            サテライト液滴飛翔方向[degrees]
        '''
        
        #計算対象リストの抽出
        #計算対象条件は、not (「メイン液滴X座標がnan」または「Y座標がpixHighより小さい」または「Y座標がpixLowより大きい」)
        lst = [l for l in self.results if not (math.isnan(l.satellite_X) or l.satellite_Y < pixHigh or l.satellite_Y > pixLow)]
        #計算対象リスト要素数が0 or 1では計算不可能なので、nanを返す
        if len(lst) < 2:
            retValue = math.nan
        #計算対象リスト要素数が2以上の場合
        else:
            #サテライト液滴傾き取得
            fit_result_slope = self.get_Satellite_vector_slope_intercept(pixHigh, pixLow)[4]
            #math.atan(slope)にて角度[rad]を取得、math.degrees()にて角度[rad]→角度[degrees]の変換
            retValue = math.degrees(math.atan(fit_result_slope))
        return retValue

    def Get_MainXY_Fit_Error_Min_Max_Range(self, pixHigh = 0, pixLow = 1080):
        '''
        サテライト液滴飛翔角度計算関数
        鉛直下向きを0°として、反時計回りに角度を定義。
        
        Parameters
        ----------
        pixHigh : int
            計算対象とするY座標上限値[pix]
        pixLow : int
            計算対象とするY座標下限値[pix]
            
        Return
        ----------
        retValue : float
            サテライト液滴飛翔方向[degrees]
        '''
        
        lst = [l for l in self.results if not (math.isnan(l.main_X) or l.main_Y < pixHigh or l.main_Y > pixLow)]       
        if len(lst) < 2:
            retValue = [math.nan, math.nan]
        else:
            fit_results = self.get_Main_vector_slope_intercept(pixHigh, pixLow)
            fit_result_slope, fit_resut_intercept = fit_results[4], fit_results[5]
            evalList = [rst.main_X - fit_result_slope * rst.main_Y - fit_resut_intercept for rst in lst]
            retValue = [min(evalList), max(evalList)]
        return retValue
        
    def Get_SatelliteXY_Fit_Error_Min_Max_Range(self, pixHigh = 0, pixLow = 1080):
        lst = [l for l in self.results if not (math.isnan(l.satellite_X) or l.satellite_Y < pixHigh or l.satellite_Y > pixLow)]       
        if len(lst) < 2:
            retValue = [math.nan, math.nan]
        else:
            fit_results = self.get_Satellite_vector_slope_intercept(pixHigh, pixLow)
            fit_result_slope, fit_resut_intercept = fit_results[4], fit_results[5]
            evalList = [rst.satellite_X - fit_result_slope * rst.satellite_Y - fit_resut_intercept for rst in lst]
            retValue = [min(evalList), max(evalList)]
        return retValue   
    
def drawTrackingResult(dirPath, trackingRsts, draw_Fitting_Line, DEBUG = False):
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
            
    Return
    ----------
        なし
    
    '''
    
    pathes = glob.glob(dirPath + "/*.jpg")
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
        j = 10
        flag_delay_is_get = False
        while j > 4:
            try:
                delay = float(f[-j:-4])
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
                im = cv2.line(im, ((int)(lineMainResults[5]), 0), ((int)(lineMainResults[4]*im.shape[0] + lineMainResults[5]), im.shape[0]), \
                              (64, 64, 128), 1)
                predMainX = (int)(lineMainResults[0] * delay + lineMainResults[1])
                predMainY = (int)(lineMainResults[2] * delay + lineMainResults[3])
                im = cv2.circle(im, (predMainX, predMainY), signature_size, (64,64,128), 1)
            if not any([math.isnan(value) for value in lineSatelliteResults]):
                im = cv2.line(im, ((int)(lineSatelliteResults[5]), 0), ((int)(lineSatelliteResults[4]*im.shape[0] + lineSatelliteResults[5]), im.shape[0]), \
                              (128, 64, 64), 1)
                predSatX = (int)(lineSatelliteResults[0] * delay + lineSatelliteResults[1])
                predSatY = (int)(lineSatelliteResults[2] * delay + lineSatelliteResults[3])
                im = cv2.circle(im, (predSatX, predSatY), signature_size, (128,64,64), 2)
        savePath = dirPath + "/trackingRsts/" + os.path.splitext(os.path.basename(f))[0] + "_drawTRResults.jpg"
        cv2.imwrite(savePath, im)
        
        if DEBUG:
            calculation_log('tracking result file is exported at {}'.format(savePath))
