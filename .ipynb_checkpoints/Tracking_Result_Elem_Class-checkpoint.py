import math

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
    
    method
    ----------
    __init__ (delay): None
        コンストラクタ、クラス生成とディレイ時間の格納
    set_mainXY(main_X, main_Y) : None
        メインX座標、Y座標のセット
    set_satellite_XY(satellite_X, satellite_Y) : None
        サテライトX座標、Y座標のセット
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