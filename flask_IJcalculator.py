from flask import *
import math
import ssl
import Get_AutoTracking_Results
from flask_cors import CORS, cross_origin
import pandas as pd
import numpy as np
import datetime
import json
import werkzeug
import os
import zipfile
import tempfile
import shutil
import io
import time
import sys
import requests

#起動モード指定
args = sys.argv
TEST_MODE = False
NET_MODE = False
if len(args) > 1:
    TEST_MODE = str(args[1]) == 'TEST'
    if TEST_MODE:
        print('test mode')
if len(args) > 2:
    NET_MODE = str(args[2]) == 'NET'
    if NET_MODE:
        print('net mode')

#API内共通変数
API_VER = '0.0.1' #APIコードのバージョン、2020.10.21

UPLOAD_DIR = 'uploads' #アップロードファイル格納ディレクトリ名
ALLOWED_EXTENSIONS = set(['zip']) #許容拡張子
RESULTSDB = 'resultsDB.csv' #計算結果格納csvファイル名
SERVER_LOG = 'server.log' #サーバー処理ログ格納ファイル名

#ルーティングURLの指定用ディクショナリ
URLs = {
    #自動追尾機能
    "auto_tracking":'/auto_tracking',
    #厚み、径→接触角、吐出体積計算用
    "calculation contactangle and volume":"/calculator/contactangle_volume",
    #吐出体積、径→厚み、接触角計算用
    "calculation contactangle and thickness":"/calculator/contactangle_thickness",
    #接触角、吐出体積→厚み、径計算用
    "calculation diameter and thickness":"/calculator/diameter_thickness",
    #平均膜厚計算用
    "calculation average thicnkess":"/calculator/average_thickness",
    #自動追尾デモ
    "auto_tracking_demo":"/auto_tracking_demo",
     #zipファイル投稿
    "auto_tracking with upload file":'/auto_tracking_upload_file',
    #管理ファイルダウンロード用
    "download management file":"/download_file/<string:fileType>",
    #保存済ファイルダウンロード用
    "download restored files":'/download_restored_files', 
    #計算フォーム出力用
    "show calculation form":"/calculator/form/<string:calculationType>",
    #断続吐出解析
    "analyze_multipleintermittency_firing":"/analyse/multi_intermittency",
    # 1枚画像テスト用
    "analyze_single_delay_image":"/analyse/single_delay_image",
}

#ポート番号指定、ローカルデバッグで8080、ネット上で443
MAIN_SERVER_PORT = 8080
if NET_MODE:
    MAIN_SERVER_PORT = 443

MIMETYPE_CSV = 'text/csv' #csvファイル出力MIMETYPE
MIMETYPE_ZIP = 'application/zip' #zipファイル出力MIMETYPE

DEBUG_MODE = 'DEBUG' #デバッグモード指定文字列
RESTORE_MODE = 'RESTORE' #ファイル保持モード指定文字列
RESTORE_DIR = 'restored_data' #解析結果画像出力時保存ディレクトリ名
CALCULATION_LOG = 'calculation_log.log' #計算処理デバッグ結果格納ファイル名
DOWNLOAD_FILE_TYPE = ['result_csv', 'server_log', 'calculation_log'] #管理ファイルDL時指定キー

#装置毎のカメラ解像度、[um/pix]
dic_camera_resolution = {
    'LJ-600':3.50,
    'NJ-X':3.50,
    'Jet-Tester':3.50,
}

#appの宣言、Flaskにて起動を指示。
app = Flask(__name__)
if NET_MODE:
    #★クロスサイト時に必要な設定、ネット上では定義
    CORS(app, support_credentials=True)
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('cert.crt', 'server_secret.key')

# 最大アップロードファイルサイズの定義、10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# シークレットキーの設定、公開の際にはOSからランダム値を生成し入力する。
app.config.from_mapping(SECRET_KEY='hogehoge')

def out_server_log(sentence):
    '''
    サーバーログ出力関数
    SERVER_LOGファイルに入力センテンスを1行出力する。
    
    argment
    ===================
    sentence : str
        出力文字列
    
    return
    ===================
    なし
    '''
    time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = SERVER_LOG
    with open(filepath, mode = 'a') as f:
        f.write('{} : {}\r\n'.format(time, sentence))
    return

def is_allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ファイルを受け取る方法の指定
@app.route(URLs["auto_tracking"], methods=['POST'])
@cross_origin(supports_credentials=True)
def uploads_file():
    '''
    
    '''

    file_read_error_result = {
        "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
        "API_VER":API_VER,
        "condition":'upload_file is FAILED.'
    }

    #ログ書きだし
    out_server_log('auto_tracking calculation with {} method was called'.format(request.method))
    #postメソッド時の処理
    if request.method == "POST":
        #ファイル名取り出しログ
        out_server_log('{} file is posted, {}, {}, {}'.format(request.files, request.form['filename'], request.form['mode'], request.form['filerestore']))
        # request.files内にuploadFile要素が無い場合
        if 'upload_file' not in request.files:
            out_server_log('file was empty')
            return make_response(jsonify(file_read_error_result))

        #ファイル受け取り
        file = request.files['upload_file']
        fileName = file.filename
        if (not fileName) or fileName == '':
            uploaded_file_name = request.form['filename']
            uploaded_files = [f for f in os.listdir(UPLOAD_DIR) if f == uploaded_file_name]
            if len(uploaded_files) != 1:
                out_server_log('file upload was FAILED')
                return make_response(jsonify(file_read_error_result))
            fileName = uploaded_files[0]
        else:
            #ファイル保存、UPLOAD_DIR内にzipを出力
            file.save(os.path.join(UPLOAD_DIR, fileName))
        uploaded_file_name = str(request.form['filename'])
        #ファイル処理後のサーバー上への保存の選択指示の受け取り
        flagFileRestore = str(request.form["filerestore"]) == RESTORE_MODE
        #デバッグモード指示受け取り
        exec_mode = str(request.form["mode"])
        #カメラ解像度受け取り
        try:
            camera_resolution = float(request.form["camera_resolution"])
        except:
            camera_resolution = dic_camera_resolution['NJ-X']
    
    if '' == fileName:
        our_server_log('uploaded filename was empty.')
        file_read_error_result.update({
            'filename':fileName,
            'condition':'filename was empty.'
        })
        result = file_read_error_result
        return make_response(jsonify(result))
    if not is_allwed_file(fileName):
        out_server_log('extension of uploaded file was not zip.')
        file_read_error_result.update({
            'filename':fileName,
            'condition':'extension is not zip.'
        })
        result = file_read_error_result
        return make_response(jsonify(result))

    out_server_log('exec_mode is {}, fire restore is {}, camera_resolution is {}'.format(
        exec_mode,
        flagFileRestore,
        camera_resolution))
    # ★ポイント4
    created_file_path = os.path.join(UPLOAD_DIR, fileName)
    with zipfile.ZipFile(created_file_path) as existing_zip:
        out_server_log('extraction uploaded zip file at {}'.format(created_file_path.strip('.zip')))
        existing_zip.extractall(created_file_path.strip('.zip'))
    time.sleep(0.3)
    created_dir = [f for f in os.listdir(created_file_path.strip('.zip')) if os.path.isdir(os.path.join(created_file_path.strip('.zip'), f))][0]
    directory_path = os.path.join(created_file_path.strip('.zip'), created_dir)
    try:
        df = pd.read_csv(RESULTSDB)
        out_server_log('import results from {} was done'.format(RESULTSDB))
    except:
        df = pd.DataFrame(columns = [])
        out_server_log('impot results from {} was FAILED'.format(RESULTSDB))
        
    result = Get_AutoTracking_Results.get_autoTracking_Results(directory_path, camera_resolution, API_VER, exec_mode)
    out_server_log('auto_tracking is execute with {}, the exec_mode {}'.format(directory_path, exec_mode))
    try:
        resultJS = json.dumps(result)
        try:
            df_add = pd.DataFrame([result])
            try:
                df = pd.concat([df, df_add], axis = 0)
                df.to_csv(RESULTSDB, index = False, encoding = 'utf-8-sig')                   
                out_server_log('export calculation result to {} was succeed.'.format(RESULTSDB))
            except:
                out_server_log('export calculation result to {} was failured.'.format(RESULTSDB))               
        except:
            out_server_log('read_dataframe from json-formatted string was failured.')
    except:
        out_server_log('read result as json was failured.')
        
    if not flagFileRestore:
        #生成ファイル処理
        shutil.rmtree(UPLOAD_DIR)
        os.mkdir(UPLOAD_DIR) 
        out_server_log('Both files at {}, and the uploaded zipfile {} were deleted'.format(created_file_path.strip('.zip'), created_file_path))
    else:
        src = created_file_path.strip('.zip')
        dst = os.path.join(RESTORE_DIR, fileName.strip('.zip'))
        dst_org = dst
        fileNum = 2
        while os.path.exists(dst):
            dst = dst_org + '_{}'.format(fileNum)
            fileNum = fileNum + 1
        shutil.copytree(src, dst)
        out_server_log('files were saved at {}'.format(dst))
        shutil.rmtree(UPLOAD_DIR)
        os.mkdir(UPLOAD_DIR)       
        out_server_log('files at {} and {} were deleted'.format(created_file_path.strip('.zip'), created_file_path))
    time.sleep(0.2)
    return make_response(jsonify(result))

# ファイルサイズ上限オーバー時の処理
@app.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
@cross_origin(supports_credentials=True)
def handle_over_max_file_size(error):
    out_server_log('uploaded file size is to large.')
    return 'result : file size is overed.'

@app.route(URLs["calculation contactangle and volume"], methods=['GET'])
@cross_origin(supports_credentials=True)
def calculate_contact_angle_and_firevolume():
    '''
    ・機能：基板上の液滴の厚み、直径から、体積と接触角を２Θ法で算出
　　・パラメータ：thickness : float
　　　　　　　　　　厚み、単位は[μm]
　　　　　　　　　diameter : float
　　　　　　　　　　液滴直径、単位は[um]
　　・返り値：contact_angle[degrees] ：float
　　　　　　　　　　接触角、単位は[degrees]
　　　　　　　fire_volume[pl] : float
　　　　　　　　　　液滴体積、単位は[pl]
　　・使用例：http://192.168.1.44:8080/calculator/angle_volume?thickness=35.0&diameter=100.0
    
    '''
    #変数宣言
    flag_argments_are_good = False
    thickness = 0.0
    diameter = 0.0
    result = []
    out_server_log('calculate_contactagnle_and_firevolume method is called with {} method.'.format(request.method))
   
    #メソッド別パラメータ取得、GETメソッド
    if request.method == 'GET':
        try:
            thickness = float(request.args.get('thickness'))
            diameter = float(request.args.get('diameter'))
            flag_argments_are_good = True
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make both thickness and diameter positive, and both the value types float'
            }         
            out_server_log('argments type are invalid')
    else:
        retult = {
            'condition' : 'the method is BAD'
        }
    #数値異常の検出
    if thickness <= 0 or diameter <= 0:
        flag_argments_are_good =False
        result = {
            'condition' : 'argments were invalid, both thickness and diameter must be positive value',
            'correspondence' : 'make both thickness and diameter positive.'
        }         
        out_server_log('neither thickness or diameter value is not positive.')
    
    #パラメータ取得時の計算
    if flag_argments_are_good:         
        radius = diameter/2.0
        firevolume = math.pi / 6.0 * thickness * ((radius ** 2) * 3.0 + thickness ** 2) / 1000.0
        contactangle = math.degrees(math.atan(thickness / radius))
        result = {
            'contact_angle[degrees]':contactangle,
            'fire_volume[pl]':firevolume
        }
        out_server_log('calculation was done.')
    
    return make_response(jsonify(result))  

@app.route(URLs["calculation contactangle and thickness"], methods=['GET'])
@cross_origin(supports_credentials=True)
def calculate_contact_angle_and_thickness():
    '''
    ・機能：基板上の液滴の直径と体積から、接触角と厚みを２Θ法で算出
　　・パラメータ：diameter : float
　　　　　　　　　　液滴直径、単位は[μm]
　　　　　　　　　firevolume : float
　　　　　　　　　　液滴体積、単位は[pl]
　　・返り値：contact_angle[degrees] ：float
　　　　　　　　　　接触角、単位は[degrees]
　　　　　　　thickness[um] : float
　　　　　　　　　　液滴厚み、単位は[um]
　　・使用例：http://192.168.1.44:8080/calculator/contactangle_thickness?diameter=100.0&firevolume=35.0
    '''

    out_server_log('calculate_contactangle_thickness method is called with {} method'.format(request.method))
    flag_argments_are_good = False
    diameter = 0.0
    firevolume = 0.0
    if request.method == 'GET':
        try:
            diameter = float(request.args.get('diameter'))
            firevolume = float(request.args.get('firevolume'))
            flag_argments_are_good = True
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make both diameter and firevolume positive, and both the value types float'
            }
            out_server_log('argments type is invalid.')
            
    else:
        retult = {
            'condition' : 'the method is bad.'
        }
    
    if diameter <= 0 or firevolume <= 0:
        flag_argments_are_good =False
        result = {
            'condition' : 'argments were invalid, both diameter and firevolume requires to be positive value',
            'correspondence' : 'make both diameter and firevolume positive, and both the value types float'
        }         
        out_server_log('neither diameter nor firevolume value is not positive.')

                             
    if flag_argments_are_good:
        radius = diameter / 2.0
        varP = 3.0 * radius ** 2.0
        varQ = -6.0 / math.pi * firevolume * 1000.0
        var_sqrt = varP*varP*varP * 4.0 / 27.0 + varQ * varQ
        varA = (-varQ + math.sqrt(var_sqrt)) / 2.0
        varB = (-varQ - math.sqrt(var_sqrt)) / 2.0
        a = varA ** (1.0/3.0)
        b = varB ** (1.0/3.0) if varB >= 0 else -(-varB)**(1.0/3.0)
        thickness = a + b
        thicknessOverL = thickness / radius
        varAlpha = 1.0 + thicknessOverL ** 2.0
        varBeta = 1.0 - thicknessOverL ** 2.0
        sinContactAngle = 1.0 / varAlpha * (1.0 - math.sqrt(1.0 - varAlpha * varBeta))
        contactangle = 90.0 - math.degrees(math.asin(sinContactAngle))
        result = {
            'contact_angle[degrees]':contactangle,
            'thickness[um]':thickness
        }
        out_server_log('calculation was done.')

    return make_response(jsonify(result))
    
@app.route(URLs["calculation diameter and thickness"], methods=['GET'])
@cross_origin(supports_credentials=True)
def calculate_diameter_and_thickness():
    '''
    ・機能：基板と液滴の接触角と体積から、直径と厚みを２Θ法で算出
　　・パラメータ：contactangle : float
　　　　　　　　　　液滴 - 基板の接触角、単位は[degrees]
　　　　　　　　　firevolume : float
　　　　　　　　　　液滴体積、単位は[pl]
　　・返り値：diameter[um] ：float
　　　　　　　　　　液滴直径、単位は[um]
　　　　　　　thickness[um] : float
　　　　　　　　　　液滴厚み、単位は[um]
　　・使用例：http://192.168.1.44:8080/calculator/diameter_thickness?contactangle=45.0&firevolume=35.0
    '''
    
    out_server_log('calculate_diameter_thickness method is called with {} method'.format(request.method))
    flag_argments_are_good = False
    contactangle = 0.0
    firevolume=0.0

    if request.method == 'GET':
        try:
            contactangle = float(request.args.get('contactangle'))
            firevolume = float(request.args.get('firevolume'))
            flag_argments_are_good = True            
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make both contactangle and firevolume positive, and both the value types float'
            }
            out_server_log('argments type is invalid.')
            
    else:
        retult = {
            'condition' : 'the method is bad.'
        }

                               
    if contactangle > 180 or contactangle < 0:
        flag_argments_are_good = False
        result = {
            'condition' : 'contactangle must be between 0 and 180 degrees',            
            'correspondence' : 'make contactangle value between 0 and 180.'
        }
        out_server_log('contactangle value is invalid')
    
    if firevolume <= 0:
        flag_argments_are_good = False
        result = {
            'condition' : 'firevolume must be positive value',                        
            'correspondence' : 'make firevolume value positive.'
        }
        out_server_log('firevolume value is negative')
                               
                               
    if flag_argments_are_good:
        contactangle_rad = math.radians(contactangle)
        varA = 1.0 + math.sin(contactangle_rad - math.pi / 2.0)
        varB = 6.0 / varA - 2.0
        thickness = (6.0 * firevolume / math.pi / varB) ** (1.0/3.0) * 10.0
        radianSphere = thickness / varA
        diameter = 2.0 * radianSphere * math.cos(contactangle_rad - math.pi / 2.0)
        result = {
            'diameter[um]':diameter,
            'thickness[um]':thickness
        }
        out_server_log('calculation was done.')
    
    return make_response(jsonify(result))

@app.route(URLs["calculation average thicnkess"], methods=['GET'])
@cross_origin(supports_credentials=True)
def calculate_averagethickness():
    '''
    ・機能：印刷メッシュ、液滴サイズ、固形分濃度と繰り返し回数から平均膜厚を計算
　　・URL：http://192.168.1.44:8080/calculator/avethickness
　　・パラメータ：pitchexpression : str
                   入力パラメータの表現。「dpi」でdpi表記、それ以外でum表記               
                 dotpitch : float
　　　　　　　　    液滴ドットピッチ
　　　　　　　　　firevolume : float
　　　　　　　　　  液滴ラインピッチ
　　　　　　　　　firevolume : float
　　　　　　　　　　液滴体積 [pl]
　　　　　　　　　printcount : int
　　　　　　　　　　印刷回数
　　　　　　　　　concentration : float
　　　　　　　　　　液滴固形分濃度[vol.%]
　　・返り値：thickness_ave[nm] ：float
　　　　　　　　　　平均膜厚、単位は[nm]
    '''
    
    out_server_log('calculate_averagethickness method is called with {} method'.format(request.method))
    flagDPI = False
    dotpitchlength = 0.0
    linepitchlength = 0.0
    firevolume = 0.0
    numprint = 0.0
    concentration = 0.0
    flag_argments_are_good = False
    if request.method == 'GET':
        try:
            flagDPI = (str(request.args.get('pitchexpression')) == 'dpi')
            dotpitchlength = float(request.args.get('dotpitch'))
            linepitchlength = float(request.args.get('linepitch'))
            firevolume = float(request.args.get('firevolume'))
            numprint = float(request.args.get('firecycle'))
            concentration = float(request.args.get('concentration'))
            flag_argments_are_good = True
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make all the argment types except pitchexpression float, and all the values positive. the type of pitchexpression should be string.'
            }
            out_server_log('argments type is invalid.')

    else:
        retult = {
            'condition' : 'the method is bad'
        }
    
    if dotpitchlength <= 0 or linepitchlength <= 0 or firevolume <= 0 or numprint < 0 or concentration < 0:
        result = {
            'condition' : 'argments were invalid! all the values must be positive values',            
            'correspondence' : 'make all the values positive.'
        }
        out_server_log('at least one parameter is not positive value.')
                               
    if flag_argments_are_good:
        dotpitchlength = 25400.0 / dotpitchlength if flagDPI else dotpitchlength
        linepitchlength = 25400.0 / linepitchlength if flagDPI else linepitchlength
        thickness_ave = firevolume * numprint * concentration * 10000.0 / dotpitchlength / linepitchlength
        result = {
            'thickness_ave[nm]':thickness_ave
        }
        out_server_log('calculation was done.')
        
    return make_response(jsonify(result))
   
@app.route(URLs["auto_tracking_demo"], methods = ['GET'])
@cross_origin(supports_credentials=True)
def get_autotracking():
    '''
    追尾→特徴量抽出関数   
    ・パラメータ：dirpath : str
                    ディレクトリパス
　　・返り値：
      <異常処理時>
      結果通知json
      {
          'condition' :"""処理結果""" 
      }
      　・メソッドエラー
      　・変数取得エラー
      　・処理エラー内容
      を通知。
      <正常処理時>
      特徴量クラス : json
          'dirPath' : str
              渡されたディレクトリパス
          'solidity[U]' : float
              各画像での最大面積輪郭のconvex_hull_area / area比の最小値、ノズルの凹凸具合を示す。
          'arc_solidity[u]' : float
              各画像での最大面積輪郭のconvex_hull_arclength / arclength比の最大値、ノズルの凹凸具合を示す。              
          'separated_delay[us]': float
              液滴分離検知タイミングのディレイ時間[us]
          'faced_delay[us]' : float
              液滴吐出開始検知タイミングのディレイ時間[us]
          'regament_max_delay[us]' : float
              リガメント長さ最大のディレイ時間[us]
          'max_regament_length[pix]' : float
              最大リガメント長さ[pix]
          'main_average_velocity[pix/us]' : float
              平均メイン液滴速度[pix/us]
          'main_velocity_stddiv[pix/us]' : float
              メイン液滴速度の標準偏差
          'main_angle[degrees]' : float
              メイン液滴吐出角度[degrees]
          'satellite_average_velocity[pix/us]' : float
              平均サテライト液滴速度[pix/us]
          'satellite_velocity_varience[pix/us]' : float
              サテライト液滴速度の標準偏差
          'satellite_angle[degrees]' : float
              サテライト液滴吐出角度[degrees]
          'main_linearity_error[pix]' : float
              メイン液滴吐出軌跡の直線フィット結果からの最大ズレ[pix]
          'satellite_linearity_error[pix]' : float
              サテライト液滴吐出軌跡の直線フィット結果からの最大ズレ[pix]
          'most_freq_Y[pix]' : int
              吐出開始前ノズル輪郭の最大頻出Y座標
    '''
    
    out_server_log('auto_tracking without zip file method is called with {} method.'.format(request.method))
    out_server_log('test_dirs are exist as {}'.format(os.listdir('./demo_data')))
    try:
        df = pd.read_csv(RESULTSDB)
        out_server_log('import results from {} was done'.format(RESULTSDB))
    except:
        df = pd.DataFrame(columns = [])
        out_server_log('impot results from {} was FAILED'.format(RESULTSDB))
    DEBUG_MODE = 'DEBUG'
#    print('URL Routing is working')
    directory_path = ''
    exec_mode = ''
    flag_get_argments_is_done = False
    #メソッドがGETである場合
    if request.method == 'GET':
#        print('GET method is working')
        try:
            directory_path = request.args.get('dirpath', type = str)
            camera_resolution = request.args.get('cameraresolution', type = float)
            exec_mode = request.args.get('mode', default='not_DEBUG', type = str)
            flag_get_argments_is_done = True
        except:
            result = {
                'condition' : 'argments were invalid!'
            }
            out_server_log('argments is invalid.')
            
    #メソッドがPOSTである場合
    elif request.method == 'POST':
        try:
            directory_path = str(request.form['dirpath'])
            camera_resolution = float(request.form['cameraresolution'])
            exec_mode = str(request.form['mode'])
            flag_get_argments_is_done = True
        except:
            result = {
                'condition' : 'argments were invalid!'
            }     
            out_server_log('argments is invalid.')

    #argmentsの取得に成功した場合
    if flag_get_argments_is_done:
        #特徴量抽出処理
        directory_path = os.path.join('demo_data', directory_path)
        result = Get_AutoTracking_Results.get_autoTracking_Results(directory_path, camera_resolution, API_VER, exec_mode)
        out_server_log('calculation was done.')
    else:
        retult = {
            'condition' : 'the method is not match'
        }
        
    if flag_get_argments_is_done:
        try:
            resultJS = json.dumps(result)
            try:
                df_add = pd.DataFrame([result])
                try:
                    df = pd.concat([df, df_add], axis = 0)
                    df.to_csv(RESULTSDB, index = False, encoding = 'utf-8-sig')
                    out_server_log('export calculation result to {} was succeed.'.format(RESULTSDB))
                except:
                    out_server_log('export calculation result to {} was FAILED.'.format(RESULTSDB))               
            except:
                out_server_log('read_dataframe was failured.')
        except:
            out_server_log('read result as json was failured.')
    return make_response(jsonify(result)) 
 
methods_test = []

if TEST_MODE:
    print("define routings")
    methods_test = ['GET', 'POST']

@app.route(URLs["auto_tracking with upload file"], methods = methods_test)
@cross_origin(supports_credentials=True)
def upload_file():
    if request.method == 'GET':
        return render_template('upload.html')
    else:
        #ファイル受け取り
        file = request.files['upload_file']
        fileName = file.filename
        files = {'upload_file':(fileName, file, MIMETYPE_ZIP)}
        exec_mode = 'DEBUG' if len(request.form.getlist("debugmode")) != 0 else 'not_DEBUG'
        file_restore = 'RESTORE' if len(request.form.getlist("filerestore")) != 0 else 'DESTROY'
        camera_resolution = float(request.form["camera_resolution"])
        print([fileName, exec_mode, file_restore, camera_resolution])
        payload = {
            "filename": fileName,
            "mode":exec_mode,
            "filerestore":file_restore,
            "camera_resolution":camera_resolution
        }
        response = requests.post(
            url = 'http://localhost:{}/auto_tracking'.format(MAIN_SERVER_PORT),
            data = payload,
            files = files,
            verify=False,
            timeout = 10)
    return make_response(response.json())    
    
@app.route(URLs["show calculation form"], methods=methods_test)
@cross_origin(supports_credentials=True)
def calculation_form(calculationType):
    if request.method == 'GET':
        return render_template('calculator.html',
                               calculationtype=calculationType,
                               arg1 = 10.0,
                               arg2 = 10.0,
                               arg3 = 10.0,
                               arg4 = 10.0,
                               arg5 = 10.0) 
    else:
        get_url = 'http://localhost:{}/calculator/'.format(MAIN_SERVER_PORT)
        if calculationType == 'contactangle_volume':
            thickness = float(request.form['thickness'])
            diameter = float(request.form['diameter'])
            get_url = get_url +calculationType + '?thickness={}&diameter={}'.format(thickness, diameter)
        elif calculationType == 'contactangle_thickness':
            diameter = float(request.form['diameter'])
            firevolume = float(request.form['firevolume'])
            get_url = get_url +calculationType + '?diameter={}&firevolume={}'.format(diameter, firevolume)
        elif calculationType == 'diameter_thickness':
            contact_angle = float(request.form['contactangle'])
            firevolume = float(request.form['firevolume'])
            get_url = get_url +calculationType + '?contactangle={}&firevolume={}'.format(contact_angle, firevolume)
        elif calculationType == 'average_thickness':
            pitchexpression = 'dpi' if len(request.form.getlist("dpi")) != 0 else 'um'
            dotpitchlength = float(request.form['dotpitch'])  
            linepitchlength = float(request.form['linepitch'])
            firevolume = float(request.form['firevolume'])
            numprint = float(request.form['firecycle'])
            concentration = float(request.form['concentration'])
            get_url = get_url + calculationType+'?pitchexpression={}&dotpitch={}&linepitch={}&firevolume={}&firecycle={}&concentration={}'\
            .format(pitchexpression, dotpitchlength, linepitchlength, firevolume, numprint, concentration)
        print(get_url)
        response = requests.get(get_url, verify=False, timeout = 10)
        answer_json = response.json()
        if calculationType == 'contactangle_volume':
            contact_angle = answer_json['contact_angle[degrees]']
            fire_volume = answer_json['fire_volume[pl]']
            ret_html = render_template('calculator.html',
                                       answertype=calculationType,
                                       calculationtype=calculationType,
                                       contact_angle = contact_angle,
                                       fire_volume=fire_volume,
                                       arg1=thickness,
                                       arg2=diameter,
                                      )
        elif calculationType == 'contactangle_thickness':
            contact_angle = answer_json['contact_angle[degrees]']
            thickness = answer_json['thickness[um]']
            ret_html = render_template('calculator.html',
                                       answertype=calculationType,
                                       calculationtype=calculationType,
                                       thickness = thickness,
                                       contact_angle=contact_angle,
                                       arg1=diameter,
                                       arg2=firevolume,
                                      )          
        elif calculationType == 'diameter_thickness':
            diameter = answer_json['diameter[um]']
            thickness = answer_json['thickness[um]']
            ret_html = render_template('calculator.html',
                                       answertype=calculationType,
                                       calculationtype=calculationType,
                                       diameter = diameter,
                                       thickness=thickness,
                                       arg1=contact_angle,
                                       arg2=firevolume,
                                      )
        elif calculationType == 'average_thickness':
            average_thickness = answer_json['thickness_ave[nm]']
            ret_html = render_template('calculator.html',
                                       answertype=calculationType,
                                       calculationtype=calculationType,
                                       ave_thickness=average_thickness,
                                       arg1=dotpitchlength,
                                       arg2=linepitchlength,
                                       arg3=firevolume,
                                       arg4=numprint,
                                       arg5=concentration,
                                      )
    return make_response(ret_html)

@app.route(URLs["download restored files"], methods=methods_test)
@cross_origin(supports_credentials=True)   
def donwload_restored_files():
    '''
    保存ファイルの出力関数
    GET:IDとPW入力画面へ遷移
    POST:入力されたIDとPWを受け取り、結果が正しければ保存ファイルをzipにてまとめて出力し保存。
    '''   
    out_server_log('download restored_files is called with {} method.'.format(request.method))
    if request.method == 'POST':
        ID = str(request.form['ID'])
        PW = str(request.form['PW'])
        flag_destroy = len(request.form.getlist("fileDelete")) != 0
        out_server_log('form was input ID : {},  PW : {}, file Delete : {}'.format(ID, PW, flag_destroy))
        if ID == "microjet" and PW == "microjet_python":
            #ゴミファイルの削除
            for f in os.listdir(RESTORE_DIR):
                if os.path.isfile(f):
                    os.remove(f)
                #RESTORE_DIR内のフォルダ数が0であれば、ダウンロードファイル生成せずに終了
                if len(os.listdir(RESTORE_DIR)) == 0:
                    return make_response('no files are downloadable.')
            downloadFileName = 'restored_files' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.zip'
            #zipファイル生成指示
            shutil.make_archive(downloadFileName.strip('.zip'), 'zip', root_dir=RESTORE_DIR)
            out_server_log('download restored_files with the name "{}" was started.'.format(downloadFileName))
            #zipファイル生成待ち
            waiting_time = 0
            while ((not os.path.exists(downloadFileName)) and waiting_time < 30):
                out_server_log('waiting file creation, waiting time = {}'.format(waiting_time))
                waiting_time = waiting_time + 1
                time.sleep(1)
            flag_file_is_exist = os.path.exists(downloadFileName)
            if flag_file_is_exist:
                out_server_log('zip file creation was done.')
                return_data = io.BytesIO()
                with open(downloadFileName, 'rb') as fo:
                    return_data.write(fo.read())
                    # (after writing, cursor will be at last byte, so move it to start)
                return_data.seek(0)
                if flag_destroy:
                    shutil.rmtree(RESTORE_DIR)
                    os.mkdir(RESTORE_DIR)
                    out_server_log('restored files were destroyed')
                os.remove(downloadFileName)   
                return send_file(return_data, as_attachment = True, \
                                 attachment_filename = downloadFileName, \
                                 mimetype = MIMETYPE_ZIP)
            else:
                out_server_log('zipfile_creation was failed')
                return make_response('zipfile_creation was failed')
        else:
            return make_response(render_template('download_restored.html'))
    else:
        return make_response(render_template('download_restored.html'))
    
@app.route(URLs["download management file"], methods = methods_test)
@cross_origin(supports_credentials=True)
def get_resultFile(fileType):
    out_server_log('download {} file is called with {} method.'.format(fileType, request.method))
    if fileType not in DOWNLOAD_FILE_TYPE:
        return make_response('selected file is not downloadable.')
    dic_download_type = {
        DOWNLOAD_FILE_TYPE[0]:RESULTSDB,
        DOWNLOAD_FILE_TYPE[1]:SERVER_LOG,
        DOWNLOAD_FILE_TYPE[2]:CALCULATION_LOG,
    }
    if request.method == "POST":
        try:
            ID = str(request.form['ID'])
            PW = str(request.form['PW'])
            out_server_log('form was input ID : {},  PW : {}'.format(ID, PW))
            if ID == "microjet" and PW == "microjet_python":
                downloadFileName = os.path.splitext('{}'.format(dic_download_type[fileType]))[0] + datetime.datetime.now().strftime('%Y%m%d%H%M%S') \
                + os.path.splitext('{}'.format(dic_download_type[fileType]))[1]
                downloadFile = dic_download_type[fileType]
                out_server_log('download was started.')
                return send_file(downloadFile, as_attachment = True, \
                                 attachment_filename = downloadFileName, \
                                 mimetype = MIMETYPE_CSV)
            else:
                out_server_log('download was not started.')
                return render_template('index.html')
        except:
            return render_template('index.html')     
    else:
        return make_response(render_template('index.html', filetype=fileType))

@app.route(URLs["analyze_multipleintermittency_firing"], methods = methods_test)
@cross_origin(supports_credentials=True)
def anaylse_intermittency_test():
    if request.method == 'GET':
        file_read_error_result = {
            "analysis_date_time":datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
            "API_VER":API_VER,
            "condition":'upload_file is FAILED.'
        }
        flag_file_extraction_done = False
        results = []
        try:
            print('try get args')
            component_file_name = str(request.args.get('filename'))
            exec_mode = str(request.args.get('mode'))
            flagFileRestore = str(request.args.get('filerestore'))==RESTORE_MODE
            #カメラ解像度受け取り
            try:
                camera_resolution = float(request.form["camera_resolution"])
            except:
                camera_resolution = dic_camera_resolution['NJ-X']
            print('get args is good.')
            if '' == component_file_name:
                our_server_log('uploaded filename was empty.')
                result = {
                    'filename':component_file_name,
                    'condition':'filename was empty.'
                }
                return make_response(jsonify(result))
            if not is_allwed_file(component_file_name):
                out_server_log('extension of uploaded file was not zip.')
                result = ({
                    'filename':component_file_name,
                    'condition':'extension is not zip.'
                })
                return make_response(jsonify(result))
            print([component_file_name, exec_mode, flagFileRestore])

            created_file_path = os.path.join(UPLOAD_DIR, component_file_name)
            print(created_file_path)
            try:
                with zipfile.ZipFile(created_file_path) as existing_zip:
                    out_server_log('extraction uploaded zip file at {}'.format(created_file_path.strip('.zip')))
                    existing_zip.extractall(created_file_path.strip('.zip'))
                created_dir = [f for f in os.listdir(created_file_path.strip('.zip')) if os.path.isdir(os.path.join(created_file_path.strip('.zip'), f))][0]
                parent_directory_path = os.path.join(UPLOAD_DIR, created_dir, created_dir)
                print(parent_directory_path)
                flag_file_extraction_done = True
            except:
                results = [file_read_error_result]
        except:
            print('argments is not good.')
            results = [file_read_error_result]
        if flag_file_extraction_done:
            try:
                df = pd.read_csv(RESULTSDB)
                out_server_log('import results from {} was done'.format(RESULTSDB))
            except:
                df = pd.DataFrame(columns = [])
                out_server_log('impot results from {} was FAILED'.format(RESULTSDB))

            dirs = os.listdir(parent_directory_path)
            print(dirs)
            for _dir in dirs:
                print(_dir)
                _dir = os.path.join(parent_directory_path, _dir)
                print(_dir)
                results.append(Get_AutoTracking_Results.get_autoTracking_Results(_dir, camera_resolution, API_VER, exec_mode))
            df_add = pd.DataFrame(results)
            df = pd.concat([df, df_add], axis = 0)
            df.to_csv(RESULTSDB, index = False, encoding = 'utf-8-sig') 
            
            if not flagFileRestore:
                #生成ファイル処理
                shutil.rmtree(UPLOAD_DIR)
                os.mkdir(UPLOAD_DIR) 
                out_server_log('Both files at {}, and the uploaded zipfile {} were deleted'.format(created_file_path.strip('.zip'), created_file_path))
            else:
                src = created_file_path.strip('.zip')
                dst = os.path.join(RESTORE_DIR, component_file_name.strip('.zip'))
                dst_org = dst
                fileNum = 2
                while os.path.exists(dst):
                    dst = dst_org + '_{}'.format(fileNum)
                    fileNum = fileNum + 1
                shutil.copytree(src, dst)
                out_server_log('files were saved at {}'.format(dst))
                shutil.rmtree(UPLOAD_DIR)
                os.mkdir(UPLOAD_DIR)       
                out_server_log('files at {} and {} were deleted'.format(created_file_path.strip('.zip'), created_file_path))
    
    return make_response(jsonify(results))

@app.route(URLs["analyze_single_delay_image"], methods = methods_test)
@cross_origin(supports_credentials=True)
def analyze_single_delay_images():
    if request.method == 'GET':
        return render_template('upload_double_images.html')
    else:
        #ファイル受け取り
        file_1 = request.files['upload_file_1']
        fileName_1 = file_1.filename
        file_2 = request.files['upload_file_2']
        fileName_2 = file_2.filename
        exec_mode = 'DEBUG' if len(request.form.getlist("debugmode")) != 0 else 'not_DEBUG'
        file_restore = 'RESTORE' if len(request.form.getlist("filerestore")) != 0 else 'DESTROY'
        camera_resolution = float(request.form["camera_resolution"])
        #ファイル保存、UPLOAD_DIR内にzipを出力
        file_1.save(os.path.join(UPLOAD_DIR, fileName_1))
        filepath_1 = os.path.join(UPLOAD_DIR, fileName_1)
        file_2.save(os.path.join(UPLOAD_DIR, fileName_2))
        filepath_2 = os.path.join(UPLOAD_DIR, fileName_2)
        ret_result = Get_AutoTracking_Results.comparison_images(filepath_1, filepath_2, exec_mode)
        if file_restore:
            src = UPLOAD_DIR
            dst = os.path.join(RESTORE_DIR, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
            dst_org = dst
            fileNum = 2
            while os.path.exists(dst):
                dst = dst_org + '_{}'.format(fileNum)
                fileNum = fileNum + 1
            shutil.copytree(src, dst)
        shutil.rmtree(UPLOAD_DIR)
        os.mkdir(UPLOAD_DIR) 
        
        return make_response(jsonify(ret_result))

#アプリ起動指示。pythonにて本ファイルを指定すると以下動く。  
if __name__ == "__main__":
    if NET_MODE:
        print('run with net_mode')
        app.run(debug=True, #flaskサーバーがデバッグモードで動くか否か。
                host='0.0.0.0', #ホスト指定。基本サーバー内部で起動するので、0.0.0.0でOK
                ssl_context=context, #ssl通信の設定。本ファイル冒頭のcontextにて指定。
                port=MAIN_SERVER_PORT, #ポート番号。ローカルデバッグ時は左記。オンライン公開時はssl通信用の443を使用
                threaded=True #並列処理の許可。WSGIサーバーを利用する場合はあまり気にしなくても良い。
               )
    else:
        print('run with local_mode')
        app.run(debug=True, #flaskサーバーがデバッグモードで動くか否か。
                host='0.0.0.0', #ホスト指定。基本サーバー内部で起動するので、0.0.0.0でOK
                #ssl_context=context, #ssl通信の設定。本ファイル冒頭のcontextにて指定。
                port=MAIN_SERVER_PORT, #ポート番号。ローカルデバッグ時は左記。オンライン公開時はssl通信用の443を使用
                threaded=True #並列処理の許可。WSGIサーバーを利用する場合はあまり気にしなくても良い。
               )