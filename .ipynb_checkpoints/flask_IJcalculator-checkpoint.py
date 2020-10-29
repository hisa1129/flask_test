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

#API内共通変数
API_VER = '0.0.0' #APIコードのバージョン、2020.10.21

UPLOAD_DIR = 'uploads' #アップロードファイル格納ディレクトリ名
ALLOWED_EXTENSIONS = set(['zip']) #許容拡張子
RESULTSDB = 'resultsDB.csv' #計算結果格納csvファイル名
SERVER_LOG = 'server.log' #サーバー処理ログ格納ファイル名

#ルーティングURLの指定用ディクショナリ
URLs = {
    #自動追尾機能
    "auto_tracking":'/auto_tracking',
    #zipファイル投稿
    "auto_tracking with upload file":'/auto_tracking_upload_file',
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
}

MIMETYPE_CSV = 'text/csv' #csvファイル出力MIMETYPE
MIMETYPE_ZIP = 'application/zip' #zipファイル出力MIMETYPE

DEBUG_MODE = 'DEBUG' #デバッグモード指定文字列
RESTORE_DIR = 'restored_data' #解析結果画像出力時保存ディレクトリ名
CALCULATION_LOG = 'calculation_log.log' #計算処理デバッグ結果格納ファイル名

#装置毎のカメラ解像度、[um/pix]
dic_camera_resolution = {
    'LJ-600':3.50,
    'NJ-X':3.50,
    'Jet-Tester':3.50,
}

#appの宣言、Flaskにて起動を指示。
app = Flask(__name__)
#★クロスサイト時に必要な設定
#CORS(app, support_credentials=True)
#context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
#context.load_cert_chain('cert.crt', 'server_secret.key')

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
@app.route(URLs["auto_tracking"], methods=['GET', 'POST'])
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
        out_server_log('{} file is posted'.format(request.files))
        # request.files内にuploadFile要素が無い場合
        if 'upload_file' not in request.files:
            our_server_log('file was empty')
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
        flagFileRestore = str(request.form["filerestore"]) == 'RESTORE'
        #デバッグモード指示受け取り
        exec_mode = str(request.form["mode"])
        #カメラ解像度受け取り
        camera_resolution = float(request.form["camera_resolution"])
    else:
        uploaded_file_name = request.args.get('filename', default='')
        uploaded_files = [f for f in os.listdir(UPLOAD_DIR) if f == uploaded_file_name]
        if len(uploaded_files) != 1:
            out_server_log('file upload was FAILED')
            result.update({
                'condition': 'file upload was FAILED'
            })
            return make_response(jsonify(result))
        fileName = uploaded_files[0]
        flagFileRestore = str(request.args.get('filerestore', default='not_RESTORE')) == 'RESTORE'
        exec_mode = DEBUG_MODE if request.args.get('mode', default='node_DEBUG') == DEBUG_MODE else 'NOT_DEBUG_MODE'
        camera_resolution = float(request.args.get('cameraresolution', default=3.50, type=float))
        out_server_log('{} file is going to be analysed.'.format(fileName))
    
    if '' == fileName:
        our_server_log('uploaded filename was empty.')
        result.update({
            'filename':fileName,
            'condition':'filename was empty.'
        })
        return make_response(jsonify(result))
    if not is_allwed_file(fileName):
        out_server_log('extension of uploaded file was not zip.')
        result.update({
            'filename':fileName,
            'condition':'extension is not zip.'
        })
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

@app.route(URLs["calculation contactangle and thickness"], methods=['GET', 'POST'])
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
    
@app.route(URLs["calculation diameter and thickness"], methods=['GET', 'POST'])
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
   
@app.route(URLs["auto_tracking_demo"], methods = ['GET', 'POST'])
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
           
#アプリ起動指示。pythonにて本ファイルを指定すると以下動く。  
if __name__ == "__main__":
    app.run(debug=True, #flaskサーバーがデバッグモードで動くか否か。
            host='0.0.0.0', #ホスト指定。基本サーバー内部で起動するので、0.0.0.0でOK
            #ssl_context=context, #ssl通信の設定。本ファイル冒頭のcontextにて指定。
            port=8080, #ポート番号。ローカルデバッグ時は左記。オンライン公開時はssl通信用の443を使用
            threaded=True #並列処理の許可。WSGIサーバーを利用する場合はあまり気にしなくても良い。
           )