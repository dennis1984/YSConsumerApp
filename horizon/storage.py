from django.core.files.storage import FileSystemStorage
from django.utils._os import abspathu, safe_join
from django.utils.functional import LazyObject, cached_property
from django.utils.module_loading import import_string
from django.conf import settings
from os.path import sep


class YSFileSystemStorage(FileSystemStorage):
    def path(self, name):
        if name.startswith(sep):
            return name
        else:
            return safe_join(self.location, name)


def get_storage_class(import_path=None):
    return import_string(import_path or settings.DEFAULT_FILE_STORAGE)


class YinShiStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class()()

yinshi_storage = YinShiStorage()
