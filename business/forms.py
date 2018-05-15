# -*- encoding: utf-8 -*-
from horizon import forms
from django.conf import settings




    #商户列表
class BusinessUserListForm(forms.Form):
    # pk = forms.IntegerField()
    food_court_id = forms.IntegerField(min_value=1)
    page_size = forms.IntegerField(min_value=1,
                                   max_value=settings.MAX_PAGE_SIZE,
                                   required=False)
    page_index = forms.IntegerField(min_value=1, required=False)

    #商户详情
class BusinessUserForm(forms.Form):
    pk = forms.IntegerField()

    #商户菜品列表
class BusinessDishesListForm(forms.Form):
    user_id = forms.IntegerField()
    page_size = forms.IntegerField(min_value=1,
                                   max_value=settings.MAX_PAGE_SIZE,
                                   required=False)
    page_index = forms.IntegerField(min_value=1, required=False)

 #商城菜品列表
class FoodCourtDishesListForm(forms.Form):
    food_court_id = forms.IntegerField()
    page_size = forms.IntegerField(min_value=1,
                                   max_value=settings.MAX_PAGE_SIZE,
                                   required=False)
    page_index = forms.IntegerField(min_value=1, required=False)

