from peewee import *

import pymysql

conn = pymysql.connect(host='localhost', user='root', password='root')
conn.cursor().execute('CREATE DATABASE db_transport_company')
conn.close()

db = MySQLDatabase('db_transport_company', host='localhost', port=3306, user='root', password='root')

from app.models import User, Stop, Line, Connection, Vehicle, Request, MaintenanceRecord, Stop2Line, DefectRecord

db.connect()
db.create_tables([User, Stop, Line, Connection, Vehicle, Request, MaintenanceRecord, Stop2Line, DefectRecord])

admin = User(name="Pavel Admin", email="admin@admin.cz", role="admin")
admin.set_password('admin')
admin.save()

maintainer = User(name="Josef Správce", email="maintainer@maintainer.cz", role="maintainer")
maintainer.set_password('maintainer')
maintainer.save()

dispatcher = User(name="Kamil Dispatcher", email="dispatcher@dispatcher.cz", role="dispatcher")
dispatcher.set_password('dispatcher')
dispatcher.save()

driver = User(name="Tereza Driver", email="driver@driver.cz", role="driver")
driver.set_password('driver')
driver.save()


