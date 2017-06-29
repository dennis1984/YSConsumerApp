# -*- encoding: utf-8 -*-
from horizon import forms
from django.conf import settings


class DishesIdForm(forms.Form):
    dishes_id = forms.IntegerField(min_value=1,
                                   error_messages={
                                       'required': u'菜品ID不能为空'
                                   })


class DishesCountForm(forms.Form):
    count = forms.IntegerField(min_value=1,
                               error_messages={
                                   'required': u'菜品数量不能为空'
                               })


class ShoppingCartCreateForm(DishesIdForm, DishesCountForm):
    """
    添加新的菜品，放入到购物车中
    """


class ShoppingCartUpdateForm(DishesIdForm, DishesCountForm):
    """
    更新购物车中某个菜品的数量
    """
    # method = forms.ChoiceField(choices=(('add', 1), ('sub', 2)),
    #                            error_messages={
    #                                'required': u'更新菜品数量的方法不能为空'
    #                            })


class ShoppingCartDeleteForm(DishesIdForm):
    """
    从购物车中删除某个菜品
    """


class ShoppingCartListForm(forms.Form):
    """
    展示用户购物车里的菜品信息
    """
    food_court_id = forms.IntegerField(min_value=1,
                                       error_messages={
                                           'required': u'美食城ID不能为空'
                                       })
    page_size = forms.IntegerField(min_value=1, max_value=settings.MAX_PAGE_SIZE, required=False)
    page_index = forms.IntegerField(min_value=1, required=False)

