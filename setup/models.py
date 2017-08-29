# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from horizon.models import model_to_dict
from horizon.main import (minutes_30_plus,
                          DatetimeEncode)

import json
import datetime


class FeedBack(models.Model):
    user_id = models.IntegerField('用户ID')
    phone = models.CharField('手机号', max_length=20, null=True, blank=True)
    nickname = models.CharField('菜品ID', max_length=100, null=True, blank=True)

    # 反馈内容
    content = models.CharField('反馈内容', max_length=365, default='')
    created = models.DateTimeField('创建时间', default=now)

    class Meta:
        db_table = 'ys_feedback'
        ordering = ['-created']

    def __unicode__(self):
        return str(self.user_id)
