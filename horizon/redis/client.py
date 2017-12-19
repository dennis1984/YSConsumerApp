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
        return self.get_perfect_object_data(string)

    def translate_instance_to_str(self, *values):
        return [pickle.dumps(arg) for arg in values]

    def translate_str_to_instance(self, *values):
        return [self.get_perfect_object_data(arg) for arg in values]

    def get_perfect_object_data(self, value):
        """
        解决反序列化数据后，文件的storage属性丢失的问题
        """
        object_data = pickle.loads(value)
        if isinstance(object_data, dict):
            for key, item in object_data.items():
                if issubclass(type(item), (FieldFile, FileField)):
                    if not hasattr(item, 'storage'):
                        setattr(object_data[key], 'storage', yinshi_storage)
        elif issubclass(type(object_data), Model):
            for field in object_data._meta.fields:
                if issubclass(type(field), (FieldFile, FileField)):
                    setattr(getattr(object_data, field.name), 'storage', yinshi_storage)
        return object_data


