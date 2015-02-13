from flask.ext.wtf import Form
from wtforms import StringField, DecimalField, BooleanField, validators
from wtforms.validators import DataRequired
from datetime import datetime


class addIntervalForm(Form):
    name = StringField('name', [validators.DataRequired(),
                                validators.Length(min=0, max=32)])
    amount = DecimalField('address', [validators.DataRequired()],
                                      default=0.0)
    address = StringField('address', [validators.DataRequired(),
                                      validators.Length(min=0, max=40)])
    int_val = StringField('int_val', [validators.DataRequired(),
                                      validators.Length(min=0, max=5)])
    int_type = StringField('int_type', [validators.DataRequired(),
                                        validators.Length(min=0, max=40)])
    start_date = StringField('start_date', [validators.Length(min=0, max=19)])


class addCronForm(Form):
    name = StringField('name', [validators.DataRequired(),
                                validators.Length(min=0, max=32)
                                ])
    amount = DecimalField('address', [validators.DataRequired()],
                                      default=0.0)
    address = StringField('address', [validators.DataRequired(),
                                      validators.Length(min=0, max=40)])
    year = StringField('year', [validators.Length(min=0, max=20)])
    month = StringField('month', [validators.Length(min=0, max=20)])
    day = StringField('day', [validators.Length(min=0, max=20)])
    week = StringField('week', [validators.Length(min=0, max=20)])
    day_of_week = StringField('day_of_week', [validators.Length(min=0, max=20)])
    hour = StringField('hour', [validators.Length(min=0, max=20)])
    minute = StringField('minute', [validators.Length(min=0, max=20)])


class addAddressForm(Form):
    name = StringField('name', [validators.DataRequired(),
                                validators.Length(min=0, max=32)
                                ])
    address = StringField('address', [validators.DataRequired(),
                                      validators.Length(min=0, max=40)])

