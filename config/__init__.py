"""
Config initialization and Python 3.15+ compatibility patches.
"""
import sys

# PyMySQL integration for Django MySQL backend
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    pass

# Python 3.15 compatibility fix for Django template BaseContext.__copy__
# In Python 3.15+, copy(super()) returns a super proxy object without __dict__.
try:
    from django.template import context as django_template_context

    def _safe_basecontext_copy(self):
        dup = self.__class__.__new__(self.__class__)
        dup.__dict__.update(self.__dict__)
        dup.dicts = self.dicts[:]
        return dup

    django_template_context.BaseContext.__copy__ = _safe_basecontext_copy
except Exception:
    pass
