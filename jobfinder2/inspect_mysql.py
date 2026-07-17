import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute('SELECT DATABASE()')
    print('DATABASE', cursor.fetchone()[0])
    cursor.execute("SHOW TABLES LIKE 'accounts_user'")
    print('HAS_TABLE', bool(cursor.fetchone()))
    cursor.execute('SELECT id, email, role FROM accounts_user WHERE email=%s', ['recrutest@gmail.com'])
    print('ROW', cursor.fetchone())
