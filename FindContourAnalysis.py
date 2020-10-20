#numpyのインポート
import numpy as np
#opencvのインポート
import cv2
#python標準のインポート
import os
import glob
import sys
from itertools import groupby
import math
from CalculationLog import calculation_log

#analysisResults用インデックス、配列2番目にて指定。
IDX_DELAY = 0
IDX_CNT = 1

#輪郭データ格納numpyArray用インデックス、配列3番目で指定。
IDX_X = 0
IDX_Y = 1


#解析結果格納クラス
class Analysis_Result:
    '''
    輪郭解析結果格納クラス
    
    Attributes
    ----------    
    delay : float
        ディレイ時間[us]
    main_X : int
        輪郭下端X座標[pix]       
    main_Y : int
        輪郭下端Y座標[pix]
    satellite_X : int
        輪郭上端X座標[pix]
    satellite_Y : int
        輪郭上端Y座標[pix]
    arclength : float
        輪郭周囲長[pix]
    area : float
        輪郭内包面積[pix]
    center_X : int
        輪郭重心X座標[pix]
    center_Y : int
        輪郭重心Y座標[pix]
    convex_hull_contour_area : float
        凸包輪郭内包面積[pix]
    convex_hull_contour_arclength : float
        凸包輪郭周囲長[pix]
    imgYMax : int
        画像Y座標最大値[pix]
    volume : float
        輪郭回転体積[pix^3]
    freq_num : int
        最頻出Y座標出現数[cnt]（0を除く）
    freq_Y : int
        最頻出Y座標[pix]
    '''
    
    def __init__(self, delay, main_X, main_Y, satellite_X, satellite_Y, arclength, area, center_X, center_Y, \
                 convex_hull_contour_area, convex_hull_contour_arclength, imgYMax, volume,\
                 freq_num, freq_Y, DEBUG = False):
        '''
        コンストラクタ
        各フィールドへの値の格納
        
        Parameters
        ----------  
        delay : float
            ディレイ時間[us]
        main_X : int
            輪郭下端X座標[pix]       
        main_Y : int
            輪郭下端Y座標[pix]
        satellite_X : int
            輪郭上端X座標[pix]
        satellite_Y : int
            輪郭上端Y座標[pix]
        arclength : float
            輪郭周囲長[pix]
        area : float
            輪郭内包面積[pix]
        center_X : int
            輪郭重心X座標[pix]
        center_Y : int
            輪郭重心Y座標[pix]
        convex_hull_contour_area : float
            凸包輪郭内包面積[pix]
        convex_hull_contour_arclength : float
            凸包輪郭周囲長[pix]
        imgYMax : int
            画像Y座標最大値[pix]
        volume : float
            輪郭回転体積[pix^3]
        freq_num : int
            最頻出Y座標出現数[cnt]（0を除く）
        freq_Y : int
            最頻出Y座標[pix]
        '''
        
        self.delay = delay
        self.main_X = main_X
        self.main_Y = main_Y
        self.satellite_X = satellite_X
        self.satellite_Y = satellite_Y
        self.arclength = arclength
        self.area = area
        self.center_X = center_X
        self.center_Y = center_Y
        self.convex_hull_contour_area = convex_hull_contour_area
        self.convex_hull_contour_arclength = convex_hull_contour_arclength
        self.imgYMax = imgYMax       
        self.volume = volume
        self.freq_num = freq_num
        self.freq_Y = freq_Y
        self.DEBUG = DEBUG
        
    def get_regament_length(self):
        '''
        輪郭リガメント長さ計算関数
        
        Parameters
        ----------
        なし
        
        Return
        ----------  
        regament_length : float
            リガメント長さ[pix]
        '''
        
        #メイン液滴座標とサテライト液滴座標の距離をリガメント長と定義し計算
        regament_length = math.sqrt((self.main_X - self.satellite_X)**2 + (self.main_Y - self.satellite_Y)**2)
        return regament_length
    
    def is_equal(self, cnt):
        '''
        輪郭一致判定関数
        
        Parameters
        ----------
        cnt: Analysis_Result
            比較対象輪郭
            
　      Return
        ----------  
        is_equal : bool
            同じ値が格納されているか。同じ値ならばTrue
        
        '''
        
        flag_delay = self.delay == cnt.delay
        flag_mainX = self.main_X == cnt.main_X
        flag_mainY = self.main_Y == cnt.main_Y
        flag_satelliteX = self.satellite_X == cnt.satellite_X
        flag_satelliteY = self.satellite_Y == cnt.satellite_Y
        flag_arclength = self.arclength == cnt.arclength
        flag_area = self.area == cnt.area
        flag_centerX = self.center_X == cnt.center_X
        flag_centerY = self.center_Y == cnt.center_Y
        flag_convHullArea = self.convex_hull_contour_area == cnt.convex_hull_contour_area
        flag_convHullArc = self.convex_hull_contour_arclength == cnt.convex_hull_contour_arclength
        flag_imgMax = self.imgYMax == cnt.imgYMax
        flag_volume = self.volume == cnt.volume
        flag_freqYNum = self.freq_num == cnt.freq_num
        flag_freqY = self.freq_Y == cnt.freq_Y
        
        return (flag_delay and flag_mainX and flag_mainY and flag_satelliteX and flag_satelliteY and\
                flag_arclength and flag_area and flag_centerX and flag_centerY and flag_convHullArea and\
                flag_convHullArc and flag_imgMax and flag_volume and flag_freqYNum and flag_freqY)
        

#解析結果群格納クラス
class Analysis_Results_List:
    '''
    Attributes
    ----------
    analysisResults : [delay, [Analysis_Result]] 
        解析結果群
    '''
    
    def __init__(self, analysisResultsList, DEBUG):
        '''
        コンストラクタ
        単純な輪郭データ群をディレイ時間でgroupByの後にリストとして格納
        
        
        Parameters
        ----------
        analysisResultsList : [Analysis_Result]
            輪郭解析結果群
        
        '''
        
        #ディレイでソート
        analysisResultsList.sort(key=lambda rst: rst.delay)
        #結果格納リスト
        groupResults = []
        #グループ化
        for delay_key, contours_group in groupby(analysisResultsList, key=lambda rst:rst.delay):
            listGroup = list(contours_group)
            if len(listGroup) > 1:
                #面積にて降順ソート
                listGroup.sort(key=lambda rst:rst.area, reverse=True)
            #ディレイタイムでGroupBy、groupResultsを生成。
            groupResults.append([delay_key, listGroup])
            if DEBUG:
                calculation_log('delay = {}, and contour count = {}'.format(delay_key, len(listGroup)))
        #結果の格納
        self.analysisResults = groupResults
        self.DEBUG = DEBUG
    
    #液滴分離検出関数
    def get_separated_delay(self, area_mirgin_detectSeparation = 2000, arc_length_mirgin_detectSeparation = 10, faced_delay = 150):
        '''
        液滴分離を検出する。
        画像を送っていき、最大面積輪郭（ノズル輪郭）のconvex_hull_area + area_migrin_detectSeparation値が
        1つ前の画像より小さくなっていれば、そこで液滴が分離していると見做す。
        
        Parameters
        ----------
        area_migrin_detectSeparation : int
            検出面積マージン値[pix]、初期値2000
        arc_length_mirgin_detectSeparation ：int
            検出輪郭値[pix]、初期値10
        faced_delay : float
            液滴検出開始ディレイ時間[us]、初期値150
        
        Return
         ----------
         [flag_separated_is_detected, delay_separated]
         
            flag_separated_is_detected : bool
                分離検出の可否
            delay_separated : float 
                分離検出ディレイ時間[us]
        '''
        
        delay_separated = 0 
        flag_separated_is_detected = False
        seeking_results_list = [data for data in self.analysisResults if data[0] > faced_delay]
        for i in range(1, len(seeking_results_list)):
            flag_convexhull_contour_area = (seeking_results_list[i][1][0].convex_hull_contour_area +\
                                            area_mirgin_detectSeparation < seeking_results_list[i-1][1][0].convex_hull_contour_area)
            flag_convexhull_contour_arclength = (seeking_results_list[i][1][0].arclength + arc_length_mirgin_detectSeparation <\
                                                 seeking_results_list[i-1][1][0].arclength)
            if flag_convexhull_contour_area and flag_convexhull_contour_arclength:
                delay_separated = seeking_results_list[i][0]
                flag_separated_is_detected = True
                break
        return flag_separated_is_detected, delay_separated

    #吐出開始検出関数
    def get_dropletFaced_delay(self, area_mirgin_detectSeparation = 1000):
        '''
        液滴検出開始検知関数。
        画像を送っていき、最大面積輪郭（ノズル輪郭）のconvex_hull_area - area_migrin_detectSeparation値が
        1つ前の画像より大きくなっていれば、そこで液滴が分離していると見做す。

        
        Parameters
        ----------
        area_migrin_detectSeparation : int
            検出面積マージン値[pix]、初期値1000
        
        Return
        ----------
        [flag_faced_is_detected, delay_faced]     
        
            flag_faced_is_detected : bool
                吐出開始検出の可否
            delay_faced : float 
                吐出開始検出ディレイ時間[us]
        '''
        
        delay_faced = 0
        flag_faced_is_detected = False
        for i in range(1, len(self.analysisResults)):
            if self.analysisResults[i][1][0].convex_hull_contour_area - area_mirgin_detectSeparation > \
            self.analysisResults[i-1][1][0].convex_hull_contour_area:
                delay_faced = self.analysisResults[i][0]
                flag_faced_is_detected = True
                break
        return flag_faced_is_detected, delay_faced
    
    def is_needed_wiping(self, solidity = 1.028, arc_lengh_to_convexhull_arc_length_ratio = 0.978):
        '''
        ワイピング必要性検出関数、Trueで要ワイピング

        Parameters
        ----------        
        solidity : float
            凸包面積 / 実面積比の閾値[U]、初期値1.028
        arc_lengh_to_convexhull_arc_length_ratio ：float
            凸包周囲長/実周囲長比の閾値、初期値0.978
        
        Return
        ----------
        flag_is_needed_wiping : bool
            ワイピング必要性
        '''
        
        solidity_eval = self.analysisResults[0][1][0].convex_hull_contour_area / self.analysisResults[0][1][0].area
        arc_length_ratio_eval = self.analysisResults[0][1][0].convex_hull_contour_arclength / self.analysisResults[0][1][0].arclength
        flag_is_needed_wiping = solidity_eval > solidity
        if flag_is_needed_wiping:
            flag_is_needed_wiping = arc_length_ratio_eval < arc_lengh_to_convexhull_arc_length_ratio
        
        return flag_is_needed_wiping
    
    def get_magnitude_of_doubletDroplet(self, area_mirgin_detectSeparation = 2000,
                                        arc_length_mirgin_detectSeparation = 10):
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
        
        separated_delay = self.get_separated_delay(area_mirgin_detectSeparation, arc_length_mirgin_detectSeparation)[1]
        maximum_area_diff = max([data[1][0].area for data in self.analysisResults if data[0]>separated_delay]) - self.analysisResults[0][1][0].area
        return maximum_area_diff
    
    def get_maximum_regament_length(self, area_mirgin_detectSeparation = 2000,
                                    arc_lengh_mirgin_detectSeparation = 10):
        '''
        最大リガメント長取得関数
        
        Parameters
        ----------        
        area_mirgin_detectSeparation : float
            分離検出面積閾値[pix]、初期値2000
        arc_length_mirgin_detectSeparation ：float
            分離検出輪郭長閾値[pix]、初期値10
        
        Return
        ----------
        [regamentLengthMax, regamentLengthMax_Delay]
        
            regamentLengthMax : float
                最大リガメント長さ[pix]               
            regamentLengthMax_Delay : float
                最大リガメント長さディレイ[us]
        '''

        #液滴分離検出
        separated_detection = self.get_separated_delay(area_mirgin_detectSeparation, arc_lengh_mirgin_detectSeparation)
        if separated_detection[0] == False:
            retValue = [math.nan, math.nan]
        
        else:           
            #リガメント長格納用リスト
            regamentLengthList = [[max([dat.get_regament_length() for dat in data[1]]), data[0]] for data in\
                                  self.analysisResults if data[0] >= separated_detection[1]]
            
            #リガメント長さ順で昇順ソート
            regamentLengthList.sort(key=lambda rst:rst[0])
               
            #最大リガメント長さ、およびそのディレイを取得
            regamentLengthMax = regamentLengthList[-1][0]
            regamentLengthMax_Delay = regamentLengthList[-1][1]
            retValue =[regamentLengthMax, regamentLengthMax_Delay]
        
        return retValue
    
    def get_cva_a_ratio(self):
        '''
        ノズルのSolidity（ = Convex_hull_area / area値）の最小値取得関数
        
        Parameters
        ----------        
        なし
        
        Return
        ----------
        solidity : float
            最小solidity値[pix/pix]
        '''
        
        rsts = [[data[0], sorted(data[1], key=lambda rs: rs.area, reverse=True)] for data in self.analysisResults]
        rsts.sort(key=lambda rst:rst[1][0].convex_hull_contour_area / rst[1][0].area)
        solidity = rsts[0][1][0].convex_hull_contour_area / rsts[0][1][0].area
        return solidity


    def get_cval_al_ratio(self):
        '''
        ノズルのArcSolidity（ = Convex_hull_arc_length / arc_length値）の最大値取得関数
        
        Parameters
        ----------        
        なし
        
        Return
        ----------
        arc_solidity : float
            最小arc_solidity値[pix/pix]
        '''        
        
        rsts = [sorted(data[1], key=lambda rs: rs.area, reverse=True) for data in self.analysisResults]
        arc_solidity = max([(dat[0].convex_hull_contour_arclength / dat[0].arclength) for dat in rsts])
        return arc_solidity
    
    def get_volume(self, area_mirgin_detectSeparation, arclength_mirgin_detectSeparation):
        '''
        液滴体積取得関数
        ※現状詳細輪郭抽出ではないので、計算値の信頼度は低い。
        
        Parameters
        ----------        
        area_mirgin_detectSeparation : float
            液滴分離検出時の面積閾値[pix]
        arclength_mirgin_detectSEparation : float
            液滴分離検出時の輪郭長さ敷地[pix]
        
        Return
        ----------
        [volumeAve, volumeStdDiv]
            volumeAve : float
                検出体積の平均値[pix^3]
            volumeStdDiv : float
                検出体積の標準偏差値[pix^3]
        '''
        
        faced_delay = self.get_dropletFaced_delay(area_mirgin_detectSeparation)
        separated_delay = self.get_separated_delay(area_mirgin_detectSeparation, arclength_mirgin_detectSeparation,faced_delay[1])[1]
        lstReached = list(filter(lambda dat: len([d for d in dat[1] if d.main_Y == d.imgYMax]) != 0, self.analysisResults))
        if len(lstReached) == 0:
            delay_upper_limit = 1000
            reaching_delay = delay_upper_limit
        else:
            reaching_delay = list(filter(lambda dat: len([d for d in dat[1] if d.main_Y == d.imgYMax]) != 0, self.analysisResults))[0][0]
        lst = [dat for dat in self.analysisResults if (dat[0] >= separated_delay) and (dat[0] < reaching_delay)]
        if len(lst) == 0:
            return -1, -1
        
        volumeList = [sum([dat.volume for dat in data[1][1:]]) for data in lst if len(data[1]) > 1]
        if len(volumeList) == 0:
            volumeAve, volumeStdDev = 0,0
        else:
            volumeAve = sum(volumeList) / len(volumeList)
            volumeStdDev = sum([math.sqrt((vol - volumeAve)**2 / len(volumeList)) for vol in volumeList]) 
        
        return volumeAve, volumeStdDiv    
    
    def get_freq_YandNum(self):
        '''
        ノズル面Y座標と座標出現頻度取得関数
        
        
        '''
        
        rsts = [sorted(data[1], key=lambda rs: rs.area, reverse=True) for data in self.analysisResults]
        cnt_target = list(filter(lambda dat: dat[0].convex_hull_contour_area / dat[0].area == self.get_cva_a_ratio() , rsts))[0][0]
        return cnt_target.freq_Y, cnt_target.freq_num
    
    def get_NumContours_at_First(self):
        '''
        初期輪郭数抽出関数
        
        return
        ------------------------
        retNum : int
            ディレイ時間にて最初の写真での輪郭数。
        
        ------------------------
        
        '''
        delay_sorted_rsts = sorted(self.analysisResults, key = lambda rs: rs[0])
        retNum = len(delay_sorted_rsts[0][1])
        return retNum
    
    def get_CntDist_is_closer(self, cntResult1, cntResult2, thresh):
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
    
    def Remove_Noise(self, thresh=25, area_thresh = 40):
        '''
        画像ノイズ除去関数
        輪郭画像から固定位置に決まって出現する小さい輪郭（＝カメラに映ったごみ）を削除。
        ノズルを除く各輪郭に対して、輪郭近似度を定義し計算。
        輪郭近似度がthresh以下のものに対して、削除判定。
        削除判定時、面積がarea_thresh以上のものは削除しない。
        
        Parameters
        ----------        
        thresh : int
            距離判定敷居値[U]、初期値25
        area_thresh : int
            近似判定時の削除輪郭最大面積敷居値[pix]、これ以上面積が大きい時は削除しない。初期値40
        
        Return
        ----------
        なし

        '''
        
        removeIndexList = []
        flagAllRemoveIsSucceed = True

        #以下、削除先データの削除。
        #i,jのアサインが変わるのでこの段階では削除元のデータは削除しない。
        #検索順はi, j昇順なので、削除元のデータのindexは削除後に再度別の輪郭の削除が生じても変化はしない。
        for i in range(len(self.analysisResults)):           
            for j in range(1, len(self.analysisResults[i][1])):
                flagDelDone = False

                for k in range(i + 1, len(self.analysisResults)):                    
                    for l in range(1, len(self.analysisResults[k][1])):
                        if self.get_CntDist_is_closer(self.analysisResults[i][1][j], self.analysisResults[k][1][l], thresh):
                            area, regLength = self.analysisResults[k][1][l].area, self.analysisResults[k][1][l].get_regament_length()
                            if area < area_thresh:
                                if self.DEBUG:
                                    calculation_log('contour with X,Y = {}, {} and area = {} was deleted as noise'.format(
                                        self.analysisResults[k][1][l].main_X,
                                        self.analysisResults[k][1][l].main_Y,
                                        self.analysisResults[k][1][l].area)
                                                   )
                                del self.analysisResults[k][1][l]
                                flagDelDone = True
                            break
                            
                if flagDelDone == True:
                    removeIndexList.append([i, j, self.analysisResults[i][1][j]])

        #以下、削除元データの削除。     
        flagAllRemoveIsSucceed = False
        for removeElem in removeIndexList:
            testList = [cnt for cnt in self.analysisResults[removeElem[0]][1] if not removeElem[2].is_equal(cnt)]
            if len(testList) != 0:
                self.analysisResults[removeElem[0]][1] = testList
                flagAllRemoveIsSucceed = True
                
        return flagAllRemoveIsSucceed

#解析結果取得関数
def analyse_Image(delay, path, min_area_thresh, 
                  binarize_thresh, auto_binarize = True,
                  draw_contour = False,
                  draw_convexhull = False,
                  draw_coords = False,
                  exportImage = False,
                  mkdir=False,
                  flag_export_fillImg = False,
                  DEBUG = False):
    '''
    
    

    '''
    if DEBUG:
        calculation_log('import file is {} with the fill img flag is {}'.format(path, flag_export_fillImg))
    #BGR画像の読み込み
    img = cv2.imread(path)
    if DEBUG:
        calculation_log('image file {} was imported'.format(path))
    #画像のグレイスケール化
    im = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #二値化、オートバイナライズか否かで挙動違う
    ret, im_bin = cv2.threshold(
        im,
        binarize_thresh, 
        255, 
        (cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU) if auto_binarize else (cv2.THRESH_BINARY_INV))
    #輪郭抽出
    contours, hierarchy = cv2.findContours(im_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #閾値でフィルタ
    contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_thresh]
    
    #インデックス値宣言、輪郭X座標インデックス、Y座標インデックスを指定。
    indX, indY = 0, 1
    
    #以下、ノズル輪郭補正
    #ターゲットとなる輪郭を抽出（ノズル輪郭は必ず画像上端にあるため、輪郭のうち少なくとも1つはY = 0を含む）
    targetCnts = [cnt for cnt in contours if any([pt[0,indY] == 0 for pt in cnt])]
    
    if DEBUG:
        calculation_log('the length of contour with Y = 0 point is {}'.format(len(targetCnts)))
    #ターゲット輪郭が存在する場合
    #targetCntがただ1つ→それはノズルがただ1つのブロブとして輪郭検出されていることを示す。
    if len (targetCnts) == 1:
        #ターゲット輪郭内部のヴォイドを検出
        #Y = 0なる輪郭点を抽出
        ptZeroList = [Pt for Pt in targetCnts[0] if Pt[0,indY] == 0]
        #Y = 0なる輪郭点のうちの最大値と最小値を検出→ノズル両端の座標
        leftX, rightX = min([pt[0,indX] for pt in ptZeroList]), max([pt[0,indX] for pt in ptZeroList])
        #理想的な輪郭抽出が実行されている場合、ノズル両端座標間の輪郭は必ず直線であるため、cv2.CHAIN_APPROX_SIMPLEでの検出では
        #ノズル両端を結ぶ輪郭内部にY = 0となる別の点が含まれることは無い。逆に、そのような点が存在する場合はノズル輪郭内部にて
        #輪郭が分割されない程度のヴォイドが発生していることを示す。
        #以下はそのようなヴォイドの有無を抽出するコード、すなわち輪郭両端座標内部（両端座標を除く）にてY == 0なる輪郭を抽出している。
        ptZeroListInnerVoid = [Pt for Pt in targetCnts[0] if Pt[0][indY] == 0 and Pt[0][indX] > leftX and Pt[0][indX] < rightX]
        if DEBUG:
            calculation_log('length of voided contour at nozzle is {}'.format(len(ptZeroListInnerVoid)))
        #ヴォイドが存在する場合
        if len(ptZeroListInnerVoid) != 0:
            #ヴォイド構成点の最も左端の座標を取得
            inner_leftX = min([pt[0,indX] for pt in ptZeroListInnerVoid])
            inner_leftPt = [Pt for Pt in ptZeroListInnerVoid if Pt[0][indX] == inner_leftX][0]
            #ヴォイド構成点の最も右端の座標を取得
            inner_rightX = max([pt[0,indX] for pt in ptZeroListInnerVoid])
            inner_rigntPt = [Pt for Pt in ptZeroListInnerVoid if Pt[0][indX] == inner_rightX][0]
            #targetCnts[0]輪郭構成点群における、ヴォイド最左端、最右端点のインデックスを取得。
            #以下は、targetCnts[0]内部にinner_leftPtと一致する座標を抽出する。
            #ただし、以下の関数ではnumpyの仕様から、X座標の一致とY座標の一致を別に検出してしまうため、
            #一旦ことごとく検出し、unique関数を用いて一致座標を座標一致回数とともに抽出する。
            u_left, counts_left = np.unique(np.where(targetCnts[0] == inner_leftPt)[0], return_counts=True)
            #X、Y座標ともに一致する場合は抽出回数が2であり、これはただ1つ存在するため
            #そのような座標を抽出した後にインデックスを取得する。
            inner_left_index = u_left[counts_left > 1][0]
            #最右端座標に関しても同様の処理をする。
            u_right, counts_right = np.unique(np.where(targetCnts[0] == inner_rigntPt)[0], return_counts=True)
            inner_right_index = u_right[counts_right > 1][0]
            #OpenCVの輪郭抽出においては、閉輪郭抽出の場合、必ずそのインデックス順序は
            #最も左上の座標を基点に反時計回りに振られる。
            #従い、ノズル輪郭上部に存在するヴォイドは、上記アルゴリズムで取得したヴォイドの最右端および最左端部インデックスの間の点である。
            voidContour = targetCnts[0][inner_right_index:inner_left_index]
            #ヴォイド構成点要素数が存在する場合（これしかありえないが、例外除け）
            if len(voidContour) != 0:
                #ヴォイド輪郭を完全に覆う最小の長方形の最小X、最大X、最大Y座標を取得する。（最小Yは必ず0である。）
                left_X_min = min([vCnt[0][0] for vCnt in voidContour])
                right_X_Max = max([vCnt[0][0] for vCnt in voidContour])
                Y = max([vCnt[0][1] for vCnt in voidContour])
                
                #元画像にて、上記長方形座標の内部を黒で塗りつぶす。
                img = cv2.rectangle(img, (left_X_min, 0), (right_X_Max, Y), (0,0,0), -1)
                if DEBUG:
                    calculation_log('img is filled with rectangle Xleft = {}, Xright = {}, Y = {}'.format(
                        left_X_min, 
                        right_X_Max,
                        Y)
                                   )
                #塗りつぶし画像出力する処理
                if flag_export_fillImg:
                    if not os.path.exists(os.path.dirname(path) + "/fillCnts"):
                        os.makedirs(os.path.dirname(path) + "/fillCnts", exist_ok = True)
                        savePath = (os.path.dirname(path) + '/fillCnts/'+ os.path.splitext(os.path.basename(path))[0] +\
                            '_fillCnts.jpg') if mkdir else (os.path.splitext(path)[0] + "_fillCnts.jpg")
                    cv2.imwrite(savePath, img)
                    
                #以下、塗りつぶした画像に対して、グレイスケール化→二値化→輪郭抽出やり直し
                im = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                ret, im_bin = cv2.threshold(
                    im,
                    binarize_thresh,
                    255,
                    (cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU) if auto_binarize else (cv2.THRESH_BINARY_INV))
                #輪郭抽出
                contours, hierarchy = cv2.findContours(im_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                #閾値でフィルタ
                contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_thresh]

    #ターゲット輪郭要素数が2つ以上の場合：これは、輪郭がスプリットするくらいにノズル内部輪郭が白くなっているため
    #上記戦略が取れない。従い、分割された輪郭全てを覆うような長方形を生成し塗りつぶす。
    if len(targetCnts) > 1:
        #各ターゲット輪郭のY = 0なる点を取得
        ptZeroListList = [[Pt for Pt in tgt if Pt[0,indY] == 0] for tgt in targetCnts]
        if DEBUG:
            calculation_log('nozzle contour is completely separated, filling processing is now called.')
        #各ターゲット輪郭の最大X座標の最大値、および最小X座標の最小値を取得（それぞれ、最左端、最右端座標となる）
        leftX = min([min([p[0,indX] for p in pts]) for pts in ptZeroListList]) 
        rightX = max([max([p[0,indX] for p in pts]) for pts in ptZeroListList])
        #輪郭抽出近似を外し、輪郭を構成する全ての座標を抽出。
        #Y座標決定にて、直線部は近似されているため最頻出Y座標とノズルY座標が一致しない可能性が高い。
        #近似を外し、全ての構成点を取得することで、実際のY座標と最頻出Y座標を一致させる。
        #黒塗りをするY座標を、分割輪郭の面積にて重み付けした期待値として取得する。
        #最頻出Y座標は、極小面積のノイズの影響を小さくするため面積にて重み付けした。
        contours, hierarchy = cv2.findContours(im_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        #閾値でフィルタ
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_thresh]
        #再度ターゲットY座標を取得
        targetCnts = [cnt for cnt in contours if any([pt[0,indY] == 0 for pt in cnt])]
        
        #以下、最頻出Yと対象輪郭面積を取得
        freqNum_YList = []
        for tgtCnt in targetCnts:
            freqNum_PtList = []
            for key, ptGroup in groupby(tgtCnt, key=lambda pt:pt[0][1]):
                listPtGroup = list(ptGroup)
                freqNum_PtList.append([len(listPtGroup), key]) 
            freqNum_PtList = [[pt[0], pt[1]] for pt in freqNum_PtList if pt[1] != 0]
            freqNum_PtList.sort(key = lambda elem:elem[0])
            freqNum_YList.append([freqNum_PtList[-1][0], freqNum_PtList[-1][1], cv2.contourArea(tgtCnt)])

        #重みとY座標の積リストを取得
        YAreas = sum([lst[1] * lst[2] for lst in freqNum_YList])
        #面積リストを取得
        Areas = sum([lst[2] for lst in freqNum_YList])
        #Y座標の期待値を算出
        Y_ = (int)(YAreas / Areas)
        #長方形を黒で塗りつぶす。
        img = cv2.rectangle(img,(leftX, 0),(rightX, Y_),(0, 0, 0),-1)
        if DEBUG:
            calculation_log('img is filled with rectangle Xleft = {}, Xright = {}, Y = {}'.format(leftX, rightX, Y_))

        #塗りつぶし画像出力する処理
        if flag_export_fillImg:
            if not os.path.exists(os.path.dirname(path) + "/fillCnts"):
                os.makedirs(os.path.dirname(path) + "/fillCnts", exist_ok = True)
            savePath = (os.path.dirname(path) + '/fillCnts/'+ os.path.splitext(os.path.basename(path))[0] +\
                        '_fillCnts.jpg') if mkdir else (os.path.splitext(path)[0] + "_fillCnts.jpg")
            cv2.imwrite(savePath, img)
            
        #以下、二値化→輪郭抽出やり直し
        im = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, im_bin = cv2.threshold(
            im,
            binarize_thresh,
            255,
            (cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU) if auto_binarize else (cv2.THRESH_BINARY_INV))
        #輪郭抽出
        contours, hierarchy = cv2.findContours(im_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        #閾値でフィルタ
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_thresh]


    #輪郭面積でソート
    contours.sort(key=lambda cnt: cv2.contourArea(cnt), reverse = True)
    if DEBUG:
        calculation_log('the length of contours is {}'.format(len(contours)))
    #輪郭結果格納リストの宣言
    cntResults = []
    imgYMax, _= im.shape
    #各輪郭に対する処理
    for cnt in contours:
        #輪郭面積
        area = cv2.contourArea(cnt)
        #周囲長
        perimeter = cv2.arcLength(cnt, True)
        #凸包輪郭計算
        hull = cv2.convexHull(cnt)
        #凸包面積
        convArea = cv2.contourArea(hull)
        #凸包周囲長さ
        convPerimeter = cv2.arcLength(hull, True)
        #モーメント計算
        M = cv2.moments(cnt)
        #重心X
        cx = int(M['m10']/M['m00'])
        #重心Y
        cy = int(M['m01']/M['m00'])
        
        #Y座標最大のpt左側にて
        yMax = max(cnt, key = lambda pt2:pt2[0,1])[0,1] 
        pt_yMax_xLeft = [pt for pt in cnt if pt[0, 1] == yMax][0][0]
        pt_yMax_xRight = [pt for pt in cnt if pt[0, 1] == yMax][-1][0]
        main_X = (pt_yMax_xLeft[0] + pt_yMax_xRight[0]) / 2
        main_Y = pt_yMax_xRight[1]
        #Y座標最小のpt左側にて
        ymin = min(cnt, key = lambda pt2:pt2[0,1])[0,1]
        pt_yMin_xLeft = [pt for pt in cnt if pt[0, 1] == ymin][0][0]
        pt_yMin_xRight = [pt for pt in cnt if pt[0, 1] == ymin][-1][0]
        satellite_X = (pt_yMin_xLeft[0] + pt_yMin_xRight[0]) / 2
        satellite_Y = pt_yMin_xLeft[1]
        
        #体積と最頻Y座標を取得
        cntList = cnt.tolist()
        cntList.sort(key = lambda pt:pt[0][1])
        volume = 0.0
        freqNum_PtList = []
        for key, ptGroup in groupby(cntList, key=lambda pt:pt[0][1]):
            listPtGroup = list(ptGroup)
            freqNum_PtList.append([len(listPtGroup), key]) 
            if len(listPtGroup) >0:
                x_min = min(listPtGroup, key = lambda pt2:pt2[0][0])[0][0]
                x_max = max(listPtGroup, key = lambda pt2:pt2[0][0])[0][0]
                volume = volume + ((x_max - x_min) / 2.0) ** 2 * math.pi                    
        
        freqNum_PtList.sort(key=lambda freqnum_pt:freqnum_pt[0])
        freq_num, freq_Y = freqNum_PtList[-1][0], freqNum_PtList[-1][1]
        
        #解析結果の格納
        retResultTmp = Analysis_Result(
            delay=delay, 
            main_X=main_X, 
            main_Y=main_Y, 
            satellite_X=satellite_X, 
            satellite_Y=satellite_Y,
            area=area, 
            arclength=perimeter, 
            center_X=cx, center_Y=cy, 
            convex_hull_contour_area=convArea, 
            convex_hull_contour_arclength=convPerimeter,
            imgYMax = imgYMax,
            volume = volume,
            freq_num = freq_num,
            freq_Y = freq_Y,
            DEBUG = DEBUG)
        #解析結果のリストへの追加        
        cntResults.append(retResultTmp)
    
    #面積で降順ソート
    cntResults.sort(key= lambda res: res.area, reverse=True)
    if DEBUG:
        calculation_log('length of cntResults is {}'.format(len(cntResults)))
    #以下、画像出力対応
    if exportImage:
        #ディレクトリ作製
        if mkdir:
            if not os.path.exists(os.path.dirname(path) + "/drawRsts"):
                os.makedirs(os.path.dirname(path) + "/drawRsts", exist_ok = True)
                if DEBUG:
                    calculation_log('mkdir at {}/drawRsts'.format(os.path.dirname(path)))
        #輪郭描画
        if draw_contour:
            #面積最大の輪郭のみ太線で描画
            img = cv2.drawContours(img, [contours[0]], -1, (0,255,0), 2)
            if len(contours) > 1:
                img = cv2.drawContours(img, contours[1:], -1, (0,255,0), 1)
        #凸包輪郭描画
        if draw_convexhull:
            #凸包輪郭取得
            hulls = [cv2.convexHull(cnt) for cnt in contours]
            #描画、面積最大のみ太線
            img = cv2.drawContours(img, [hulls[0]], -1, (255,255,0), 2)
            if len(hulls) > 1:
                img = cv2.drawContours(img, hulls[1:], -1, (255,255,0), 1)
        #座標描画
        if draw_coords:
            for i in range(len(cntResults)):
                main_X = cntResults[i].main_X
                main_Y = cntResults[i].main_Y 
                img = cv2.rectangle(img,
                                    ((int)(main_X-5), (int)(main_Y-5)),
                                    ((int)(main_X+5), (int)(main_Y+5)),
                                    (0,0,255),
                                    2 if i == 0 else 1)
                satellite_X = cntResults[i].satellite_X
                satellite_Y = cntResults[i].satellite_Y
                img = cv2.rectangle(img,
                                    ((int)(satellite_X-5),(int)(satellite_Y-5)),
                                    ((int)(satellite_X+5),(int)(satellite_Y+5)),
                                    (0,255,255),
                                    2 if i == 0 else 1)
                center_X = cntResults[i].center_X
                center_Y = cntResults[i].center_Y
                img = cv2.rectangle(img,
                                    ((int)(center_X-5),(int)(center_Y-5)),
                                    ((int)(center_X+5),(int)(center_Y+5)),
                                    (255,255,255),
                                    2 if i == 0 else 1)      
        #ファイルパス生成
        savePath = (os.path.dirname(path) + '/drawRsts/'+ os.path.splitext(os.path.basename(path))[0] + \
                    '_drawResult.jpg') if mkdir else (os.path.splitext(path)[0] + "_drawResult.jpg")
        #ファイル生成
        cv2.imwrite(savePath, img)
        if DEBUG:
            calculation_log('export image at {}'.format(savePath))
    #輪郭解析結果リストを返す
    return cntResults      


def analyse_Images_List(directoryPath, min_area_thresh, binarize_thresh=128, auto_binarize = True, mkdir=False, \
                        draw_contour = False, draw_convexhull = False, draw_coords = False, exportImage = False, \
                        draw_reg_Detected = False, area_mirgin_detectSeparation = 2000, arc_length_mirgin_detectSeparation = 10, \
                        DEBUG = False):
    '''
    追尾用輪郭解析関数
    
    Parameters
    ----------------------
    directoryPath : str
        画像格納ディレクトリパス
    min_area_thresh : int
        輪郭最小面積[pix]
    binarize_thresh : int
        二値化時閾値画素、初期値128
    auto_binarize : bool
        大津の二値化採用。Trueで大津の二値化。
    mkdir : bool
        描画時ディレクトリ作製
    draw_contour : bool
        輪郭抽出結果の描画出力。初期値False
    draw_convexhull : bool
        凸包輪郭描画。初期値False
    draw_cootds : bool
        輪郭→座標結果の描画。初期値False
    exportImage : bool
        画像出力フラグ。初期値False
    draw_reg_Detected : bool
        リガメント長さ最大値出力フラグ。初期値False
    area_mirgin_detectSeparation : int
        液滴分離検出時閾値面積[pix]
    arc_length_mirgin_detectSeparation : int
        液滴分離検出時輪郭長さ閾値[pix]
    
    
    Returns
    ----------------------
    retAnalysisResults : [[delay, contour]]
        輪郭抽出結果群
        
        delay : float
            ディレイ時間[us]
        contour : [Analysis_Result]
            対応ディレイ時間における輪郭抽出結果群
    '''
    
    #ファイルリストの取得
    files = glob.glob(directoryPath + "/*.jpg")
    if DEBUG:
        calculation_log('files are imported, {}'.format(len(files)))
        calculation_log('min_area_thresh is {}'.format(min_area_thresh))
    #解析結果集計用リスト
    analysisResultsList = []

    for filePath in files:
        #ファイル名前よりディレイ時間の取得
        delay = 0.0
        i = 10
        flag_delay_is_get = False
        while i > 4:
            try:
                delay = float(filePath[-i:-4])
                flag_delay_is_get = True
                break
            except:
                i = i - 1
        
        if not flag_delay_is_get:
            delay = -1.0
        #輪郭抽出結果の格納

        if DEBUG:
            calculation_log('analyse_image method is calling for the delay {} with file {}'.format(delay, filePath))
        appendResults = analyse_Image(
            delay,
            filePath,
            min_area_thresh,
            binarize_thresh,
            auto_binarize,
            draw_contour,
            draw_convexhull,
            draw_coords,
            exportImage,
            mkdir,
            flag_export_fillImg = False,
            DEBUG = DEBUG)
        #一度バラしてリストに格納
        for rst in appendResults:
            analysisResultsList.append(rst)
    #返り値格納用リストに再集計、コンストラクタにてデータ整理
    retAnalysisResults = Analysis_Results_List(analysisResultsList, DEBUG)
    if DEBUG:
        calculation_log('retAnalysisResults object were generated, length is {}'.format(len(retAnalysisResults.analysisResults)))
    #最大リガメント長さの描画、フラグにて有無を制御
    if draw_reg_Detected:
        #分離検出マージン
        separate_detect_area_mirgin = area_mirgin_detectSeparation
        #リガメント長さととのディレイの取得
        regamentResults = retAnalysisResults.get_maximum_regament_length(separate_detect_area_mirgin, arc_length_mirgin_detectSeparation)
        if DEBUG:
            calculation_log('detected delay is {} us, and detected length is {} pix'.format(regamentResults[1], regamentResults[0]))
        #当該輪郭の検出
        drawResultCnts = list(filter(lambda data: data[0] == regamentResults[1], retAnalysisResults.analysisResults))[0]
        drawResultCnt = list(filter(lambda cnt: cnt.get_regament_length() == regamentResults[0], drawResultCnts[1]))[0]
        #ディレクトリ生成
        os.makedirs(directoryPath+'/rgResult', exist_ok=True)
        #当該ディレイの画像ファイルパス取得
        if DEBUG:
            calculation_log('mkdir at {}/rgResult'.format(directoryPath))
        try:
            filePath = glob.glob(directoryPath+'/*{0}.jpg'.format(str(drawResultCnts[0])))[0]
        except:
            filePath = glob.glob(directoryPath+'/*{0}.jpg'.format(str((int)(drawResultCnts[0]))))[0]
        #当該画像データ取得
        im = cv2.imread(filePath)
        #リガメント描画
        im = cv2.line(im,
                      ((int)(drawResultCnt.main_X),(int)(drawResultCnt.main_Y)),
                      ((int)(drawResultCnt.satellite_X),(int)(drawResultCnt.satellite_Y)),
                      (255, 255, 128),
                      3)
        #ファイル出力
        savePath = directoryPath+'/rgResult/' + os.path.basename(filePath) + '_drawRegament.jpg'
        cv2.imwrite(savePath, im)
        if DEBUG:
            calculation_log('export regament result image, {}'.format(savePath))
    
    #返り値
    return retAnalysisResults

def drawContours(delay,
                 path,
                 min_area_thresh,
                 binarize_thresh,
                 auto_binarize = True,
                 draw_convexhull = False,
                 draw_coords = False,
                 exportImage = False,
                 draw_reg_Detected = False,
                 mkdir=False,
                 DEBUG = False):
    '''
    
    '''
    
    if mkdir:
        if not os.path.exists(os.path.dirname(path) + "/drawRsts"):
            os.makedirs(os.path.dirname(path) + "/drawRsts", exist_ok = True)
            if DEBUG:
                calculation_log('mkdir at {}/drawRsts'.format(os.path.dirname(path)))

    im = cv2.imread(path)
    imGray = cv2.imread(path,0)
     #二値化、オートバイナライズか否かで挙動違う
    ret, im_bin = cv2.threshold(
        imGray,
        binarize_thresh, 
        255, 
        (cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU) if auto_binarize else (cv2.THRESH_BINARY_INV))
    #輪郭抽出
    contours, hierarchy = cv2.findContours(im_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #閾値でフィルタ
    contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_thresh].sort(
        key = lambda rst: cv2.contourArea(rst), reverse=True)
    im = cv2.drawContours(im, [contours[0]], -1, (0,255,0), 2)
    if len(contours) > 1:
        im = cv2.drawContours(im, contours[1:], -1, (0,255,0), 1)
    if draw_convexhull:
        hulls = [cv2.convexHull(cnt) for cnt in contours]
        im = cv2.drawContours(im, [hulls[0]], -1, (255,255,0), 2)
        if len(hulls) > 1:
            im = cv2.drawContours(im, hulls[1:], -1, (255,255,0), 1)
    
    if draw_coords:
        coords = analyse_Image(
            delay = delay,
            path=path,
            min_area_thresh = min_area_thresh,
            binarize_thresh=binarize_thresh,
            auto_binarize = auto_binarize
        )
        for i in range(len(coords)):
            main_X = coords[i].main_X
            main_Y = coords[i].main_Y       
            im = cv2.rectangle(im,
                               ((int)(main_X-5),(int)(main_Y-5)),
                               ((int)(main_X+5),(int)(main_Y+5)),
                               (0,0,255),
                               2 if i == 0 else 1)
            satellite_X = coords[i].satellite_X
            satellite_Y = coords[i].satellite_Y
            im = cv2.rectangle(im,
                               ((int)(satellite_X-5),(int)(satellite_Y-5)),
                               ((int)(satellite_X+5),(int)(satellite_Y+5)),
                               (0,255,255),
                               2 if i == 0 else 1)
            center_X = coords[i].center_X
            center_Y = coords[i].center_Y
            im = cv2.rectangle(im,
                               ((int)(center_X-5),(int)(center_Y-5)),
                               ((int)(center_X+5),(int)(center_Y+5)),
                               (255,255,255),
                               2 if i == 0 else 1)            
       
    savePath = (os.path.dirname(path) + '/drawRsts/'+ os.path.splitext(os.path.basename(path))[0] + \
                '_drawResult.jpg') if mkdir else (os.path.splitext(path)[0] + "_drawResult.jpg")
    cv2.imwrite(savePath, im)
    if DEBUG:
        calculation_log('export debug image at {}'.format(savePath))
    return