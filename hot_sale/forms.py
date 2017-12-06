# -*- encoding: utf-8 -*-
from horizon import forms
from django.conf import settings


class HotSaleListForm(forms.Form):
    food_court_id = forms.IntegerField(min_value=1)
    # 运营标记： 0：无标记  10：新品  20：特惠  30：招牌  40: 新商户专区  50: 晚市特惠
    mark = forms.ChoiceField(choices=((10, 1),
                                      (20, 2),
                                      (30, 3),
                                      (40, 4),
                                      (50, 5),
                                      (0, 4)),
                             error_messages={
                                 'required': 'Field "mark" must in [0,10,20,30,40,50].'})
    page_size = forms.IntegerField(min_value=1,
                                   max_value=settings.MAX_PAGE_SIZE,
                                   required=False)
    page_index = forms.IntegerField(min_value=1, required=False)


class DishesGetForm(forms.Form):
    pk = forms.IntegerField()


class FoodCourtGetForm(forms.Form):
    pk = forms.IntegerField()


class FoodCourtListForm(forms.Form):
    city = forms.CharField(min_length=2, max_length=100, required=False)
    district = forms.CharField(min_length=2, max_length=100, required=False)
    mall = forms.CharField(min_length=2, max_length=200, required=False)
    page_size = forms.IntegerField(min_value=1,
                                   max_value=settings.MAX_PAGE_SIZE,
                                   required=False)
    page_index = forms.IntegerField(min_value=1, required=False)


class RecommendDishesListForm(forms.Form):
    food_court_id = forms.IntegerField(min_value=1)
