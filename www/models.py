import time, uuid
from orm import Model, IntField, FloatField, BooleanField, TextField, StringField

def next_id():
    return '%015d%s000' % (int(time.time()*1000), uuid.uuid4().hex)



