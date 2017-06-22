# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now


class WXPayResult(models.Model):
    """
    微信支付结果信息
    """
    orders_id = models.CharField('订单ID', max_length=32, db_index=True, unique=True)

    result_code = models.CharField('支付结果', max_length=16, null=True)
    err_code = models.CharField('错误代码', max_length=32, null=True)
    err_code_des = models.CharField('错误代码描述', max_length=128, null=True)
    openid = models.CharField('用户标识', max_length=128, null=True)
    is_subscribe = models.CharField('是否关注公众号', max_length=1, null=True)
    trade_type = models.CharField('交易类型', max_length=16, null=True)
    bank_type = models.CharField('付款银行', max_length=16, null=True)
    total_fee = models.IntegerField('订单金额', null=True)   # 单位为分
    settlement_total_fee = models.IntegerField('应结订单金额', null=True)  # 单位为分
    cash_fee = models.IntegerField('现金支付金额', null=True)   # 单位为分
    transaction_id = models.CharField('微信支付订单号', max_length=32, unique=True, null=True)
    attach = models.CharField('商家数据包（原样返回）', max_length=128, null=True)
    time_end = models.CharField('支付完成时间', max_length=14, null=True)

    request_data = models.TextField('调用微信支付时传过去的数据（数据格式：json类型的dict）')
    created = models.DateTimeField('记录创建时间', default=now)
    extend = models.TextField('扩展信息', null=True)

    class Meta:
        db_table = 'ys_wxpay'

    def __unicode__(self):
        return self.orders_id

    @classmethod
    def get_object_by_orders_id(cls, orders_id):
        try:
            return cls.objects.get(orders_id=orders_id)
        except cls.DoesNotExist as e:
            return Exception(e)

