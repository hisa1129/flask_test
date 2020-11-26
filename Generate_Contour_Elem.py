from CalculationLog import calculation_log #calculation_Log関数のインポート
import numpy as np #numpyのインポート
import cv2 #opencvのインポート
import math #math関数のインポート
import os #os関連インポート
import Contour_Elem
from itertools import groupby
import gc
import Analysis_Results_Class

#analysisResults用インデックス、配列2番目にて指定。
IDX_DELAY = 0
IDX_CNT = 1

#輪郭データ格納numpyArray用インデックス、配列3番目で指定。
IDX_X = 0
IDX_Y = 1

num_evaluate_contour_max = 100

gamma = 0.8
# ガンマ値を使って Look up tableを作成
lookUpTable = np.empty((1,256), np.uint8)
for i in range(256):
    lookUpTable[0,i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)


def filter2d(src, kernel):
    '''
    画像作用関数
    
    Parameter
    =================
    src : np.array
        入力画像
    kernel : np.array
        フィルター行列
    
    return
    =================
    dst : np.array
        出力画像
    '''
    m, n = kernel.shape
    
    d = int((m-1) / 2)
    h, w = src.shape[0], src.shape[1]
    
    dst = np.zeros((h,w))
    
    for y in range(d, h-d):
        for x in range(d, w-d):
            dst[y][x] = np.sum(src[y-d:y+d+1, x-d:x+d+1]*kernel)
    
    return dst
    
#解析結果取得関数
def analyse_Image(delay, 
                  path,
                  min_area_thresh,             
                  binarize_thresh, 
                  auto_binarize,
                  draw_contour,
                  draw_convexhull,
                  draw_coords,
                  exportImage,
                  mkdir,
                  flag_export_fillImg,
                  DEBUG):
    '''
    画像読み込み→輪郭抽出→データ格納関数
    
    Parameters
    ----------------------
    delay : float
        ディレイ時間[ux]
    path : str
        ファイル名
    min_area_thresh : float
        輪郭面積最小値、この値以下はノイズと見做す。
    binarize_thresh : int
        二値化時閾値、auto_binarize = Falseで本値を利用。
    auto_binarize : bool
        自動二値化実行。大津の方法で実行する。
    draw_contour : bool
        輪郭描画フラグ
    draw_convexhull : bool
        凸包輪郭描画フラグ
    draw_coords : bool
        各座標描画フラグ
    exportImage : bool
        画像出力フラグ
    mkdir : bool
        ディレクトリ生成フラグ
    flag_export_fillImg : bool
        輪郭穴埋め結果描画フラグ
    DEBUG : bool  
        デバッグモード起動

    Returns
    ----------------------
    cntResults  : Analysis_Resultクラス
        輪郭抽出結果。画像内にある結果を一括で出力。
    '''
    if DEBUG:
        calculation_log('import file is {} with the fill img flag is {}'.format(path, flag_export_fillImg))
    #BGR画像の読み込み
    img = cv2.imread(path)
    if DEBUG:
        calculation_log('image file {} was imported'.format(path))
    #ガウシアンによるぼかし。バックグラウンドノイズの除去
#    img = cv2.GaussianBlur(img,(9, 9),3)    
    #ガンマ関数
#    img = gamma_function(img)
    #画像のグレイスケール化
    im = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)   
    
    #エッジ強調フィルタのテスト。余計な計算コストとノイズを拾いやすくなることから様子見。
#    kernel = np.array([[-1,-1,-1],
#                      [-1,9,-1],
#                      [-1,-1,-1]])
    
#    im = cv2.filter2D(im, -1, kernel)
    
    #二値化、オートバイナライズか否かで挙動違う
    ret, im_bin = cv2.threshold(
        im,
        binarize_thresh, 
        255, 
        (cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU) if auto_binarize else (cv2.THRESH_BINARY_INV))
    ret = ret - 1
    #輪郭抽出
    contours, hierarchy = cv2.findContours(im_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #閾値でフィルタ
    contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_thresh]
    
    #インデックス値宣言、輪郭X座標インデックス、Y座標インデックスを指定。
    indX, indY = 0, 1
    imgYMax, _= im.shape
    yMax_at_largest_contour = max(contours[0], key = lambda pt2:pt2[0,1])[0,1]
    calculation_log('ymax_at_largest_contour is {}'.format(yMax_at_largest_contour))
    if yMax_at_largest_contour == imgYMax - 1:
        contours.pop(0)
        calculation_log('delete bottom noise')

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
                img = cv2.fillConvexPoly(img, voidContour, color=(ret,ret,ret))
                #img = cv2.rectangle(img, (left_X_min, 0), (right_X_Max, Y), (0,0,0), -1)
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
        img = cv2.rectangle(img,(leftX, 0),(rightX, Y_),(ret, ret, ret),-1)
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
    if len(contours) > num_evaluate_contour_max:
        contours = contours[:num_evaluate_contour_max]
    yMax_at_largest_contour = max(contours[0], key = lambda pt2:pt2[0,1])[0,1]
    ymin_at_largest_contour = min(contours[0], key = lambda pt2:pt2[0,1])[0,1]
    calculation_log('ymax_at_largest_contour is {} after modified'.format(yMax_at_largest_contour))
    if yMax_at_largest_contour == imgYMax - 1:
        contours.pop(0)
        imgYMax = ymin_at_largest_contour
        calculation_log('delete bottom noise')
    if DEBUG:
        calculation_log('the length of contours is {}'.format(len(contours)))
    #輪郭結果格納リストの宣言
    cntResults = []
    
    #サテライトY順に降順ソート
    contours.sort(key=lambda cnt: min(cnt, key = lambda pt2:pt2[0,1])[0,1])
    
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
        if DEBUG:
            calculation_log('contour was analysed with main_y : {}'.format(main_Y))
        
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
        if DEBUG:
            calculation_log('contour was analysed with freq_Y : {}'.format(freq_Y))
        
        #解析結果の格納
        retResultTmp = Contour_Elem.Analysis_Result(
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
        if DEBUG:
            calculation_log('cnt_class with main_Y is {} is generated'.format(retResultTmp.main_Y))
        #解析結果のリストへの追加        
        cntResults.append(retResultTmp)
        if DEBUG:
            calculation_log('cnt with main_Y is {} is appended'.format(cntResults[-1].main_Y))
    
    cntResults = [cnt for cnt in cntResults if cnt.main_Y <= imgYMax]
    cntResults.sort(key= lambda res: res.satellite_Y)  
    #面積で降順ソート
    analysis_contours = Analysis_Results_Class.Analysis_Results(delay, cntResults, DEBUG)
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
        
    #メモリ解放
    del img
    del im
    del contours
    gc.collect()
    #輪郭解析結果リストを返す
    return analysis_contours    

def gamma_function(img):
    calculation_log('gamma_function is calling.')
    return cv2.LUT(img, lookUpTable)    
