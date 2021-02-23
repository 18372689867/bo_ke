from ddblog.celery import app
from tools.sms import YunTongXin


@app.task
def send_sms(phone, code):
    # 一般情况下，写到配置文件中
    aid = '8a216da87380115d017389546bb802f5'
    atoken = '12444d5592d247b2af0e5cc10bf666a0'
    appid = '8a216da87380115d017389546c9e02fb'
    tid = '1'

    # 1 创建云通信对象
    x = YunTongXin(aid, atoken, appid, tid)
    # 2 发送短信
    res = x.run(phone, code)
    # 3 返回信息
    print(res)
