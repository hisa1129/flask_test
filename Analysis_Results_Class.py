import Contour_Elem
import numpy as np
import math
from CalculationLog import calculation_log

class Analysis_Results:
    '''
    単独画像輪郭格納クラス
    
    '''
    
    def __init__(self, delay, contours, DEBUG):
        if DEBUG:
            calculation_log('constructor of contours_analysis_results in single_image was called')
        self.contours = contours
        self.delay = delay
        self.__DEBUG = DEBUG
        if DEBUG:
            calculation_log('datas were setted.')            
        self.__set_convex_hull_area_of_nozzle()
        self.__set_area_of_nozzle()
        self.__set_arclength_of_nozzle()
        self.__set_convex_hull_arclength_of_nozzle()
        self.__set_solidity_of_nozzle()
        self.__set_freq_Y_of_nozzle()
        self.__set_num_contours()
        self.__set_max_reg_length_in_delay()
        self.__set_max_mainXY()
        self.__set_satellite_suspicious_XY()
        self.__set_volume_without_nozzle()
        return None
           
    def __set_convex_hull_area_of_nozzle(self):
        '''
        ノズルのConvex_Hull_Area値を取得する関数
        '''
        if self.__DEBUG:
            calculation_log('set convex_hull_area_of_nozzle')        
        convex_hull_area_of_nozzle = self.contours[0].convex_hull_contour_area
        self.convex_hull_area_of_nozzle = convex_hull_area_of_nozzle
        return None
        
    def __set_area_of_nozzle(self):
        '''
        ノズルのArea値を取得する関数
        '''
        if self.__DEBUG:
            calculation_log('set area_of_nozzle')
        area_of_nozzle = self.contours[0].area
        self.area_of_nozzle = area_of_nozzle
        return None

    def __set_arclength_of_nozzle(self):
        '''
        ノズルのArclength値を取得する関数
        '''
        if self.__DEBUG:
            calculation_log('set arclength_of_nozzle')
        arclength_of_nozzle = self.contours[0].arclength
        self.arclength_of_nozzle = arclength_of_nozzle
        return None
    
    def __set_convex_hull_arclength_of_nozzle(self):
        '''
        ノズルのconvex_hull_arclength値を取得する関数
        '''
        if self.__DEBUG:
            calculation_log('set convex_hull_arclength_of_nozzle')
        convex_hull_arclength_of_nozzle = self.contours[0].convex_hull_contour_arclength
        self.convex_hull_arclength_of_nozzle = convex_hull_arclength_of_nozzle
        return None
    
    def __set_solidity_of_nozzle(self):
        '''
        ノズルのSolidity値を取得する関数
        '''
        if self.__DEBUG:
            calculation_log('set solidity_of_nozzle')
        solidity_of_nozzle = self.convex_hull_area_of_nozzle / self.area_of_nozzle
        self.solidity_of_nozzle = solidity_of_nozzle
        return None
    
    def __set_freq_Y_of_nozzle(self):
        '''
        ノズルの最頻出Y座標を取得する関数
        '''
        if self.__DEBUG:
            calculation_log('set freq_Y_of_nozzle')
        self.freq_Y_of_Nozzle = self.contours[0].freq_Y
        self.num_freq_Y_of_Nozzle = self.contours[0].freq_num
        return None

    def __set_num_contours(self):
        '''
        画像内の輪郭数をカウントする関数
        ※ノイズ除去前ゆえ、ノイズが含まれる可能性がある。
        '''
        if self.__DEBUG:
            calculation_log('set num_contours')
        num_contours = len(self.contours)
        self.num_contours = num_contours

        return None

    def __set_max_mainXY(self):
        '''
        メイン液滴と推定される座標を取得
        （main_Y座標最大となる輪郭のmain_X、main_Y座標を取得）
        '''
        if self.__DEBUG:
            calculation_log('set max_MainXY')
        mainXY = sorted(self.contours, key = lambda cnt : cnt.area, reverse = True)[0]
        self.max_mainY = mainXY.main_Y
        self.max_mainX = mainXY.main_X
        
        return None
    
    def __set_satellite_suspicious_XY(self):
        '''
        サテライト液滴座標と推定される座標を取得
        '''
        if self.__DEBUG:
            calculation_log('set sattelite_like_XY')
        set_num_X = 0
        set_num_Y = 0
        if self.num_contours < 2:
            set_num_X = -1
            set_num_Y = -1
        else:
            eval_cnts = sorted(self.contours, key = lambda cnt : cnt.satellite_Y )
            set_num_X = eval_cnts[1].satellite_X
            set_num_Y = eval_cnts[1].satellite_Y
        
        self.satellite_suspicious_X = set_num_X
        self.satellite_suspicious_Y = set_num_Y
        
        return None
            
    def __set_max_reg_length_in_delay(self):
        '''
        リガメント値が最大となる輪郭のリガメント値を取得
        '''
        if self.__DEBUG:
            calculation_log('set max_reg_length')
        set_value = -1
        if not self.num_contours < 2:
            eval_cnts = self.contours[1:]
            reg_length_list = [cnt.get_regament_length() for cnt in eval_cnts]
            set_value = max(reg_length_list)

        self.max_reg_length_in_delay = set_value
        return None
    
    def __set_volume_without_nozzle(self):
        '''
        ノズル輪郭をのぞく輪郭の体積値の和を取得
        '''
        if self.__DEBUG:
            calculation_log('set volume without_nozzle')
        set_value = 0
        if not self.num_contours < 2:
            eval_cnts = self.contours[1:]
            volume_list = [cnt.volume for cnt in eval_cnts]
            set_value = max(volume_list)

        self.volume_without_nozzle = set_value
        return None