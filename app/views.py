#!/usr/bin/env python
#
import os
from flask import render_template, flash, url_for, redirect, request
from app import app, db, scheduler
from .forms import addIntervalForm, addCronForm, addAddressForm
from .models import JobHistory, AddressBook
from ckapi import CKRequestor
from datetime import datetime
from dateutil import tz
from sqlalchemy import func
from tzlocal import get_localzone
from pytz import timezone, all_timezones_set, common_timezones_set
from decimal import *
import re


# API Keys and other unique configuration goes into "settings.py"
try:
    # normally, you should put your settings into settings.py
    from settings import *
except NotImplementedError:
    # if "settings_dev.py" exists, use that instead (so I don't have to commit my keys)
    from settings_dev import *


def log_error(e, err_type, dest_address, name):
    # Log the error in the transaction history table
    e_str = re.sub('\s+', ' ', str(e)).strip()
    note = '[%s] %s' % (err_type, e_str)
    error = JobHistory(ck_ref='error',
                       name=name,
                       timestamp=datetime.utcnow(),
                       amount = '0',
                       currency = '',
                       address = note)
    db.session.add(error)
    db.session.commit()
    print("(%s) Error executing transaction to '%s'" % (name, dest_address))


def send_funds(funds_amount, dest_address, name):
    # Create transaction and send through API
    if not demo_mode:
        # Create send request through API
        try:
            ck_send = CK_API.put('/v1/new/send',
                                 account=ck_account,
                                 amount=funds_amount,
                                 dest=dest_address)
        except Exception as e:
            log_error(e, 'ck_send', dest_address, name)
            return None
        # Authorize transaction through API
        try:
            ck_auth = CK_API.put(ck_send.next_step)
        except Exception as e:
            log_error(e, 'ck_auth', dest_address, name)
            return None
        ck_ref = ck_auth.result['CK_refnum']
        address = str('%s [%s]' % (get_name(dest_address),
                                   dest_address)).strip()
        currency = ck_send.args['amount']['currency']
        print("(%s) Transaction executed to '%s' [ref: %s]"
              % (name, dest_address, ck_ref))
    else:
        ck_ref= 'Demo'
        currency = 'BTC'
        address = str('%s [%s]' % (get_name(dest_address),
                                   dest_address)).strip()
    # Add job to history table
    job = JobHistory(ck_ref=ck_ref,
                     name=name,
                     timestamp=datetime.utcnow(),
                     amount = str(funds_amount),
                     currency = currency,
                     address = address)
    db.session.add(job)
    db.session.commit()


@app.route('/')
@app.route('/index')
def index():
    if not demo_mode:
        ck_acct = CK_API.get('/v1/account/%s' % (ck_account))
        balance = ck_acct.account['balance']['decimal']
        pending = ck_acct.account['balance_pending']['decimal']
        currency = ck_acct.account['coin_type']
        ck_self = CK_API.get('/v1/my/self')
        limit = ck_self.api_key['funds_limit']['decimal']
    else:
        balance = '0'
        pending = ''
        currency = 'BTC'
        limit = '0.00'
    # Get active jobs from the scheduler
    jobs = scheduler.get_jobs()
    # Get the transaction history from the database
    try:
        transList = JobHistory.query.order_by('timestamp desc').limit(25)
    except:
        transList = ''
    addresses = get_addresses()
    return render_template('index.html',
                           jobs=jobs,
                           transList=transList,
                           addresses=addresses,
                           demo=demo_mode,
                           balance=balance,
                           pending=pending,
                           currency=currency,
                           limit=limit)


@app.route('/add_job_interval', methods=['GET', 'POST'])
def add_job_interval():
    form = addIntervalForm()
    if form.validate_on_submit():
        # Validate the start date, return empty string if it fails
        try:
            start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d %H:%M:%S')
        except:
            start_date = ''
        # Check address book for name, use form address data if none found
        address = get_address(form.address.data)
        if address is None:
            address = form.address.data
        # Set job params for scheduler
        job_params = {form.int_type.data: int(form.int_val.data),
                      'name': form.name.data,
                      'start_date': start_date,
                      'trigger': 'interval',
                      'args': (form.amount.data,
                               address,
                               form.name.data),
                      'timezone': timezone(request.cookies.get('tz_name'))}
        # Remove empty params from dict
        job_params = remove_empty_keys(job_params)
        # Add job to scheduler
        try:
            scheduler.add_job(send_funds, **job_params)
            print '[%s] Job added: %s' % (str(datetime.now()), job_params)
        except Exception:
            flash('Settings are invalid, please try again')
            return redirect(url_for('add_job_interval'))
        return redirect(url_for('index'))
    return render_template('add_job_interval.html',
                           form=form)


@app.route('/add_job_cron', methods=['GET', 'POST'])
def add_job_cron():
    form = addCronForm()
    if form.validate_on_submit():
        # Reject if at least one cron trigger is not set
        if not form.year.data and not form.month.data \
           and not form.day.data and not form.week.data \
           and not form.day_of_week.data and not form.hour.data \
           and not form.minute.data:
            flash('You must include at least one cron trigger')
            return redirect(url_for('add_job_cron'))
        # Check address book for name, use form.address.data if none found
        address = get_address(form.address.data)
        if address is None:
            address = form.address.data
        # Set job params for scheduler
        job_params = {'name': form.name.data,
                      'year': form.year.data,
                      'month': form.month.data,
                      'day': form.day.data,
                      'week': form.week.data,
                      'day_of_week': form.day_of_week.data,
                      'hour': form.hour.data,
                      'minute': form.minute.data,
                      'trigger': 'cron',
                      'args': (form.amount.data,
                               address,
                               form.name.data),
                      'timezone': timezone(request.cookies.get('tz_name'))}
        # Remove empty params from dict
        job_params = remove_empty_keys(job_params)
        # Add job to scheduler
        try:
            scheduler.add_job(send_funds, **job_params)
            print '[%s] Job added: %s' % (str(datetime.now()), job_params)
        except Exception:
            flash('Settings are invalid, please try again')
            return redirect(url_for('add_job_cron'))
        return redirect(url_for('index'))
    return render_template('add_job_cron.html',
                           form=form)


@app.route('/delete_job/<string:ref_num>')
def delete_job(ref_num):
    try:
        scheduler.remove_job(ref_num)
        print '[%s] Job deleted: %s' % (str(datetime.now()), ref_num)
    except:
        flash('Cannot delete, job not found.')
    return redirect(url_for('index'))


@app.route('/history')
def history():
    try:
        transList = JobHistory.query.order_by('timestamp desc').all()
    except:
        transList = ''
    addresses = get_addresses()
    return render_template('history.html',
                           transList=transList,
                           addresses=addresses,
                           demo=demo_mode)


@app.route('/address_book')
def address_book():
    addressList = AddressBook.query.order_by('name').all()
    return render_template('address_book.html',
                           addressList=addressList)


@app.route('/add_address', methods=['GET', 'POST'])
def add_address():
    form = addAddressForm()
    if form.validate_on_submit():
        # Check for existing name (not case-sensitive) and address
        check_name = AddressBook.query.filter(func.lower(AddressBook.name) \
                                              == func.lower(str(form.name.data))).first()
        check_address = AddressBook.query.filter_by(address=form.address.data).first()
        # Add address to db if no duplicates found
        if not check_name and not check_address:
            address = AddressBook(name=form.name.data,
                                  address=form.address.data)
            db.session.add(address)
            db.session.commit()
            print '[%s] Address created for: %s (%s)' % (str(datetime.now()), form.name.data, form.address.data)
        else:
            flash('Duplicate entry found on name or address')
        return redirect(url_for('address_book'))
    return render_template('add_address.html',
                           form=form)


@app.route('/delete_address/<string:address>')
def delete_address(address):
    try:
        address = AddressBook.query.filter_by(address=address).first()
        db.session.delete(address)
        db.session.commit()
        print '[%s] Address deleted: %s' % (str(datetime.now()), address.address)
    except:
        flash('Cannot delete, address not found.')
    return redirect(url_for('address_book'))


@app.template_filter('substring')
def substring(string, start, end):
    return string[start:end]


def remove_empty_keys(d):
    empty_keys = [k for k,v in d.iteritems() if not v]
    for k in empty_keys:
        del d[k]
    return d


# Returns address book as dict
def get_addresses():
    d = {}
    addresses = AddressBook.query.all()
    for a in addresses:
        d.update({a.address: a.name})
    return d


# Returns the name of a given address from the address book
def get_name(a):
    n = AddressBook.query.filter_by(address=str(a)).first()
    if n:
        return n.name
    else:
        return ''
    

# Returns the address of a given name from the address book
def get_address(n):
    a = AddressBook.query.filter(func.lower(AddressBook.name) \
                                 == func.lower(str(n))).first()
    if a:
        return a.address
    else:
        return None
