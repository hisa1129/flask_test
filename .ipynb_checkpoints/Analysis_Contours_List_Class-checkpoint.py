import numpy as np
from CalculationLog import calculation_log
import Contour_Elem
from Contour_Elem import *
import math
from itertools import groupby
from Tracking_Results_Class import *

#analysisResults用インデックス、配列2番目にて指定。
IDX_DELAY = 0
IDX_CNT = 1

#輪郭データ格納numpyArray用インデックス、配列3番目で指定。
IDX_X = 0
IDX_Y = 1

#解析結果群格納クラス
class Analysis_Results_List:
    '''
    連続輪郭解析結果格納関数
    
    Attributes
    ----------
    analysisResults : [delay, [Analysis_Result]] 
        輪郭解析結果群
    __area_mirgin_detect_faced : float
        液滴吐出開始検知面積閾値[pix]
    __area_mirgin_detect_separation : float
        液滴分離検出面積閾値[pix]
    __arc_length_mirgin_detect_separation : float
        液滴分離検出輪郭長閾値[pix]
    __solidity_mirgin_detect_separation : float
        液滴分離検出solidity比閾値[U]
    __noise_remove_topological_dist_thresh : float
        ノイズ除去時輪郭パラメータ類似判定閾値
    __nosie_remove_area_thresh : float
        ノイズ除去時輪郭面積上限閾値[pix]
    __DEBUG : bool
        デバッグモード
    solidity : float
        ノズル輪郭の最小solidity値
    flag_faced_is_detected : bool
        液滴吐出開始検知
    delay_faced : float
        液滴吐出開始ディレイ[us]
    flag_separated_is_detected : bool
        液滴分離検知
    delay_separated : float
        液滴分離ディレイ[us]
    delay_max_regament_detected :float
        最大リガメント長時ディレイ[us]
    max_regament_length : float
        最大リガメント長さ[pix]
    arc_solidity : float
        凸包輪郭長/実輪郭長比[U]
    freq_Y :int
        最頻出Y座標[pix]
    freq_Y_cnt :int
        最頻出Y座標検出数[pix]
    num_contours_at_first : int
        最小ディレイにおける輪郭数[cnt]
        
    method
    ----------
    __init__ : None
        コンストラクタ、データのセット、ノイズ除去と輪郭のみから計算可能な特徴量のセット。
        ノイズ除去はremove_noise関数、特徴量セットは以下のsetサブ関数を使う。
    __set_solidity : None
        solidity最小値設定関数
    __set_droplet_faced : None
        液滴吐出開始検知およびディレイタイムセット関数
    __set_droplet_separated : None
        液滴分離検知およびディレイタイムセット関数
    __set_regament_max : None
        リガメント最大抽出関数
    __set_arc_solidity : None
        凸包輪郭長/実輪郭長比最大値セット関数
    __set_volume : None
        体積計算関数
    __set_freq_Y : None
        最頻出Y座標抽出関数
    __set_num_initial_contour : None
        初回画像輪郭数
    __set_magnitude_of_doubletDroplet : None
        二重吐出度抽出関数
    __get_CntDist_is_closer(cnt1, cnt2, thresh) : bool
        輪郭類似度判定関数
    __remove_noise : bool
        ノイズ除去関数
    
    Check_exotic_droplet_exists(trackingRst, pix_mirgin) : bool
        逸脱輪郭判定関数
    '''
    def __init__(self,
                 analysis_results_list,
                 area_mirgin_detect_faced,
                 area_mirgin_detect_separation,
                 arc_length_mirgin_detect_separation,
                 solidity_mirgin_detect_separation,
                 noise_remove_topological_dist_thresh,
                 noise_remove_area_thresh,
                 DEBUG):
        '''
        コンストラクタ
        １：単純な輪郭データ群をディレイ時間でgroupByの後にリストとして格納
        ２：ノイズを除去
        ３：特徴量計算しクラス変数に格納        
        
        Parameters
        ----------
        analysis_results_list : [Analysis_Result]
            輪郭解析結果群
        area_mirgin_detect_faced : float
            液滴吐出開始検知閾値面積 [pix]
        area_mirgin_detect_separation : float
            液滴分離検知閾値面積[pix]
        arc_length_mirgin_detect_separation : float
            液滴分離検知閾値輪郭長[pix]
        solidity_mirgin_detect_separation : float
            液滴分離検知閾値solidity [U]
        noise_remove_topological_dist_thresh : float
            ノイズ除去時輪郭類似判定用の位相空間距離 [U]
        nosie_remove_area_thresh : int
            ノイズ除去時輪郭面積上限[pix]
        DEBUG : bool
            デバッグモード判定
        '''
        if DEBUG:
            calculation_log('constructor was called.')
        #ディレイでソート
        analysis_results_list.sort(key=lambda rst: rst.delay)
        #結果格納リスト
        groupResults = []
        #グループ化
        for delay_key, contours_group in groupby(analysis_results_list, key=lambda rst:rst.delay):
            listGroup = list(contours_group)
            if len(listGroup) > 1:
                #面積にて降順ソート
                listGroup.sort(key=lambda rst:rst.area, reverse=True)
            #ディレイタイムでGroupBy、groupResultsを生成。
            groupResults.append([delay_key, listGroup])
            if DEBUG:
                calculation_log('delay = {}, and contour count = {}'.format(delay_key, len(listGroup)))
        #結果の格納
        if DEBUG:
            calculation_log('set params to class_field parameters.')
        #ディレイ時間にて昇順ソートしanalysisResultsに格納
        self.analysisResults = sorted(groupResults, key=lambda grs:grs[IDX_DELAY])
        #以下、プロパティのセット
        self.__DEBUG = DEBUG
        self.__area_mirgin_detect_faced = area_mirgin_detect_faced
        self.__area_mirgin_detect_separation = area_mirgin_detect_separation
        self.__arc_length_mirgin_detect_separation = arc_length_mirgin_detect_separation
        self.__solidity_mirgin_detect_separation = solidity_mirgin_detect_separation
        self.__noise_remove_topological_dist_thresh = noise_remove_topological_dist_thresh
        self.__noise_remove_area_thresh = noise_remove_area_thresh
        if DEBUG:
            calculation_log('set params to class_field parameters was completed.')
        #ノイズ除去関数によるノイズ除去
        self.__remove_noise()
        if DEBUG:
            calculation_log('noises was removed.')
        #パラメータセット関数によるパラメータセット
        self.__set_solidity()  
        self.__set_droplet_faced()
        self.__set_droplet_separated()               
        self.__set_regament_max()
        self.__set_arc_solidity()
        self.__set_volume()
        self.__set_freq_Y()
        self.__set_num_initial_contour()

        if DEBUG:
            calculation_log('set feature params was completed.')
        return None
       
    def __set_solidity(self):
        '''
        Solidity値取得関数
        各画像の面積最大輪郭（=ノズル輪郭）の凸包輪郭面積 / 実面積比の最小値を取得する。
        ノズルに異物がついているとこの値は大きくなるので、ある閾値を越えた場合に異物があると判定する。
        詳細アルゴリズムはコメントにて記載する。
        '''
        if self.__DEBUG:
            calculation_log('solidity method was called.') 
        #各ディレイ時間における輪郭データを面積をキーに降順ソート
        rsts = [[data[IDX_DELAY], sorted(data[IDX_CNT], key=lambda rs: rs.area, reverse=True)] for data in self.analysisResults]
        #各ディレイ時間を最大面積輪郭のSolidity値をキーに昇順ソート
        #Solidity = convex_hukk_contour_area / area
        rsts.sort(key=lambda rst:rst[IDX_CNT][0].convex_hull_contour_area / rst[IDX_CNT][0].area)
        #Solidityの最小値を取得
        solidity = rsts[0][IDX_CNT][0].convex_hull_contour_area / rsts[0][IDX_CNT][0].area
        #クラスプロパティにセット
        self.solidity = solidity
    
        return None
    
    def __set_droplet_faced(self):
        '''
        液滴吐出開始検知関数
        液滴吐出開始を検知し、吐出有無およびそのディレイタイムをflag_faced_is_detected、およびdelay_facedに値をセットする。        
        吐出開始検知が無い場合はdelay_faced = -1.0
        詳細アルゴリズムはコメントにて記載。
        '''
        if self.__DEBUG:
            calculation_log('detect_faced method was called.')
        #初期値のセット
        delay_faced = -1.0
        flag_faced_is_detected = False
        #
        for i in range(1, len(self.analysisResults)):
            evaluation_delay = self.analysisResults[i][IDX_DELAY]
            evaluation_contour_list_after = sorted(self.analysisResults[i][IDX_CNT], key = lambda cnt: cnt.area, reverse = True)
            evaluation_contour_list_before = sorted(self.analysisResults[i-1][IDX_CNT], key = lambda cnt2: cnt2.area, reverse = True)
            flag_detection = evaluation_contour_list_after[0].convex_hull_contour_area - self.__area_mirgin_detect_faced > \
            evaluation_contour_list_before[0].convex_hull_contour_area
            if self.__DEBUG:
                calculation_log('delay : {}, evaluation_area : {} evaluation_area_before : {}'.format(
                    evaluation_delay,
                    evaluation_contour_list_after[0].convex_hull_contour_area,
                    evaluation_contour_list_before[0].convex_hull_contour_area)
                               )
            if flag_detection:
                delay_faced = evaluation_delay
                flag_faced_is_detected = True
                if self.__DEBUG:
                    calculation_log('detect_faced delay is {}.'.format(delay_faced))
                break
        
        self.flag_faced_is_detected = flag_faced_is_detected
        self.delay_faced = delay_faced
        
        return None
    
    def __set_droplet_separated(self):
        '''
        液滴分離検知関数
        液滴吐出開始を検知し、吐出有無およびそのディレイタイムをflag_separated_is_detected、およびdelay_separatedに値をセットする。        
        分離検知が無い場合はdelay_separated = -1.0
        詳細アルゴリズムはコメントにて記載
        '''
        if self.__DEBUG:
            calculation_log('separation method was called.')
        delay_separated = -1.0
        flag_separated_is_detected = False
        seeking_results_list = [data for data in self.analysisResults if data[0] > self.delay_faced]
        solidity_base = self.solidity
        for i in range(1, len(seeking_results_list)):
            eval_delay = seeking_results_list[i][IDX_DELAY]
            eval_contour_list_after = sorted(seeking_results_list[i][IDX_CNT], key = lambda cnt: cnt.area, reverse = True)
            eval_contour_list_before = sorted(seeking_results_list[i-1][IDX_CNT], key = lambda cnt2: cnt2.area, reverse = True)
            flag_convexhull_contour_area = (eval_contour_list_after[0].convex_hull_contour_area +\
                                            self.__area_mirgin_detect_separation < eval_contour_list_before[0].convex_hull_contour_area)
            flag_convexhull_contour_arclength = (eval_contour_list_after[0].arclength + self.__arc_length_mirgin_detect_separation <\
                                                 eval_contour_list_before[0].arclength)
            solidity_at_seeking_result = eval_contour_list_after[0].convex_hull_contour_area / eval_contour_list_after[0].area
            eval_ratio = solidity_at_seeking_result / solidity_base
            flag_solidity_is_plausible =  eval_ratio < self.__solidity_mirgin_detect_separation
            if self.__DEBUG:
                calculation_log('delay at {}, solidity is {}, eval ratio is {}, and flag is {}'.format(
                    eval_delay,
                    solidity_at_seeking_result,
                    eval_ratio,
                    flag_solidity_is_plausible)
                               )               
            if flag_convexhull_contour_area and flag_convexhull_contour_arclength and flag_solidity_is_plausible:
                delay_separated = seeking_results_list[i][IDX_DELAY]
                flag_separated_is_detected = True
                break
        if self.__DEBUG:
            calculation_log('separated_delay is {}'.format(delay_separated))
        self.flag_separated_is_detected = flag_separated_is_detected
        self.delay_separated = delay_separated
        
        return None
    
    def __set_regament_max(self):
        if self.flag_separated_is_detected == False:
            regamentLengthMax_Delay, regamentLengthMax = math.nan, math.nan
        else:
            #リガメント長格納用リスト
            regamentLengthList = [[max([dat.get_regament_length() for dat in data[IDX_CNT]]), data[IDX_DELAY]] for data in\
                                  self.analysisResults if data[IDX_DELAY] >= self.delay_separated]
            #リガメント長さ順で昇順ソート
            regamentLengthList.sort(key=lambda rst:rst[0])             
            #最大リガメント長さ、およびそのディレイを取得
            regamentLengthMax = regamentLengthList[-1][0]
            regamentLengthMax_Delay = regamentLengthList[-1][1]
        
        self.delay_max_regament_detected = regamentLengthMax_Delay
        self.max_regament_length = regamentLengthMax     
        
        return None
    
    def __set_arc_solidity(self):
        '''
        
        '''
        if self.__DEBUG:
            calculation_log('arc_solidity method was called.') 
        rsts = [sorted(data[IDX_CNT], key=lambda rs: rs.area, reverse=True) for data in self.analysisResults]
        arc_solidity = max([(dat[0].convex_hull_contour_arclength / dat[0].arclength) for dat in rsts])
        self.arc_solidity = arc_solidity
        
        return None
    
    def __set_volume(self):
        '''
        
        '''
        if self.__DEBUG:
            calculation_log('volume method was called.')         
        lstReached = list(filter(lambda dat: len([d for d in dat[IDX_CNT] if d.main_Y == d.imgYMax]) != 0, self.analysisResults))
        if len(lstReached) == 0:
            delay_upper_limit = 1000
            reaching_delay = delay_upper_limit
        else:
            reaching_delay = list(filter(lambda dat: len([d for d in dat[IDX_CNT] if d.main_Y == d.imgYMax]) != 0, self.analysisResults))[IDX_DELAY][0]
        lst = [dat for dat in self.analysisResults if (dat[IDX_DELAY] >= self.delay_separated) and (dat[IDX_DELAY] < reaching_delay)]
        if len(lst) == 0:
            volumeAve = -1
            volumeStdDiv = -1
        volumeList = [sum([dat.volume for dat in data[IDX_CNT][1:]]) for data in lst if len(data[IDX_CNT]) > 1]
        if len(volumeList) == 0:
            volumeAve = 0
            volumeStdDiv = 0
        else:
            volumeAve = sum(volumeList) / len(volumeList)
            volumeStdDiv = sum([math.sqrt((vol - volumeAve)**2 / len(volumeList)) for vol in volumeList])        
        self.volume_ave = volumeAve
        self.volume_std_div = volumeStdDiv
        
        return None
    
    def __set_freq_Y(self):
        if self.__DEBUG:
            calculation_log('freq_Y method was called.')            
        rsts = [sorted(data[IDX_CNT], key=lambda rs: rs.area, reverse=True) for data in self.analysisResults]
        cnt_target = list(filter(lambda dat: (dat[0].convex_hull_contour_area / dat[0].area) == self.solidity , rsts))[IDX_DELAY][0]
        self.freq_Y = cnt_target.freq_Y
        self.freq_Y_cnt = cnt_target.freq_num
        
        return None
    
    def __set_num_initial_contour(self):
        delay_sorted_rsts = sorted(self.analysisResults, key = lambda rs: rs[IDX_DELAY])
        retNum_list = [len(rst[IDX_CNT]) for rst in delay_sorted_rsts if rst[IDX_DELAY] < self.delay_separated]
        self.num_contours_at_first = retNum_list

        return None
    
    def __set_magnitude_of_doubletDroplet(self):
        '''
        二重吐出度評価用関数
        液滴分離検出後のノズル面積 - 1枚目のノズル面積の最大値
        
        Parameters
        ----------        
        area_mirgin_detectSeparation : float
            分離検出面積閾値[pix]、初期値2000
        arc_length_mirgin_detectSeparation ：float
            分離検出輪郭長閾値[pix]、初期値10
        
        Return
        ----------
        maximum_area_diff : float
             最大面積差分[pix]
        '''
        
        maximum_area_diff = max([data[1][0].area for data in self.analysisResults if data[0]>self.delay_separated]) - self.analysisResults[0][1][0].area
        self.magnitude_of_doubletdroplet = maximum_area_diff
        return None
    
    def __get_CntDist_is_closer(self, cntResult1, cntResult2, thresh):
        '''
        輪郭類似度計算関数
        輪郭類似度を、以下の式にて計算
            dMainXY ： 2つのmain_X、main_Y座標距離[pix]
            dSatelliteXY ： 2つのsatellite_X、satellite_Y座標距離[pix]
            dCenterXY : 2つのcenter_X、center_Y座標距離[pix]
            dArea : 2つの内包面積差の絶対値差[pix]
            dArcLength : 2つの輪郭長さの絶対値差[pix]
        これらの和がthresh以下であれば、2つの輪郭は同じノイズを拾っていると見做す。すなわち、
        diff_cnt_dist = dMainXY + dSatelliteXY + dCentrXY + dArea + dArclength < thresh
        にて判定
        
        Parameters
        ----------        
        cntResult1, 2 : AnalysisResultクラス
            輪郭類似度判定をする輪郭抽出結果
        thresh : float
            類似判定閾値
       
        Return
        ----------        
        flag_dcntResults_is_closer : bool
            類似判定結果
                                
        '''
        
        dMainXY = math.sqrt((cntResult1.main_X - cntResult2.main_X)**2 +\
                            (cntResult1.main_Y - cntResult2.main_Y)**2)
        dSatelliteXY = math.sqrt((cntResult1.satellite_X - cntResult2.satellite_X)**2 +\
                                 (cntResult1.satellite_Y - cntResult2.satellite_Y)**2)
        dCenterXY = math.sqrt((cntResult1.center_X - cntResult2.center_X)**2 +\
                              (cntResult1.center_Y - cntResult2.center_Y)**2)
        dArea = math.sqrt((cntResult1.area - cntResult2.area)**2)
        dArcLength = math.sqrt((cntResult1.arclength - cntResult2.arclength)**2)
        flag_dcntResults_is_closer = (dMainXY + dSatelliteXY + dCenterXY + dArea + dArcLength < thresh)
        return flag_dcntResults_is_closer
    
    def __remove_noise(self):
        '''
        画像ノイズ除去関数
        輪郭画像から固定位置に決まって出現する小さい輪郭（＝カメラに映ったごみ）を削除。
        ノズルを除く各輪郭に対して、輪郭近似度を定義し計算。
        輪郭近似度がthresh以下のものに対して、削除判定。
        削除判定時、面積がself.noise_remove_area_thresh以上のものは削除しない。
        コンストラクタより呼び出し。
        
        Parameters
        ----------        
        なし
        
        Return
        ----------
        なし

        '''
        
        if self.__DEBUG:
            calculation_log('noise_remove method is called')
        removeIndexList = []
        flagAllRemoveIsSucceed = True

        #以下、削除先データの削除。
        #i,jのアサインが変わるのでこの段階では削除元のデータは削除しない。
        #検索順はi, j昇順なので、削除元のデータのindexは削除後に再度別の輪郭の削除が生じても変化はしない。
        for i in range(len(self.analysisResults)):           
            for j in range(1, len(self.analysisResults[i][IDX_CNT])):
                flagDelDone = False

                for k in range(i + 1, len(self.analysisResults)):                    
                    for l in range(1, len(self.analysisResults[k][IDX_CNT])):
                        if self.__get_CntDist_is_closer(self.analysisResults[i][IDX_CNT][j],
                                                      self.analysisResults[k][IDX_CNT][l],
                                                      self.__noise_remove_topological_dist_thresh):
                            area, regLength = self.analysisResults[k][IDX_CNT][l].area, self.analysisResults[k][IDX_CNT][l].get_regament_length()
                            if area < self.__noise_remove_area_thresh:
                                if self.__DEBUG:
                                    calculation_log('contour with X,Y = {}, {} and area = {} was deleted as noise'.format(
                                        self.analysisResults[k][IDX_CNT][l].main_X,
                                        self.analysisResults[k][IDX_CNT][l].main_Y,
                                        self.analysisResults[k][IDX_CNT][l].area)
                                                   )
                                del self.analysisResults[k][IDX_CNT][l]
                                flagDelDone = True
                            break
                            
                if flagDelDone == True:
                    removeIndexList.append([i, j, self.analysisResults[i][IDX_CNT][j]])

        #以下、削除元データの削除。     
        flagAllRemoveIsSucceed = False
        for removeElem in removeIndexList:
            testList = [cnt for cnt in self.analysisResults[removeElem[0]][IDX_CNT] if not removeElem[2].is_equal(cnt)]
            if len(testList) != 0:
                self.analysisResults[removeElem[0]][IDX_CNT] = testList
                flagAllRemoveIsSucceed = True
                
        return flagAllRemoveIsSucceed
    
    def Check_exotic_droplet_exists(self, tracking_Results, pix_mirgin):
        '''
        エキゾチック輪郭（逸脱輪郭）検出関数
        
        Parameters
        ----------        
        tracking_Results : Tracking_Resultsクラス
            追尾結果クラス
        pix_mirgin : int
            逸脱判定時画像上マージン値[pix]、必ず正の値をとる。
        
        Return
        ----------
        flag_exotic_droplet_exists : bool
            逸脱輪郭検出有無、Trueで逸脱輪郭検出

        
        '''
        #逸脱評価輪郭リストの取得
        eval_cnts_list = [[cnts[IDX_DELAY], sorted(cnts[IDX_CNT], key = lambda cnt:cnt.area, reverse = True)] for cnts in self.analysisResults]
        if self.__DEBUG:
            calculation_log('eval cnts is called.')
        #追尾結果より、メイン-サテライト液滴トラッキング近似結果の取得
        main_slope_params = tracking_Results.get_Main_vector_slope_intercept()
        sat_slope_params = tracking_Results.get_Satellite_vector_slope_intercept()
        if self.__DEBUG:
            calculation_log('slopes were calculated. main : {}, sat: {}'.format(main_slope_params, sat_slope_params))
        #逸脱輪郭検出フラグの宣言
        flag_exotic_droplet_exists = False
        for cnt_list in eval_cnts_list:
            if self.__DEBUG:
                calculation_log('cnt_list with delay {} is called'.format(cnt_list[IDX_DELAY]))
            if len(cnt_list[IDX_CNT]) == 1:
                if self.__DEBUG:
                    calculation_log('length is 1.')
                continue
            #通常輪郭存在領域の指定
            #max_x:X座標右端、サテライトかメイン液滴x座標 + mirgin値の最大値
            max_x = max([main_slope_params[0] * cnt_list[IDX_DELAY] + main_slope_params[1] + pix_mirgin,\
                         sat_slope_params[0] * cnt_list[IDX_DELAY] + sat_slope_params[1] + pix_mirgin])
            #min_x:X座標左端、サテライトかメイン液滴x座標 - mirgin値の最大値
            min_x = min([main_slope_params[0] * cnt_list[IDX_DELAY] + main_slope_params[1] - pix_mirgin,\
                         sat_slope_params[0] * cnt_list[IDX_DELAY] + sat_slope_params[1] - pix_mirgin])
            #max_y:Y座標下端、メイン液滴y座標 + mirgin値、または画像下端Y座標の最大値
            max_y = min([main_slope_params[2] * cnt_list[IDX_DELAY] + main_slope_params[3] + pix_mirgin,\
                         cnt_list[IDX_CNT][0].imgYMax])
            #max_y:Y座標上端、サテライト液滴y座標 + mirgin値、または画像上端Y座標の最小値
            min_y = max([sat_slope_params[2] * cnt_list[IDX_DELAY] + sat_slope_params[3] - pix_mirgin,\
                         0])           
            
            #吐出輪郭の検証
            #ノズル輪郭は除く（ゆえにレンジは1からスタート）
            for i in range(1, len(cnt_list[IDX_CNT])):
                cnt = cnt_list[IDX_CNT][i]
                if self.__DEBUG:
                    calculation_log('{} th cnt with delay at {} is called'.format(i, cnt_list[IDX_DELAY]))
                #各輪郭の重心座標が上記4点で定義される矩形範囲に入るか否かを判定する。
                flag_exotic_droplet_exists = (cnt.center_X < min_x) or (cnt.center_X > max_x) or (cnt.center_Y < min_y) or (cnt.center_Y > max_y)
                if flag_exotic_droplet_exists:
                    if self.__DEBUG:
                        calculation_log('exotic droplet occured at {} us, X : {}, Y : {} at min_x : {}, max_x : {}, min_y : {}, max_y : {}'.format(
                        cnt_list[IDX_DELAY], cnt.center_X, cnt.center_Y, min_x, max_x, min_y, max_y))
                    break
                else:
                    if self.__DEBUG:
                        calculation_log('cnt at delay{} does not contain exotic droplets'.format(cnt_list[IDX_DELAY]))
            #逸脱輪郭を発見した場合は検証打ち切り
            if flag_exotic_droplet_exists:
                break
        
        return flag_exotic_droplet_exists