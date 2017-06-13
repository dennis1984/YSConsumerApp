# -*- encoding: utf-8 -*-
from horizon import forms


class PhoneForm(forms.Form):
    username = forms.CharField(max_length=20, min_length=11,
                               error_messages={
                                   'required': u'手机号不能为空',
                                   'min_length': u'手机号位数不够'
                               })


class PasswordForm(forms.Form):
    password = forms.CharField(min_length=6,
                               max_length=50,
                               error_messages={
                                   'required': u'密码不能为空',
                                   'min_length': u'密码长度不能少于6位'
                               })
    # confirm_password = forms.CharField(min_length=6,
    #                                    max_length=50,
    #                                    error_messages={
    #                                        'required': u'密码不能为空',
    #                                        'min_length': u'密码长度不能少于6位'
    #                                    })


class SendIdentifyingCodeForm(PhoneForm):
    """
    发送手机验证码
    """
    method = forms.ChoiceField(choices=('register', 'forget_password'),
                               max_length=30,
                               error_messages={
                                   'required': u'method 值必须为"register"或"forget_password"',
                               })


class VerifyIdentifyingCodeForm(PhoneForm):
    """
    验证手机验证码
    """
    identifying_code = forms.CharField(max_length=10,
                                       error_messages={'required': u'验证码不能为空'})


class ChangePasswordForm(PasswordForm):
    """
    修改密码
    """


class CreateUserForm(VerifyIdentifyingCodeForm, PasswordForm):
    """
    用户注册
    """


class SetPasswordForm(CreateUserForm):
    """
    忘记密码
    """
