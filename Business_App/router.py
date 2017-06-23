# -*- coding:utf-8 -*-


class BusinessAppRouter(object):
    """
    控制 Business App 应用中模型的
    所有数据库操作的路由
    """
    def db_for_read(self, model, **hints):
        module_name = self.get_module_name(model)
        if module_name == 'Business_App':
            return 'business'
        return None

    def db_for_write(self, model, **hints):
        module_name = self.get_module_name(model)
        if module_name == 'Business_App':
            return 'business'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        obj1_module_name = self.get_module_name(obj1)
        obj2_module_name = self.get_module_name(obj2)
        if obj1_module_name == 'Business_App' or obj2_module_name == 'Business_App':
            return True
        return None

    def allow_syncdb(self, db, model):
        if db == 'business':
            return model._meta.app_label == 'Business_App'
        elif model._meta.app_label == 'Business_App':
            return False
        return None

    @classmethod
    def get_module_name(cls, model):
        return model._meta.model.__module__.split('.', 1)[0]
