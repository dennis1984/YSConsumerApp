#-*- coding:utf8 -*-
# from PAY.wxpay import settings as wx_settings
# from PAY.alipay import settings as ali_settings
from django.conf import settings
from django.utils.timezone import now
from lxml import etree
import datetime
import qrcode
import json
import os
import uuid
from hashlib import md5
import base64
import random

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256


def minutes_15_plus():
    return now() + datetime.timedelta(minutes=15)


def minutes_30_plus():
    return now() + datetime.timedelta(minutes=30)


def make_time_delta(days=0, minutes=0, seconds=0):
    """
    设置时间增量
    """
    return now() + datetime.timedelta(days=days,
                                      minutes=minutes,
                                      seconds=seconds)


class DatetimeEncode(json.JSONEncoder):
    """
    让json模块可以序列化datetime类型的字段
    """
    def default(self, o):
        from django.db.models.fields.files import ImageFieldFile

        if isinstance(o, datetime.datetime):
            return str(o)
        elif isinstance(o, ImageFieldFile):
            return str(o)
        else:
            return json.JSONEncoder.default(self, o)


def timezoneStringTostring(timezone_string):
    """
    rest framework用JSONRender方法格式化datetime.datetime格式的数据时，
    生成数据样式为：2017-05-19T09:40:37.227692Z 或 2017-05-19T09:40:37Z
    此方法将数据样式改为："2017-05-19 09:40:37"，
    返回类型：string
    """
    if not isinstance(timezone_string, (str, unicode)):
        return ""
    if not timezone_string:
        return ""
    timezone_string = timezone_string.split('.')[0]
    timezone_string = timezone_string.split('Z')[0]
    try:
        timezone = datetime.datetime.strptime(timezone_string, '%Y-%m-%dT%H:%M:%S')
    except:
        return ""
    return str(timezone)


def make_qrcode(source_data, version=5):
    """
    生成二维码图片
    """
    qr = qrcode.QRCode(version=version,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=10,
                       border=4)
    qr.add_data(source_data)
    qr.make(fit=True)
    fname = "%s.png" % uuid.uuid4()
    qrcode_dir = settings.PICTURE_DIRS['qrcode']
    fname_path = os.path.join(qrcode_dir, fname)

    if not os.path.isdir(qrcode_dir):
        os.makedirs(qrcode_dir)
    image = qr.make_image()
    image.save(fname_path)
    return fname_path


def anaysize_xml_to_dict(source):
    """
    解析xml字符串
    """
    root = etree.fromstring(source)
    result = {article.tag: article.text for article in root}
    return result

#
# def make_dict_to_xml(source_dict, use_cdata=True):
#     """
#     生成xml字符串
#     """
#     if not isinstance(source_dict, dict):
#         raise ValueError('Parameter must be dict.')
#
#     xml = etree.Element('xml')
#     for _key, _value in source_dict.items():
#         _key_xml = etree.SubElement(xml, _key)
#         if _key == 'detail':
#             _key_xml.text = etree.CDATA(_value)
#         else:
#             if not isinstance(_value, (bytes, unicode)):
#                 _value = unicode(_value)
#             if use_cdata:
#                 _key_xml.text = etree.CDATA(_value)
#             else:
#                 _key_xml.text = _value
#
#     xml_string = etree.tostring(xml,
#                                 pretty_print=True,
#                                 encoding="UTF-8",
#                                 method="xml",
#                                 xml_declaration=True,
#                                 standalone=None)
#     return xml_string.split('\n', 1)[1]


# def make_sign_for_wxpay(source_dict):
#     """
#     生成签名（微信支付）
#     """
#     key_list = []
#     for _key in source_dict:
#         if not source_dict[_key] or _key == 'sign':
#             continue
#         key_list.append({'key': _key, 'value': source_dict[_key]})
#     key_list.sort(key=lambda x: x['key'])
#
#     string_param = ''
#     for item in key_list:
#         string_param += '%s=%s&' % (item['key'], item['value'])
#         # 把密钥和其它参数组合起来
#     string_param += 'key=%s' % wx_settings.KEY
#     md5_string = md5(string_param.encode('utf8')).hexdigest()
#     return md5_string.upper()
#
#
# def verify_sign_for_alipay(params_str, source_sign):
#     """
#     支付宝支付验证签名（公钥验证签名）
#     """
#     pub_key = RSA.importKey(open(ali_settings.ALI_PUBLIC_KEY_FILE_PATH))
#     source_sign = base64.b64decode(source_sign)
#     _sign = SHA256.new(params_str)
#     verifer = PKCS1_v1_5.new(pub_key)
#     return verifer.verify(_sign, source_sign)


def make_dict_to_verify_string(params_dict):
    """
    将参数字典转换成待签名的字符串
    """
    params_list = []
    for key, value in params_dict.items():
        if not value or key == 'sign':
            continue
        params_list.append({'key': key, 'value': value})
    params_list.sort(key=lambda x: x['key'])
    params_strs = []
    for item in params_list:
        params_strs.append('%s=%s' % (item['key'], (item['value']).encode('utf8')))
    return '&'.join(params_strs)


def make_random_number_of_string(str_length=6):
    """
    生成数字型的随机字符串（最大长度：128位）
    """
    if str_length > 128:
        str_length = 128
    random_str = _random_str = str(random.random()).split('.')[1]
    for i in range(str_length / len(_random_str)):
        random_str += str(random.random()).split('.')[1]
    index_start = random.randint(0, len(random_str) - str_length)
    return random_str[index_start: index_start + str_length]


def make_random_char_and_number_of_string(str_length=32):
    """
    生成英文字符和数字混合型的字符串（最大长度：128位）
    """
    if str_length > 128:
        str_length = 128
    random_str = _random_str = ''.join(str(uuid.uuid4()).split('-'))
    for i in range(str_length / len(_random_str)):
        random_str += ''.join(str(uuid.uuid4()).split('-'))
    index_start = random.randint(0, len(random_str) - str_length)
    return random_str[index_start: index_start + str_length]


def send_identifying_code_to_phone(params, receive_phones, template):
    """
    使用阿里云的短信服务发送短信
    """
    from horizon.http_requests import send_http_request
    import urllib
    url = 'http://sms.market.alicloudapi.com/singleSendSms'
    AppCode = '2e8a1a8a3e22486b9be6ac46c3d2c6ec	'

    if isinstance(params, basestring):
        params_query = params
    elif isinstance(params, dict):
        params_query = urllib.quote(json.dumps(params))
    else:
        return TypeError('params must be unicode or dictionary')

    if not isinstance(receive_phones, (tuple, list)):
        return TypeError('receive phones type must be list or tuple')

    query = {'ParamString': params_query,
             'RecNum': ','.join(receive_phones),
             'TemplateCode': template}

    return send_http_request(url, query, add_header={'Authorization:': 'APPCODE %s' % AppCode})
