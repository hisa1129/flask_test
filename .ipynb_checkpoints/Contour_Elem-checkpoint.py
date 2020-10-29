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
        
    method
    ----------    
    __init__ : None
        コンストラクタ、
    get_regament_lentgh() : float
        リガメント長さ取得関数、メイン座標とサテライト座標の距離[pix]を返す。
    is_equal(cnt) : bool
        輪郭比較関数、パラメータ一致でTrue
    
    '''
    
    def __init__(self, 
                 delay,
                 main_X,
                 main_Y,
                 satellite_X,
                 satellite_Y,
                 arclength,
                 area,
                 center_X,
                 center_Y,
                 convex_hull_contour_area,
                 convex_hull_contour_arclength,
                 imgYMax,
                 volume,
                 freq_num, 
                 freq_Y,
                 DEBUG):
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
        if DEBUG:
            calculation_log('constructor of Analysis_Class is called with main_y: {}'.format(main_Y))
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
        
        is_equal = (flag_delay and flag_mainX and flag_mainY and flag_satelliteX and flag_satelliteY and\
                flag_arclength and flag_area and flag_centerX and flag_centerY and flag_convHullArea and\
                flag_convHullArc and flag_imgMax and flag_volume and flag_freqYNum and flag_freqY)
        
        return is_equal