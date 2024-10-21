from peewee import *
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager
from app import login
from enum import Enum

db = MySQLDatabase('db_transport_company', host='localhost', port=3306, user='root', password='root')

class BaseModel(Model):
    class Meta:
        database = db

class User(UserMixin, BaseModel):
    name = CharField()
    email = CharField(unique = True)
    role = CharField()
    password = CharField()

    def set_password(self, psswd):
        self.password = generate_password_hash(psswd)
        
    def check_password(self, psswd):
        return check_password_hash(self.password, psswd)

class Stop(BaseModel):
    name = CharField()
    
class Line(BaseModel):
    num = IntegerField()
    duration = IntegerField() #in minutes

class Stop2Line(BaseModel):
    stop_id = ForeignKeyField(Stop, backref='stop2line')
    line_id = ForeignKeyField(Line,backref='stop2line')
    order = IntegerField()

class Vehicle(BaseModel):
    spz = CharField()
    username = CharField()
    type = CharField()
    brand = CharField()
    condition = CharField()

class Connection(BaseModel):
    departure = TimeField()
    direction = CharField()
    only_working_days = BooleanField()
    line = ForeignKeyField(Line, backref='connections')
    vehicle = ForeignKeyField(Vehicle, backref='connection')
    driver = ForeignKeyField(User, backref='connection')

class Request(BaseModel):
    description = CharField()
    creation_date = DateField()
    deadline = DateField()
    is_done = BooleanField()
    vehicle = ForeignKeyField(Vehicle, backref='requests')

class MaintenanceRecord(BaseModel):
    date = DateField()
    status = CharField()
    author = ForeignKeyField(User, backref='maintenance_record')
    request = ForeignKeyField(Request, backref='maintenance_record')

class DefectRecord(BaseModel):
    description = CharField()
    date = DateField()
    vehicle = ForeignKeyField(Vehicle, backref='defect')
    author = ForeignKeyField(User, backref='defect')


@login.user_loader
def load_user(id):
    return User().get_or_none(User.id == int(id))

class Role(Enum):
    ADMIN = 'admin'
    MAINTAINER = 'maintainer'
    TECHNICIAN = 'technician'
    DISPATCHER = 'dispatcher'
    DRIVER = 'driver'

db.connect()