from flask import *
import math
import ssl
from flask_cors import CORS, cross_origin
import datetime
import json
import werkzeug
import os
import zipfile
import tempfile
import shutil
import io
import time
import requests

#API内共通変数
API_VER = '0.0.1' #APIコードのバージョン、2020.10.21

UPLOAD_DIR = 'uploads' #アップロードファイル格納ディレクトリ名
ALLOWED_EXTENSIONS = set(['zip']) #許容拡張子
RESULTSDB = 'resultsDB.csv' #計算結果格納csvファイル名
SERVER_LOG = 'server.log' #サーバー処理ログ格納ファイル名

#ルーティングURLの指定用ディクショナリ
URLs = {
    #zipファイル投稿
    "auto_tracking with upload file":'/auto_tracking_upload_file',
    #管理ファイルダウンロード用
    "download management file":"/download_file/<string:fileType>",
    #保存済ファイルダウンロード用
    "download restored files":'/download_restored_files',   
}

MIMETYPE_CSV = 'text/csv' #csvファイル出力MIMETYPE
MIMETYPE_ZIP = 'application/zip' #zipファイル出力MIMETYPE
DOWNLOAD_FILE_TYPE = ['result_csv', 'server_log', 'calculation_log'] #管理ファイルDL時指定キー

DEBUG_MODE = 'DEBUG' #デバッグモード指定文字列
RESTORE_DIR = 'restored_data' #解析結果画像出力時保存ディレクトリ名
CALCULATION_LOG = 'calculation_log.log' #計算処理デバッグ結果格納ファイル名

MAIN_SERVER_PORT = '443'

#appの宣言、Flaskにて起動を指示。
app = Flask(__name__)
#★クロスサイト時に必要な設定
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

@app.route(URLs["auto_tracking with upload file"], methods = ['GET', 'POST'])
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
            files = files)
        return make_response(response.json())
        

# ファイルサイズ上限オーバー時の処理
@app.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
@cross_origin(supports_credentials=True)
def handle_over_max_file_size(error):
    out_server_log('uploaded file size is to large.')
    return 'result : file size is overed.'
     
@app.route("/calculator/form/<string:calculationType>", methods=['GET', 'POST'])
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
        response = requests.get(get_url)
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

@app.route(URLs["download restored files"], methods = ['GET', 'POST'])
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
    
@app.route(URLs["download management file"], methods = ['GET', 'POST'])
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


    
#アプリ起動指示。pythonにて本ファイルを指定すると以下動く。  
if __name__ == "__main__":
    app.run(debug=True, #flaskサーバーがデバッグモードで動くか否か。
            host='0.0.0.0', #ホスト指定。基本サーバー内部で起動するので、0.0.0.0でOK
            ssl_context=context, #ssl通信の設定。本ファイル冒頭のcontextにて指定。
            port=MAIN_SERVER_PORT, #ポート番号。ローカルデバッグ時は左記。オンライン公開時はssl通信用の443を使用
            threaded=True #並列処理の許可。WSGIサーバーを利用する場合はあまり気にしなくても良い。
           )