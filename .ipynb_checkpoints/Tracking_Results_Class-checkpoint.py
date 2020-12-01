import math
import Tracking_Result_Elem_Class

#追尾結果列格納クラス
class Tracking_Results:
    '''
    メイン - サテライト液滴座標群格納クラス
    
    Attribute
    ----------
    results : List<Tracking_Result_Elem>
        液滴座標追尾結果リスト
    
    method
    ----------
    __init__ : None
        クラス生成、初期化のみ実施。
    Set_MainXY(delay, main_X, main_Y) : None
        results内の対応するdelayが格納されたTracking_Result_ElemクラスにメインX、Y座標を格納する。
        対応するdelayが無い場合は新しく生成する。
    Set_SatelliteXY(delay, main_X, main_Y) : None
        results内の対応するdelayが格納されたTracking_Result_ElemクラスにサテライトX、Y座標を格納する。
        対応するdelayが無い場合は新しく生成する。
    Get_Main_Velocity(pixHigh = 0, pixLow = 1080) : [aveVelocity, stdivVelocity]
        Y座標がpixHigh ~ pixLowの範囲に入っている領域でのメイン液滴の平均速度、標準偏差値を計算する。
    Get_Satellite_Velocity(pixHigh = 0, pixLow = 1080) : [aveVelocity, stdivVelocity]
        Y座標がpixHigh ~ pixLowの範囲に入っている領域でのサテライト液滴の平均速度、標準偏差値を計算する。
    get_Main_vector_slope_intercept(pixHigh = 0, pixLow = 1080) : [float×6]
        Y座標がpixHigh ~ pixLowの範囲に入っている領域でのメイン液滴の再近似直線を計算する。
    get_Satellite_vector_slope_intercept(pixHigh = 0, pixLow = 1080) : [float×6]
        Y座標がpixHigh ~ pixLowの範囲に入っている領域でのサテライト液滴の再近似直線を計算する。
    Get_Main_Angle_degrees(pixHigh = 0, pixLow = 1080) : float
        Y座標がpixHigh ~ pixLowの範囲に入っている領域でのメイン液滴の吐出角度を計算する。
    Get_Satellite_Angle_degrees(pixHigh = 0, pixLow = 1080) : float
        Y座標がpixHigh ~ pixLowの範囲に入っている領域でのサテライト液滴の吐出角度を計算する。
    Get_MainXY_Fit_Error_Min_Max_Range(pixHigh = 0, pixLow = 1080) : float
        Y座標がpixHigh ~ pixLowの範囲に入っている領域でのメイン液滴の再近似曲線からのズレの最大値を計算する。
    Get_SatelliteXY_Fit_Error_Min_Max_Range(pixHigh = 0, pixLow = 1080) : float
        Y座標がpixHigh ~ pixLowの範囲に入っている領域でのサテライト液滴の再近似曲線からのズレの最大値を計算する。
    '''
    
    def __init__(self):
        '''
        コンストラクタ
        resultsアトリビュートを宣言。
        '''
        
        self.results = []
        return None

        
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
            tmpRst = Tracking_Result_Elem_Class.Tracking_Result_Elem(delay)
            #要素をリストに追加
            self.results.append(tmpRst)
        
        #ビューにて対象ディレイの要素アドレスを参照する（この段階では必ずリスト内に指定要素がただ1つ存在する）。
        operating_elem = list(filter(lambda rst: rst.delay == delay, self.results))[0]
        #対象要素に、引数値を格納する。
        #参照型クラスに対する操作なので、下記操作でresults内のデータが同時に操作される。
        operating_elem.set_mainXY(main_X, main_Y)
        #resultsリストをdelay値にて昇順ソート
        self.results.sort(key = lambda rst:rst.delay)
        
        return None
       
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
            tmpRst = Tracking_Result_Elem_Class.Tracking_Result_Elem(delay)
            #要素をリストに追加           
            self.results.append(tmpRst) 

        #ビューにて対象ディレイの要素アドレスを参照する（この段階では必ずリスト内に指定要素がただ1つ存在する）。
        operating_elem = list(filter(lambda rst: rst.delay == delay, self.results))[0]
        #対象要素に、引数値を格納する。
        #参照型クラスに対する操作なので、下記操作でresults内のデータが同時に操作される。
        operating_elem.set_satelliteXY(satellite_X, satellite_Y)
        #resultsリストをdelay値にて昇順ソート
        self.results.sort(key = lambda rst:rst.delay)
        
        return None
    
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
            aveDelay = sum(map(lambda rst: rst.delay, lst))/(float)(len(lst))
            aveMainX = sum(map(lambda rst: (float)(rst.main_X), lst))/(float)(len(lst))
            aveMainY = sum(map(lambda rst: (float)(rst.main_Y), lst))/(float)(len(lst))   

            #ディレイ値、メインX座標、メインY座標の分散値を取得
            sumVarianceSq_delay = sum(map(lambda rst: (rst.delay - aveDelay)**2, lst))
            sumVarianceSq_mainX = sum(map(lambda rst: ((float)(rst.main_X) - aveMainX)**2, lst))
            sumVarianceSq_mainY = sum(map(lambda rst: ((float)(rst.main_Y) - aveMainY)**2, lst))
            
            #メインX - delay、メインY - delay、メインX - メインY座標の共分散を取得
            sumCoVariance_mainX_delay = sum(map(lambda rst: (rst.delay - aveDelay)*((float)(rst.main_X) - aveMainX), lst))
            sumCoVariance_mainY_delay = sum(map(lambda rst: (rst.delay - aveDelay)*((float)(rst.main_Y) - aveMainY), lst))
            sumCoVariance_mainX_mainY = sum(map(lambda rst: ((float)(rst.main_X) - aveMainX)*((float)(rst.main_Y) - aveMainY), lst))
            
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
            aveSatDelay = sum(map(lambda rst: rst.delay, lst))/(float)(len(lst))
            aveSatelliteX = sum(map(lambda rst: (float)(rst.satellite_X), lst))/(float)(len(lst))
            aveSatelliteY = sum(map(lambda rst: (float)(rst.satellite_Y), lst))/(float)(len(lst))   
            
            #ディレイ値、メインX座標、メインY座標の分散値を取得
            sumVarianceSq_delay = sum(map(lambda rst: (rst.delay - aveSatDelay)**2, lst))
            sumVarianceSq_satelliteX = sum(map(lambda rst: ((float)(rst.satellite_X) - aveSatelliteX)**2, lst))
            sumVarianceSq_satelliteY = sum(map(lambda rst: ((float)(rst.satellite_Y) - aveSatelliteY)**2, lst))
            
            #メインX - delay、メインY - delay、メインX - メインY座標の共分散を取得
            sumCoVariance_satelliteX_delay = sum(map(lambda rst: (rst.delay - aveSatDelay)*((float)(rst.satellite_X) - aveSatelliteX), lst))
            sumCoVariance_satelliteY_delay = sum(map(lambda rst: (rst.delay - aveSatDelay)*((float)(rst.satellite_Y) - aveSatelliteY), lst))
            sumCoVariance_satelliteX_satelliteY = sum(map(lambda rst: ((float)(rst.satellite_Y) - aveSatelliteY)*((float)(rst.satellite_X) - aveSatelliteX), lst))
            
            #「傾き = 共分散 / 分散」から傾きを取得 
            slopeSatelliteX_delay = sumCoVariance_satelliteX_delay/sumVarianceSq_delay
            slopeSatelliteY_delay = sumCoVariance_satelliteY_delay/sumVarianceSq_delay
            slopeSatelliteX_satelliteY = sumCoVariance_satelliteX_satelliteY/sumVarianceSq_satelliteY
            
            #「切片 = 平均 - 傾き / 平均」から切片を取得            
            interceptSatelliteX_delay = aveSatelliteX - slopeSatelliteX_delay * aveSatDelay
            interceptSatelliteY_delay = aveSatelliteY - slopeSatelliteY_delay * aveSatDelay   
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
            #nanを返すと最終的に-1になるので、-90 < Θ < 90の範囲外の値を入れる。
            value_angle_is_not_detected = float('inf')
            retValue = value_angle_is_not_detected
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
            #nanを返すと最終的に-1になるので、-90 < Θ < 90の範囲外の値を入れる。
            value_angle_is_not_detected = float('inf')
            retValue = value_angle_is_not_detected
        #計算対象リスト要素数が2以上の場合
        else:
            #サテライト液滴傾き取得
            fit_result_slope = self.get_Satellite_vector_slope_intercept(pixHigh, pixLow)[4]
            #math.atan(slope)にて角度[rad]を取得、math.degrees()にて角度[rad]→角度[degrees]の変換
            retValue = math.degrees(math.atan(fit_result_slope))
        return retValue

    def Get_MainXY_Fit_Error_Min_Max_Range(self, pixHigh = 0, pixLow = 1080):
        '''
        メイン液滴ブレ取得関数
        再近似特性直線からの予測値と実測値のズレに最大値（正の方向へのズレ）、最小値（負の方向へのズレ）を取得
        
        Parameters
        ----------
        pixHigh : int
            計算対象とするY座標上限値[pix]
        pixLow : int
            計算対象とするY座標下限値[pix]
            
        Return
        ----------
        retValue : [min_diff : float, max_diff : float]
            メイン液滴と特性直線のズレの最小値および最大値
        '''
        #計算対象リストの抽出
        #計算対象条件は、not (「メイン液滴X座標がnan」または「Y座標がpixHighより小さい」または「Y座標がpixLowより大きい」)
        lst = [l for l in self.results if not (math.isnan(l.main_X) or l.main_Y < pixHigh or l.main_Y > pixLow)]       
        #計算対象リスト要素数が0 or 1では計算不可能なので、nanを返す
        if len(lst) < 2:
            #nanを返すと最終的に-1になるので、-90 < Θ < 90の範囲外の値を入れる。
            retValue = [-float('inf'), float('inf')]
        else:
            #メイン液滴液滴特性取得
            fit_results = self.get_Main_vector_slope_intercept(pixHigh, pixLow)
            fit_result_slope, fit_resut_intercept = fit_results[4], fit_results[5]
            #特性予測値からの距離を取得
            evalList = [(float)(rst.main_X) - fit_result_slope * (float)(rst.main_Y) - fit_resut_intercept for rst in lst]
            #最大、最小ズレを取得
            retValue = [min(evalList), max(evalList)]
        return retValue
        
    def Get_SatelliteXY_Fit_Error_Min_Max_Range(self, pixHigh = 0, pixLow = 1080):
        '''
        サテライト液滴ブレ取得関数
        再近似特性直線からの予測値と実測値のズレに最大値（正の方向へのズレ）、最小値（負の方向へのズレ）を取得
        
        Parameters
        ----------
        pixHigh : int
            計算対象とするY座標上限値[pix]
        pixLow : int
            計算対象とするY座標下限値[pix]
            
        Return
        ----------
        retValue : [min_diff : float, max_diff : float]
            サテライト液滴と特性直線のズレの最小値および最大値
        '''
        #計算対象リストの抽出
        #計算対象条件は、not (「サテライト液滴X座標がnan」または「Y座標がpixHighより小さい」または「Y座標がpixLowより大きい」)
        lst = [l for l in self.results if not (math.isnan(l.satellite_X) or l.satellite_Y < pixHigh or l.satellite_Y > pixLow)]       
        #計算対象リスト要素数が0 or 1では計算不可能なので、nanを返す
        if len(lst) < 2:
            retValue = [-float('inf'), float('inf')]
        else:
            #サテライト液滴液滴特性取得
            fit_results = self.get_Satellite_vector_slope_intercept(pixHigh, pixLow)
            fit_result_slope, fit_resut_intercept = fit_results[4], fit_results[5]
            #特性予測値からの距離を取得
            evalList = [(float)(rst.satellite_X) - fit_result_slope * (float)(rst.satellite_Y) - fit_resut_intercept for rst in lst]
            #最大、最小ズレを取得
            retValue = [min(evalList), max(evalList)]
        return retValue   
    
