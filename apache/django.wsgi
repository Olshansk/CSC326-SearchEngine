import os
import sys

sys.path.append('/home/ubuntu/.virtualenvs/ding/lib/python2.7/site-packages/')

path = '/home/ubuntu/csc326-search-engine/search-engine'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'search-engine.settings'
os.environ['DING_DEBUG'] = 'False'
os.environ['DING_SQLITE_NAME'] = '/home/ubuntu/csc326-search-engine/search-engine/db.sqlite3'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

