# -*- coding:utf8 -*-
from aliyun_sms_sdk.aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
from aliyun_sms_sdk.aliyunsdkcore.client import AcsClient
from PAY.wxpay import settings as wx_settings
from oauthlib.common import generate_token
from django.conf import settings
from django.utils.timezone import now
from lxml import etree
import datetime
import qrcode
import json
import os
import uuid
from hashlib import md5, sha1
from barcode import generate
from barcode.writer import ImageWriter
import base64
import random
import time
import uuid

from common.models import AliYunPhoneMessageInformation


def minutes_5_plus():
    return now() + datetime.timedelta(minutes=5)


def minutes_15_plus():
    return now() + datetime.timedelta(minutes=15)


def minutes_30_plus():
    return now() + datetime.timedelta(minutes=30)


def days_7_plus():
    return now() + datetime.timedelta(days=7)


def make_time_delta(days=0, minutes=0, seconds=0):
    """
    设置时间增量
    """
    return now() + datetime.timedelta(days=days,
                                      minutes=minutes,
                                      seconds=seconds)


def make_time_delta_for_custom(date_time, days=0, hours=0, minutes=0, seconds=0):
    """
    设置时间增量
    """
    return date_time + datetime.timedelta(days=days,
                                          hours=hours,
                                          minutes=minutes,
                                          seconds=seconds)


def make_perfect_time_delta(days=0, hours=0, minutes=0, seconds=0):
    """
    设置时间增量
    """
    now_date = datetime.datetime.strftime(now().date(), '%Y-%m-%d %H:%M:%S')
    now_datetime = datetime.datetime.strptime(now_date, '%Y-%m-%d %H:%M:%S')
    return now_datetime + datetime.timedelta(days=days,
                                             hours=hours,
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


QRCODE_PICTURE_PATH = settings.PICTURE_DIRS['consumer']['qrcode']


def make_qrcode(source_data, save_path=QRCODE_PICTURE_PATH, version=5):
    """
    生成二维码图片
    """
    qr = qrcode.QRCode(version=version,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=10,
                       border=4)
    qr.add_data(source_data)
    qr.make(fit=True)
    fname = "%s.png" % make_random_char_and_number_of_string(20)
    fname_path = os.path.join(save_path, fname)

    if not os.path.isdir(save_path):
        os.makedirs(save_path)
    image = qr.make_image()
    image.save(fname_path)
    return fname_path


def make_barcode(save_path=QRCODE_PICTURE_PATH, barcode_length=8):
    """
    生成条形码
    返回：条形码数字及条形码文件名
    """
    source_data = make_random_number_of_string(barcode_length)
    generate_dict = {8: {'name': 'EAN8',
                         'width': 0.96},
                     13: {'name': 'EAN13',
                          'width': 0.66}
                     }
    fname = '%s.png' % make_random_char_and_number_of_string(20)
    fname_path = os.path.join(save_path, fname)
    if not os.path.isdir(save_path):
        os.makedirs(save_path)
    fp = open(fname_path, 'wb')
    writer = ImageWriter()
    generate_name = generate_dict[barcode_length]['name']
    width = generate_dict[barcode_length]['width']
    generate(generate_name, source_data, writer=writer, output=fp,
             writer_options={'module_width': width,
                             'module_height': 30})
    fp.close()

    return writer.text, fname_path


def make_static_url_by_file_path(file_path):
    path_list = file_path.split('static/', 1)
    return os.path.join(settings.WEB_URL_FIX, 'static', path_list[1])


def anaysize_xml_to_dict(source):
    """
    解析xml字符串
    """
    root = etree.fromstring(source)
    result = {article.tag: article.text for article in root}
    return result


def make_dict_to_xml(source_dict, use_cdata=True):
    """
    生成xml字符串
    """
    if not isinstance(source_dict, dict):
        raise ValueError('Parameter must be dict.')

    xml = etree.Element('xml')
    for _key, _value in source_dict.items():
        _key_xml = etree.SubElement(xml, _key)
        if _key == 'detail':
            _key_xml.text = etree.CDATA(_value)
        else:
            if not isinstance(_value, (bytes, unicode)):
                _value = unicode(_value)
            if use_cdata:
                _key_xml.text = etree.CDATA(_value)
            else:
                _key_xml.text = _value

    xml_string = etree.tostring(xml,
                                pretty_print=True,
                                encoding="UTF-8",
                                method="xml",
                                xml_declaration=True,
                                standalone=None)
    return xml_string.split('\n', 1)[1]


def make_perfect_sign_string(source_dict):
    """
    对字典key进行排序，并生成"&"字符连接的字符串
    :param source_dict:
    :return:
    """
    key_list = []
    for _key in source_dict:
        if not source_dict[_key] or _key == 'sign':
            continue
        key_list.append({'key': _key, 'value': source_dict[_key]})
    key_list.sort(key=lambda x: x['key'])

    string_param = ''
    for item in key_list:
        string_param += '%s=%s&' % (item['key'], item['value'])
    return string_param[:-1]


def make_sign_for_wxpay(source_dict):
    """
    生成签名（微信支付）
    """
    string_param = make_perfect_sign_string(source_dict)
    # 把密钥和其它参数组合起来
    string_param += '&key=%s' % wx_settings.KEY
    md5_string = md5(string_param.encode('utf8')).hexdigest()
    return md5_string.upper()


def make_sign_base(source_dict, sign_type='md5'):
    """
    对字典key进行排序，并签名
    :param source_dict
    :param sign_type:
    :return:
    """
    sign_string = make_perfect_sign_string(source_dict)
    if sign_type.lower() == 'md5':
        return md5(sign_string.encode('utf8')).hexdigest()
    elif sign_type.lower() == 'sha1':
        return sha1(sign_string.encode('utf8')).hexdigest()
    else:
        return md5(sign_string.encode('utf8')).hexdigest()


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
    return generate_token(length=str_length)


def get_time_stamp():
    stamp = str(time.time()).split('.')[0]
    return stamp


def send_message_to_phone(params, receive_phones, template_name=None):
    """
    使用阿里云的短信服务发送短信
    """
    from horizon.http_requests import send_http_request
    import urllib

    url = 'http://sms.market.alicloudapi.com/singleSendSms'
    AppCode = '2e8a1a8a3e22486b9be6ac46c3d2c6ec'
    # Access Key ID
    access_id = 'LTAIr9xuJ6xt2UKa'
    # Access Key Secret
    access_secret = '8XyKngzCRxVzJITc2I85L3LupaLzrS'
    region = "cn-hangzhou"
    sign_names = '吟食'
    template_dict = {'recharge': 'SMS_123290665',
                     'register': 'SMS_123290666',
                     'recharge_give_gift': 'SMS_123671510'}
    params_key_dict = {'register': 'code',
                       'recharge': 'count',
                       'recharge_give_gift': 'code'}

    if not template_name:
        template = template_dict['register']
    else:
        if template_name not in template_dict.keys():
            return ValueError('Params template incorrect')
        template = template_dict[template_name]
    if isinstance(params, (str, unicode, int, float)):
        if isinstance(params, (float, int)):
            params_dict = {params_key_dict[template_name]: '%.2f' % params}
        else:
            params_dict = {params_key_dict[template_name]: params}
        params_query = json.dumps(params_dict)
    elif isinstance(params, dict):
        params_query = json.dumps(params)
    elif isinstance(params, (tuple, list)):
        params_dict = dict(zip(params_key_dict[template_name], params))
        params_query = json.dumps(params_dict)
    else:
        return TypeError('params must be unicode or dictionary')

    if isinstance(receive_phones, (str, unicode)):
        receive_phones = [receive_phones]
    else:
        if not isinstance(receive_phones, (tuple, list)):
            return TypeError('receive phones type must be list or tuple')

    _business_id = uuid.uuid1()
    return send_sms(_business_id, ''.join(receive_phones), sign_names, template, params_query)
    # query = {'RecNum': ','.join(receive_phones),
    #          'TemplateCode': template,
    #          'SignName': sign_names[0]}
    # query_str = '%s&ParamString=%s' % (urllib.urlencode(query), params_query)
    #
    # return send_http_request(url, query_str, add_header={'Authorization': 'APPCODE %s' % AppCode})


Aliyun_Message_Information = AliYunPhoneMessageInformation.get_object()
ACCESS_ID = Aliyun_Message_Information.access_id
ACCESS_SECRET = Aliyun_Message_Information.access_secret
REGION = Aliyun_Message_Information.region


def send_sms(business_id, phone_number, sign_name, template_code, template_param=None):
    """
    阿里云短信服务：发送短信官方函数
    :param business_id:
    :param phone_number:
    :param sign_name:
    :param template_code:
    :param template_param:
    :return:
    """
    smsRequest = SendSmsRequest.SendSmsRequest()
    # 申请的短信模板编码,必填
    smsRequest.set_TemplateCode(template_code)
    # 短信模板变量参数,友情提示:如果JSON中需要带换行符,请参照标准的JSON协议对换行符的要求,
    # 比如短信内容中包含\r\n的情况在JSON中需要表示成\\r\\n,否则会导致JSON在服务端解析失败
    if template_param is not None:
        smsRequest.set_TemplateParam(template_param)
    # 设置业务请求流水号，必填。
    smsRequest.set_OutId(business_id)
    # 短信签名
    smsRequest.set_SignName(sign_name)
    # 短信发送的号码，必填。支持以逗号分隔的形式进行批量调用，批量上限为1000个手机号码,
    # 批量调用相对于单条调用及时性稍有延迟,验证码类型的短信推荐使用单条调用的方式
    smsRequest.set_PhoneNumbers(phone_number)
    # 发送请求
    acs_client = AcsClient(ACCESS_ID, ACCESS_SECRET, REGION)
    smsResponse = acs_client.do_action_with_exception(smsRequest)
    return smsResponse
