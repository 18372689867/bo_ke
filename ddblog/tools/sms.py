import datetime
import hashlib
import base64
import json

import requests  # 使用该库发送请求


class YunTongXin():
    base_url = 'https://app.cloopen.com:8883'

    def __init__(self, accountSid, accountToken, appId, templateId):
        self.accountSid = accountSid
        self.accountToken = accountToken
        self.appId = appId
        self.templateId = templateId

    # 1 构造url
    def get_request_url(self, sig):
        self.url = self.base_url + '/2013-12-26/Accounts/%s/SMS/TemplateSMS?sig=%s' % (self.accountSid,
                                                                                       sig)
        return self.url

    # 生成时间戳
    def get_timestamp(self):
        now = datetime.datetime.now()
        now_str = now.strftime("%Y%m%d%H%M%S")
        return now_str

    # 计算sig
    def get_sig(self, timestamp):
        data = self.accountSid + self.accountToken + timestamp
        md5 = hashlib.md5()
        md5.update(data.encode())
        hash_value = md5.hexdigest()
        return hash_value.upper()

    # 2 构造请求头
    def get_request_header(self, timestamp):
        data = self.accountSid + ':' + timestamp
        # base64编码
        data_bs = base64.b64encode(data.encode())
        data_bs = data_bs.decode()
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=utf-8',
            'Authorization': data_bs
        }

    # 3 构造请求体
    def get_request_body(self, phone, code):
        data = {
            'to': phone,
            'appId': self.appId,
            'templateId': self.templateId,
            'datas': [code, '3']
        }
        return data

    # 4 发送请求
    def do_request(self, url, header, body):
        res = requests.post(url, headers=header,
                            data=json.dumps(body))
        return res.text

    # 5 封装以上所有步骤
    def run(self, phone, code):
        # 1 构建url
        timestamp = self.get_timestamp()
        sig = self.get_sig(timestamp)
        url = self.get_request_url(sig)
        # 2 构建header
        header = self.get_request_header(timestamp)
        # 3 构建body
        body = self.get_request_body(phone, code)
        # 4 发送请求
        res = self.do_request(url, header, body)
        return res


if __name__ == '__main__':
    aid = '8a216da87380115d017389546bb802f5'
    atoken = '12444d5592d247b2af0e5cc10bf666a0'
    appid = '8a216da87380115d017389546c9e02fb'
    tid = '1'

    # 1 创建云通信对象
    x = YunTongXin(aid, atoken, appid, tid)
    # 2 发送短信
    res = x.run('13426018419', '123456')
    # 3 打印返回信息
    print(res)
