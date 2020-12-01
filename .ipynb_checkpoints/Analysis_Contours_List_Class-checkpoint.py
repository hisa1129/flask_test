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
        if DEBUG:
            calculation_log('set params to class_field parameters.')
        analysis_results_list = [rsts for rsts in analysis_results_list if len(rsts.contours) != 0]
        #ディレイ時間にて昇順ソートしanalysisResultsに格納
        analysis_results_list.sort(key=lambda rst: rst.delay)
        self.analysisResults = analysis_results_list

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
        self.__set_magnitude_of_doublet_droplet()

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
        solidity_list = [cnts.solidity_of_nozzle for cnts in self.analysisResults]
        #クラスプロパティにセット
        self.solidity = min(solidity_list)
           
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
            evaluation_delay = self.analysisResults[i].delay
            before_convex_hull_area = self.analysisResults[i-1].convex_hull_area_of_nozzle
            after_convex_hull_area = self.analysisResults[i].convex_hull_area_of_nozzle
            flag_detection = after_convex_hull_area - self.__area_mirgin_detect_faced > before_convex_hull_area
            if self.__DEBUG:
                calculation_log('delay : {}, evaluation_area : {} evaluation_area_before : {}'.format(
                    evaluation_delay,
                    after_convex_hull_area,
                    before_convex_hull_area)
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
        seeking_results_list = [data for data in self.analysisResults if data.delay >= self.delay_faced]
        solidity_base = self.solidity
        for i in range(1, len(seeking_results_list)):
            eval_delay = seeking_results_list[i].delay
            flag_convexhull_contour_area = (seeking_results_list[i].convex_hull_area_of_nozzle +\
                                            self.__area_mirgin_detect_separation < seeking_results_list[i-1].convex_hull_area_of_nozzle)
            flag_convexhull_contour_arclength = (seeking_results_list[i].arclength_of_nozzle + self.__arc_length_mirgin_detect_separation <\
                                                 seeking_results_list[i-1].arclength_of_nozzle)
            solidity_at_seeking_result = seeking_results_list[i].solidity_of_nozzle
            eval_ratio = solidity_at_seeking_result / solidity_base
            flag_solidity_is_plausible =  eval_ratio < self.__solidity_mirgin_detect_separation
            flag_length_of_contours = (len(seeking_results_list[i].contours) > 1)
            if self.__DEBUG:
                calculation_log('delay at {}, solidity is {}, eval ratio is {}, and flag is {}'.format(
                    eval_delay,
                    solidity_at_seeking_result,
                    eval_ratio,
                    flag_solidity_is_plausible)
                               )  
            
            if flag_convexhull_contour_area and flag_convexhull_contour_arclength and flag_solidity_is_plausible and flag_length_of_contours:
                delay_separated = eval_delay
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
            regamentLengthList = [[data.max_reg_length_in_delay, data.delay] for data in self.analysisResults if data.delay >= self.delay_separated]
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
        rsts = [cnts.convex_hull_arclength_of_nozzle / cnts.arclength_of_nozzle for cnts in self.analysisResults]
        arc_solidity = max(rsts)
        self.arc_solidity = arc_solidity
               
        return None
    
    def __set_volume(self):
        '''
        
        '''
        if self.__DEBUG:
            calculation_log('volume method was called.')         
        lstReached = list(filter(lambda dat: len([d for d in dat.contours if d.main_Y == d.imgYMax]) != 0, self.analysisResults))
        if len(lstReached) == 0:
            delay_upper_limit = 1000
            reaching_delay = delay_upper_limit
        else:
            reaching_delay = list(filter(lambda dat: len([d for d in dat.contours if d.main_Y == d.imgYMax]) != 0, self.analysisResults))[0].delay
        lst = [dat for dat in self.analysisResults if (dat.delay >= self.delay_separated) and (dat.delay < reaching_delay)]
        if len(lst) == 0:
            volumeAve = -1
            volumeStdDiv = -1
        volumeList = [data.volume_without_nozzle for data in lst if len(data.contours) > 1]
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
        target_cnt = [cnts for cnts in self.analysisResults if cnts.solidity_of_nozzle == self.solidity][0]        
        self.freq_Y = target_cnt.freq_Y_of_Nozzle
        self.freq_Y_cnt = target_cnt.num_freq_Y_of_Nozzle
        
        return None
    
    def __set_num_initial_contour(self):
        if self.__DEBUG:
            calculation_log('num_ave_contour_method was called.')            
        if self.flag_separated_is_detected:
            retNum_list = [len(rst.contours) for rst in self.analysisResults if rst.delay < self.delay_separated]
        else:
            retNum_list = [len(rst.contours) for rst in self.analysisResults]            
        self.num_contours_at_first = retNum_list

        return None
       
    def __set_magnitude_of_doublet_droplet(self):      
        '''
        二重吐出度計算関数
        
        '''
        if self.__DEBUG:
            calculation_log('detect magnitude of doublet_droplet method was called.')
        if self.flag_separated_is_detected:
            seeking_results_list = [cnts.solidity_of_nozzle for cnts in self.analysisResults if cnts.delay >= self.delay_separated]
            if len(seeking_results_list) == 1:
                self.magnitude_of_doublet_droplet = -1
            else:
                diff_solidity_after_separation = max(seeking_results_list) - min(seeking_results_list)     
                self.magnitude_of_doublet_droplet = diff_solidity_after_separation       
        else:
            self.magnitude_of_doublet_droplet = -1
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
#            print('{}'.format(i))
            for j in range(1, len(self.analysisResults[i].contours)):
#                print('{}'.format(j))
                flagDelDone = False
                for k in range(i + 1, len(self.analysisResults)):
#                    print('{}'.format(k))
                    for l in range(1, len(self.analysisResults[k].contours)):
#                        print('{}'.format(l))
                        if self.__get_CntDist_is_closer(self.analysisResults[i].contours[j],
                                                      self.analysisResults[k].contours[l],
                                                      self.__noise_remove_topological_dist_thresh):
                            area = self.analysisResults[k].contours[l].area
                            if area < self.__noise_remove_area_thresh:
#                                print('{}, {}, will be deled'.format(k, l))
                                if self.__DEBUG:
                                    calculation_log('contour with X,Y = {}, {} and area = {} was deleted as noise'.format(
                                        self.analysisResults[k].contours[l].main_X,
                                        self.analysisResults[k].contours[l].main_Y,
                                        self.analysisResults[k].contours[l].area)
                                                   )
                                lists = self.analysisResults[k].contours.pop(l)
 #                               print('{}, {}, del done'.format(k, l))
                                flagDelDone = True
                                break
                            
                if flagDelDone == True:
                    removeIndexList.append([i, j, self.analysisResults[i].contours[j]])

#        print('first_remove was done')
        #以下、削除元データの削除。     
        flagAllRemoveIsSucceed = False
        for removeElem in removeIndexList:
            testList = [cnt for cnt in self.analysisResults[removeElem[0]].contours if not removeElem[2].is_equal(cnt)]
            if len(testList) != 0:
                self.analysisResults[removeElem[0]].contours = testList
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
        if self.__DEBUG:
            calculation_log('eval cnts is called.')
        #追尾結果より、メイン-サテライト液滴トラッキング近似結果の取得
        main_slope_params = tracking_Results.get_Main_vector_slope_intercept()
        sat_slope_params = tracking_Results.get_Satellite_vector_slope_intercept()
        if self.__DEBUG:
            calculation_log('slopes were calculated. main : {}, sat: {}'.format(main_slope_params, sat_slope_params))
        #逸脱輪郭検出フラグの宣言
        flag_exotic_droplet_exists = False
        cnt_exotic_areas = []
        for cnt_list in self.analysisResults:
            flag_exotic_droplet_detected = False
            if self.__DEBUG:
                calculation_log('cnt_list with delay {} is called'.format(cnt_list.delay))
            if len(cnt_list.contours) == 1:
                if self.__DEBUG:
                    calculation_log('length is 1.')
                continue
            #通常輪郭存在領域の指定
            #max_x:X座標右端、サテライトかメイン液滴x座標 + mirgin値の最大値
            max_x = max([main_slope_params[0] * cnt_list.delay + main_slope_params[1] + pix_mirgin,\
                         sat_slope_params[0] * cnt_list.delay + sat_slope_params[1] + pix_mirgin])
            #min_x:X座標左端、サテライトかメイン液滴x座標 - mirgin値の最大値
            min_x = min([main_slope_params[0] * cnt_list.delay + main_slope_params[1] - pix_mirgin,\
                         sat_slope_params[0] * cnt_list.delay + sat_slope_params[1] - pix_mirgin])
            #max_y:Y座標下端、メイン液滴y座標 + mirgin値、または画像下端Y座標の最大値
            max_y = min([main_slope_params[2] * cnt_list.delay + main_slope_params[3] + pix_mirgin,\
                         cnt_list.contours[0].imgYMax])
            #max_y:Y座標上端、サテライト液滴y座標 + mirgin値、または画像上端Y座標の最小値
            min_y = max([sat_slope_params[2] * cnt_list.delay + sat_slope_params[3] - pix_mirgin,\
                         0])           
            
            #吐出輪郭の検証
            #ノズル輪郭は除く（ゆえにレンジは1からスタート）
            for i in range(1, len(cnt_list.contours)):
                cnt = cnt_list.contours[i]
                if self.__DEBUG:
                    calculation_log('{} th cnt with delay at {} is called'.format(i, cnt_list.delay))
                #各輪郭の重心座標が上記4点で定義される矩形範囲に入るか否かを判定する。
                flag_exotic_droplet_detected = (cnt.center_X < min_x) or (cnt.center_X > max_x) or (cnt.center_Y < min_y) or (cnt.center_Y > max_y)
                if flag_exotic_droplet_detected:
                    if self.__DEBUG:
                        calculation_log('exotic droplet occured at {} us, X : {}, Y : {} at min_x : {}, max_x : {}, min_y : {}, max_y : {}'.format(
                        cnt_list.delay, cnt.center_X, cnt.center_Y, min_x, max_x, min_y, max_y))
                        flag_exotic_droplet_exists = True
                        cnt_exotic_areas.append(cnt.area)
                else:
                    if self.__DEBUG:
                        calculation_log('cnt at delay{} does not contain exotic droplets'.format(cnt_list.delay))
        ret_max_areas = max(cnt_exotic_areas) if len(cnt_exotic_areas) != 0 else 0
        
        return flag_exotic_droplet_exists, ret_max_areas
    
    def modify_faced_delay_and_freq_Y(self):
        if not self.flag_faced_is_detected:
            return
        print('modify_faced_delay_was_called, faced_delay : {}, freq_Y : {}'.format(self.delay_faced, self.freq_Y))
        index_faced_delay = len([contours for contours in self.analysisResults if contours.delay < self.delay_faced])
        if index_faced_delay == 0:
            return None
        if len(self.analysisResults) - 1 < index_faced_delay:
            return None
        delta_S1 = self.analysisResults[index_faced_delay].convex_hull_area_of_nozzle - self.analysisResults[index_faced_delay - 1].convex_hull_area_of_nozzle
        delta_S2 = self.analysisResults[index_faced_delay + 1].convex_hull_area_of_nozzle - self.analysisResults[index_faced_delay].convex_hull_area_of_nozzle
        delay_1 = self.analysisResults[index_faced_delay].delay
        delay_2 = self.analysisResults[index_faced_delay + 1].delay
        delta_delay = delay_2 - delay_1
        delay_faced_modified = self.analysisResults[index_faced_delay].delay - delta_delay * delta_S1 / delta_S2
        print("estimated_delay_faced :{}, delay_limit : {}".format(
            delay_faced_modified, self.analysisResults[index_faced_delay - 1].delay))
        if delay_faced_modified > self.analysisResults[index_faced_delay - 1].delay:
            self.delay_faced = delay_faced_modified
        freq_Y_modified = (self.analysisResults[index_faced_delay].main_Y_of_nozzle * (delay_2 - delay_faced_modified) - \
                       self.analysisResults[index_faced_delay + 1].main_Y_of_nozzle * (delay_1 - delay_faced_modified)) / delta_delay
        print('estimated_freq_Y : {}'.format(freq_Y_modified))
        if abs(freq_Y_modified - self.freq_Y) < self.analysisResults[index_faced_delay].contours[0].imgYMax * 0.05:
            self.freq_Y = freq_Y_modified
        print('modify_faced_delay_was_done, faced_delay : {}, freq_Y : {}'.format(self.delay_faced, self.freq_Y))
        return None
    
    def modify_separated_delay(self, tracking_Results):
        if not self.flag_separated_is_detected:
            return None
        print('modify_separated_delay_was_called, delay_separated : {}'.format(self.delay_separated))        
        index_separated = len([contours for contours in self.analysisResults if contours.delay < self.delay_separated])
        eval_tracking_rsts = [tr for tr in tracking_Results.results if tr.delay >= self.delay_separated]
        if len(self.analysisResults) - 1 < index_separated:
            return None
        delay_1 = self.analysisResults[index_separated].delay
        delay_2 = self.analysisResults[index_separated + 1].delay
        delta_delay = delay_2 - delay_1
        delta_Y2 = eval_tracking_rsts[1].satellite_Y - self.freq_Y
        delta_Y1 = eval_tracking_rsts[0].satellite_Y - self.freq_Y
        delay_separated_modified = (delay_1 * delta_Y2 - delay_2 * delta_Y1)/(eval_tracking_rsts[1].satellite_Y - eval_tracking_rsts[0].satellite_Y )
        print("estimated_delay_separated :{}, delay_limit : {}".format(
            delay_separated_modified, self.analysisResults[index_separated - 1].delay))
        if delay_separated_modified > self.analysisResults[index_separated - 1].delay:
            self.delay_separated = delay_separated_modified
        print('modify_separated_delay_was_done, delay_separated : {}'.format(self.delay_separated))        
        return None