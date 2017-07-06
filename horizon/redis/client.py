#-*- coding:utf8 -*-
import redis
import pickle


class Redis(redis.Redis):
    def __init__(self, *args, **kwargs):
        super(Redis, self).__init__(*args, **kwargs)

    def rpush(self, name, *values):
        pk_values = self.translate_instance_to_str(*values)
        return super(Redis, self).rpush(name, *pk_values)

    def rpushx(self, name, value):
        pk_values = self.translate_instance_to_str(value)[0]
        return super(Redis, self).rpushx(name, *pk_values)

    def lpush(self, name, *values):
        pk_values = self.translate_instance_to_str(*values)
        return super(Redis, self).lpush(name, *pk_values)

    def lpushx(self, name, value):
        pk_values = self.translate_instance_to_str(value)[0]
        return super(Redis, self).lpushx(name, *pk_values)

    def lrange(self, name, start=0, end=-1):
        strings = super(Redis, self).lrange(name, start, end)
        return self.translate_str_to_instance(*strings)

    def set(self, name, value, **kwargs):
        pk_value = self.translate_ins_to_str_for_string(value)
        return super(Redis, self).set(name, pk_value, **kwargs)

    def get(self, name):
        string = super(Redis, self).get(name)
        if not string:
            return string
        return self.translate_str_to_ins_for_string(string)

    def translate_ins_to_str_for_string(self, value):
        return pickle.dumps(value)

    def translate_str_to_ins_for_string(self, string):
        return pickle.loads(string)

    def translate_instance_to_str(self, *values):
        return [pickle.dumps(arg) for arg in values]

    def translate_str_to_instance(self, *values):
        return [pickle.loads(arg) for arg in values]


