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
import Analysis_Contours_List_Class
from Contour_Elem import *
from Generate_Contour_Elem import *

#コードバージョン記載
CONTOUR_CODE_VER = '0.0.1'

#analysisResults用インデックス、配列2番目にて指定。
IDX_DELAY = 0
IDX_CNT = 1

#輪郭データ格納numpyArray用インデックス、配列3番目で指定。
IDX_X = 0
IDX_Y = 1

#コードバージョン取得用関数
def get_code_ver():
    '''
    連続輪郭解析コードバージョン取得関数
    
    argments:なし
    
    return
    =============
    CONTOUR_CODE_VER : str
        輪郭検出コードバージョン
    '''
    return CONTOUR_CODE_VER
    
#輪郭連続解析実行関数
def analyse_Images_List(directoryPath,
                        min_area_thresh,
                        binarize_thresh,
                        auto_binarize,
                        area_mirgin_detect_faced,
                        area_mirgin_detect_separation,
                        arc_length_mirgin_detect_separation,
                        solidity_mirgin_detect_separation,
                        noise_remove_topological_dist_thresh,
                        noise_remove_area_thresh,
                        mkdir,
                        draw_contour, 
                        draw_convexhull,
                        draw_coords,
                        exportImage,
                        draw_reg_Detected,
                        DEBUG):
    '''
    画像ディレクトリ→連続輪郭解析関数
    
    Parameters
    ----------------------
    directoryPath : str
        解析ディレクトリ名
    min_area_thresh : float
        最小面積閾値[pix]
    binarize_thresh : int
        二値化閾値
    auto_binarize : bool
        自動二値化（大津の方法）実行
    area_mirgin_detect_faced : float
        液滴吐出開始検知閾値[pix]
    area_mirgin_detect_separation : float
        液滴分離検知面積閾値[pix]
    arc_length_mirgin_detect_separation : float
        液滴分離検知輪郭長閾値[pix]
    solidity_mirgin_detect_separation : float
        液滴分離検知solidity比閾値[U]
    noise_remove_topological_dist_thresh : float
        ノイズ除去時輪郭類似判定位相空間距離閾値
    noise_remove_area_thresh : float
        ノイズ除去時輪郭面積上限[pix]
    mkdir : bool
        ディレクトリ作製フラグ
    draw_contour : bool
        輪郭描画フラグ
    draw_convexhull : bool
        凸包輪郭描画フラグ
    draw_coords : bool
        各座標描画フラグ
    exportImage : bool
        解析結果画像出力フラグ
    draw_reg_Detected : bool
        最大輪郭検出結果画像出力フラグ
    DEBUG : bool
        デバッグモードフラグ
    
    Returns
    ----------------------
    retAnalysisResults : Analysis_Results_Listクラス
        輪郭抽出結果群
    '''
    
    #ファイルリストの取得
    extension = '.jpg'
    files = glob.glob(directoryPath + "/*" + extension)
    if DEBUG:
        calculation_log('files are imported, {}'.format(len(files)))
        calculation_log('min_area_thresh is {}'.format(min_area_thresh))
    #解析結果集計用リスト
    analysisResultsList = []
    #ファイル名末尾よりディレイ時間取得
    for filePath in files:
        #ファイル名前よりディレイ時間の取得
        delay = 0.0
        max_description_field_length = 10
        i = max_description_field_length
        flag_delay_is_get = False
        while i > len(extension):
            try:
                delay = float(filePath[-i:-len(extension)])
                flag_delay_is_get = True
                break
            except:
                i = i - 1
        
        if not flag_delay_is_get:
            delay = -1.0
        #輪郭抽出結果の格納

        if DEBUG:
            calculation_log('analyse_image method is calling for the delay {} with file {}'.format(delay, filePath))
        #画像→輪郭解析実行
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
            if DEBUG:
                calculation_log('analysis image results were appended for the delay {} with file {}'.format(delay, filePath))

    #全画像輪郭解析実施後処理
    if DEBUG:
        calculation_log('contour_list was completed with length {}'.format(len(analysisResultsList)))
    #返り値格納用リストに再集計、コンストラクタにてデータ整理
    retAnalysisResults = Analysis_Contours_List_Class.Analysis_Results_List(
        analysis_results_list = analysisResultsList,
        area_mirgin_detect_faced = area_mirgin_detect_faced,
        area_mirgin_detect_separation = area_mirgin_detect_separation,
        arc_length_mirgin_detect_separation = arc_length_mirgin_detect_separation,
        solidity_mirgin_detect_separation = solidity_mirgin_detect_separation,
        noise_remove_topological_dist_thresh = noise_remove_topological_dist_thresh,
        noise_remove_area_thresh = noise_remove_area_thresh,
        DEBUG = DEBUG
    )
    #解析結果群格納クラス取得後処理    
    if DEBUG:
        calculation_log('retAnalysisResults object were generated, length is {}'.format(len(retAnalysisResults.analysisResults)))
    #最大リガメント長さの描画、フラグにて有無を制御
    if draw_reg_Detected:
        regamentResults = retAnalysisResults.max_regament_length, retAnalysisResults.delay_max_regament_detected
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
    
    #成功処理
    if DEBUG:
        calculation_log('cnt selection was completed.')
    #関数終了
    return retAnalysisResults

def drawContours(delay,
                 path,
                 min_area_thresh,
                 binarize_thresh,
                 auto_binarize,
                 draw_convexhull,
                 draw_coords,
                 exportImage,
                 draw_reg_Detected,
                 mkdir,
                 DEBUG):
    '''
    デバッグ時輪郭解析結果出力関数
    
    
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
        symbol_size = 5
        for i in range(len(coords)):
            main_X = coords[i].main_X
            main_Y = coords[i].main_Y       
            im = cv2.rectangle(im,
                               ((int)(main_X-symbol_size),(int)(main_Y-symbol_size)),
                               ((int)(main_X+symbol_size),(int)(main_Y+symbol_size)),
                               (0,0,255),
                               2 if i == 0 else 1)
            satellite_X = coords[i].satellite_X
            satellite_Y = coords[i].satellite_Y
            im = cv2.rectangle(im,
                               ((int)(satellite_X-symbol_size),(int)(satellite_Y-symbol_size)),
                               ((int)(satellite_X+symbol_size),(int)(satellite_Y+symbol_size)),
                               (0,255,255),
                               2 if i == 0 else 1)
            center_X = coords[i].center_X
            center_Y = coords[i].center_Y
            im = cv2.rectangle(im,
                               ((int)(center_X-symbol_size),(int)(center_Y-symbol_size)),
                               ((int)(center_X+symbol_size),(int)(center_Y+symbol_size)),
                               (255,255,255),
                               2 if i == 0 else 1)            
       
    savePath = (os.path.dirname(path) + '/drawRsts/'+ os.path.splitext(os.path.basename(path))[0] + \
                '_drawResult.jpg') if mkdir else (os.path.splitext(path)[0] + "_drawResult.jpg")
    cv2.imwrite(savePath, im)
    if DEBUG:
        calculation_log('export debug image at {}'.format(savePath))
    return None