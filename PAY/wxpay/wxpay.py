#-*- coding:utf8 -*-

import requests
from PAY.wxpay import settings as wx_settings
from django.conf import settings as app_settings
import uuid
from hashlib import md5
from lxml import etree


FIELDS = ('appid',              # 公众账号ID
          'mch_id',             # 商户号
          'device_info',        # 设备号
          'nonce_str',          # 随机字符串
          'sign',               # 签名
          'sign_type',          # 签名类型
          'body',               # 商品描述
          'detail',             # 商品详情
          'attach',             # 附加数据
          'out_trade_no',       # 商户订单号
          'fee_type',           # 标价币种
          'total_fee',          # 标价金额
          'spbill_create_ip',   # 终端IP
          'time_start',         # 交易起始时间
          'time_expire',        # 交易结束时间
          'goods_tag',          # 订单优惠标记
          'notify_url',         # 通知地址
          'trade_type',         # 交易类型
          'product_id',         # 商品ID
          'limit_pay',          # 指定支付方式
          'openid',             # 用户标识
          )


class WXPAYUnifiedOrder(object):
    """
    统一下单支付模式（微信支付入口  注：除了刷卡支付，刷卡支付有单独的支付入口）
    """
    def __init__(self, body=None, out_trade_no=None, total_fee=None,
                 trade_type=None, notify_url=None, **kwargs):
        if not (body and out_trade_no and total_fee and trade_type and notify_url):
            raise ValueError('fields [body, out_trade_no, total_fee, trade_type, notify_url] '
                             'must be not empty!')
        if trade_type not in wx_settings.TRADE_TYPE.values():
            raise ValueError('Fields trade_type is incorrect')

        self.appid = wx_settings.APPID
        self.mch_id = wx_settings.MCH_ID
        self.body = body                        # 商品描述
        self.out_trade_no = out_trade_no        # 商户订单号
        self.total_fee = total_fee              # 交易金额（单位：分，字段类型：整数）
        self.trade_type = trade_type            # 交易类型为：NATIVE, JSAPI 或 APP
        self.spbill_create_ip = wx_settings.SPBILL_CREATE_IP      # 终端IP
        self.notify_url = notify_url              # 回调地址
        self.nonce_str = get_nonce_string()                   # 随机字符串
        self.sign_type = wx_settings.SIGN_TYPE    # 签名类型

        for _key in kwargs:
            if kwargs[_key] and _key in FIELDS:
                setattr(self, _key, kwargs[_key])

        self.sign = self.make_sign()                          # 签名

    def make_sign(self):
        """
        生成签名
        """
        key_list = []
        for _key in self.__dict__:
            if getattr(self, _key):
                key_list.append({'key': _key, 'value': getattr(self, _key)})
        key_list.sort(key=lambda x: x['key'])

        string_param = ''
        for item in key_list:
            string_param += '%s=%s&' % (item['key'], item['value'])
        # 把密钥和其它参数组合起来
        string_param += 'key=%s' % wx_settings.KEY
        md5_string = md5(string_param.encode('utf8')).hexdigest()
        return md5_string.upper()

    @property
    def xml(self):
        xml = etree.Element('xml')
        for _key in self.__dict__:
            if getattr(self, _key):
                _key_xml = etree.SubElement(xml, _key)
                if _key == 'detail':
                    _key_xml.text = etree.CDATA(getattr(self, _key))
                else:
                    attr = getattr(self, _key)
                    if not isinstance(attr, (bytes, unicode)):
                        attr = unicode(attr)
                    _key_xml.text = attr

        xml_string = etree.tostring(xml,
                                    pretty_print=True,
                                    encoding="UTF-8",
                                    method="xml",
                                    xml_declaration=True,
                                    standalone=None)
        return xml_string.split('\n', 1)[1]

    def go_to_pay(self):
        headers = {'Content-Type': 'text/xml; charset=UTF-8'}
        results = requests.post(wx_settings.UNIFIED_ORDER_URL,
                                data=self.xml,
                                headers=headers)
        return results


def get_nonce_string():
    """
    生成长度不超过32位的随机数字符串
    """
    uuid_string = str(uuid.uuid1())
    uuid_string = ''.join(uuid_string.split('-'))
    return uuid_string[:32]


class WXPAYJsApi(WXPAYUnifiedOrder):
    def __init__(self, body=None, out_trade_no=None, total_fee=None, openid=None, **kwargs):
        if not (body and out_trade_no and total_fee and openid):
            raise ValueError('fields [body, out_trade_no, total_fee, openid] must be not empty!')

        kwargs['openid'] = openid
        super(WXPAYJsApi, self).__init__(body=body,
                                         out_trade_no=out_trade_no,
                                         total_fee=total_fee,
                                         trade_type=wx_settings.TRADE_TYPE['js'],
                                         notify_url=wx_settings.NOTIFY_URL_DICT['JSAPI'],
                                         **kwargs)


class WXPAYApp(WXPAYUnifiedOrder):
    def __init__(self, body=None, out_trade_no=None, total_fee=None, **kwargs):
        if not (body and out_trade_no and total_fee):
            raise ValueError('fields [body, out_trade_no, total_fee] must be not empty!')
        super(WXPAYApp, self).__init__(body=body,
                                       out_trade_no=out_trade_no,
                                       total_fee=total_fee,
                                       trade_type=wx_settings.TRADE_TYPE['js'],
                                       notify_url=wx_settings.NOTIFY_URL_DICT['APP'],
                                       **kwargs)
