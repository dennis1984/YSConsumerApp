# -*- coding:utf8 -*-
from orders.models import PayOrders, ConsumeOrders
from wallet.models import WalletAction


class WalletPay(object):
    """
    钱包支付
    """
    def __init__(self, request, orders_instance):
        if not isinstance(orders_instance, PayOrders):
            raise TypeError('orders_instance must be PayOrders instance')
        self.request = request
        self.orders = orders_instance

    def is_valid(self):
        if self.orders.is_expired:
            return False
        if not self.orders.is_payable:
            return False
        if self.orders.is_recharge_orders:
            return False
        if self.request.user.id != self.orders.user_id:
            return False
        return True

    def go_to_pay(self):
        if not self.is_valid():
            return ValueError('Orders data is incorrect')
        result = WalletAction().consume(self.request, self.orders)
        return result
