import datetime

#ログ出力ファイルの指定
CALCULATION_LOG = 'calculation_log.log'

def calculation_log(sentence):
    '''
    計算ログ出力関数
    
    '''
    time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = CALCULATION_LOG
    with open(filepath, mode = 'a') as f:
        f.write('{} : {}\r\n'.format(time, sentence))
    return