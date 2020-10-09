from flask import *
import math
import ssl

import Get_AutoTracking_Results
from flask_cors import CORS, cross_origin
import pandas as pd
import numpy as np
import datetime

app = Flask(__name__)

CORS(app, support_credentials=True) # ■■■ ,の右部分
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain('cert.crt', 'server_secret.key')

@app.route("/calculator/contactangle_volume", methods=['GET','POST'])
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
    #メソッド別パラメータ取得、POSTメソッド
    if request.method == 'POST':
        try:
            thickness = float(request.form['thickness'])
            diameter = float(request.form['diameter'])
            flag_argments_are_good = True
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make both thickness and diameter positive, and both the value types float'

            }
    
    #メソッド別パラメータ取得、GETメソッド
    elif request.method == 'GET':
        try:
            thickness = float(request.args.get('thickness'))
            diameter = float(request.args.get('diameter'))
            flag_argments_are_good = True
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make both thickness and diameter positive, and both the value types float'
            }         
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
    
    #パラメータ取得時の計算
    if flag_argments_are_good:         
        radius = thickness/2.0
        firevolume = math.pi / 6.0 * thickness * ((radius ** 2) * 3.0 + thickness ** 2) / 1000.0
        contactangle = math.degrees(math.atan(thickness / radius))
        result = {
            'contact_angle[degrees]':contactangle,
            'fire_volume[pl]':firevolume
        }
    
    return result    

@app.route("/calculator/contactangle_thickness", methods=['GET', 'POST'])
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
    
    flag_argments_are_good = False
    diameter = 0.0
    firevolume = 0.0
    if request.method == 'POST':
        try:
            diameter = float(request.form['diameter'])
            firevolume = float(request.form['firevolume'])
            flag_argments_are_good = True
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make both diameter and firevolume positive, and both the value types float'

            }
    elif request.method == 'GET':
        try:
            diameter = float(request.args.get('diameter'))
            firevolume = float(request.args.get('firevolume'))
            flag_argments_are_good = True
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make both diameter and firevolume positive, and both the value types float'
            }
    
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

    return result
    
@app.route("/calculator/diameter_thickness", methods=['GET', 'POST'])
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
    flag_argments_are_good = False
    contactangle = 0.0
    firevolume=0.0

    if request.method == 'POST':
        try:
            contactangle = float(request.form['contactangle'])
            firevolume = float(request.form['firevolume'])
            flag_argments_are_good = True            
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make both contactangle and firevolume positive, and both the value types float'

            }
    elif request.method == 'GET':
        try:
            contactangle = float(request.args.get('contactangle'))
            firevolume = float(request.args.get('firevolume'))
            flag_argments_are_good = True            
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make both contactangle and firevolume positive, and both the value types float'
            }
            
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
    
    if firevolume <= 0:
        flag_argments_are_good = False
        result = {
            'condition' : 'firevolume must be positive value',                        
            'correspondence' : 'make firevolume value positive.'
        }
                               
                               
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
    
    return result

@app.route("/calculator/avethickness/", methods=['GET', 'GET'])
@cross_origin(supports_credentials=True)
def calculate_averagethickness():
    '''
    ・機能：印刷メッシュ、液滴サイズ、固形分濃度と繰り返し回数から平均膜厚を計算
　　・URL：http://192.168.1.44:8080/calculator/avethickness/
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
            numprint = float(request.args.get('printcount'))
            concentration = float(request.args.get('concentration'))
            flag_argments_are_good = True
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make all the argment types except pitchexpression float, and all the values positive. the type of pitchexpression should be string.'
            }
    elif request.method == 'POST':
        try:
            flagDPI = (str(request.form['pitchexpression']) == 'dpi')
            dotpitchlength = float(request.form['dotpitch'])
            linepitchlength = float(request.form['linepitch'])
            firevolume = float(request.form['firevolume'])
            numprint = float(request.form['printcount'])
            concentration = float(request.form['concentration'])
            flag_argments_are_good = True
        except:
            result = {
                'condition' : 'argments were invalid!',
                'correspondence' : 'make all the argment types except pitchexpression float, and all the values positive. the type of pitchexpression should be string.'
            }
    else:
        retult = {
            'condition' : 'the method is bad'
        }
    
    if dotpitchlength <= 0 or linepitchlength <= 0 or firevolume <= 0 or numprint < 0 or concentration < 0:
        result = {
            'condition' : 'argments were invalid! all the values must be positive values',            
            'correspondence' : 'make all the values positive.'
        }
                               
    if flag_argments_are_good:
        dotpitchlength = 25400.0 / dotpitchlength if flagDPI else dotpitchlength
        linepitchlength = 25400.0 / linepitchlength if flagDPI else linepitchlength
        thickness_ave = firevolume * numprint * concentration * 10000.0 / dotpitchlength / linepitchlength
        result = {
            'thickness_ave[nm]':thickness_ave
        }
        
    return result

@app.route("/auto_tracking", methods = ['GET', 'POST'])
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
            exec_mode = request.args.get('mode', default='not_DEBUG', type = str)
            flag_get_argments_is_done = True
        except:
            result = {
                'condition' : 'argments were invalid!'
            }
    #メソッドがPOSTである場合
    elif request.method == 'POST':
        try:
            directory_path = str(request.form['dirpath'])
            exec_mode = str(request.form['mode'])
            flag_get_argments_is_done = True
        except:
            result = {
                'condition' : 'argments were invalid!'
            }     
    #argmentsの取得に成功した場合
    if flag_get_argments_is_done:
        #特徴量抽出処理
        result = Get_AutoTracking_Results.get_autoTracking_Results(directory_path, exec_mode)
    else:
        retult = {
            'condition' : 'the method is not match'
        }
    
    return result
    
if __name__ == "__main__":
    
    app.run(debug=False, host='0.0.0.0', ssl_context=context, port=443, threaded=True)