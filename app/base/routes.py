# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from flask import jsonify, render_template, redirect, request, url_for, session
# from flask_login import (
#     current_user,
#     login_required,
#     login_user,
#     logout_user
# )
import requests

# from app import db, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm, ResetPasswordForm

import logging

log = logging.getLogger(__name__)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


UDAPI_URL = "http://localhost:2020"


@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))

@blueprint.route('/page_<error>')
def route_errors(error):
    return render_template('errors/page_{}.html'.format(error))

## Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)

    if 'login' in request.form:
        # POST to UDAPI to login
        username = request.form['username']
        password = request.form['password']

        url = UDAPI_URL + "/login"
        payload = {
            "username":username,
            "password":password
        }
        response = requests.post(url, json=payload)
        data = response.json()

        # If login successfull
        if data['success']:
            print(data['jwtToken'])  # DEBUG LINE
            session["username"] = username
            session["jwtToken"] = data['jwtToken']

            # GET user info from UDAPI
            url = UDAPI_URL + "/user"
            headers = {'jwtToken': data['jwtToken']}
            response = requests.get(url, headers=headers)
            user_data = response.json()
            if user_data['success']:
                session["email"] = user_data['users'][0]['email']
                session["admin"] = user_data['users'][0]['admin']
            else:
                print(user_data['message'])
                return render_template('errors/page_500.html'), 500
            return redirect(url_for('base_blueprint.route_default'))

        return render_template( 'login/login.html', msg=data['message'], form=login_form)

    if not "username" in session:
        return render_template( 'login/login.html', form=login_form)

    return redirect(url_for('home_blueprint.index'))
    

@blueprint.route('/create_user', methods=['GET', 'POST'])
def create_user():
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username         = request.form['username']
        email            = request.form['email'   ]
        password         = request.form['password']
        confirm_password = request.form['repeat_password']

        url = UDAPI_URL + "/register"
        payload = {
            "username":username,
            "email":email,
            "password":password,
            "confirm_password":confirm_password
        }
        response = requests.post(url, json=payload)
        data = response.json()

        if data['success']:
            return render_template( 'login/register.html', success='User created please <a href="/login">login</a>', form=create_account_form)

        if data['error_code'] == 7002:
            return render_template( 'login/register.html', msg=data['message'], form=create_account_form)
        
        return render_template( 'login/register.html', msg=data['message'], form=create_account_form)
    else:
        return render_template( 'login/register.html', form=create_account_form)



@blueprint.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    login_form = LoginForm(request.form)
    reset_password_form = ResetPasswordForm(request.form)
    if 'register' in request.form:
        email            = request.form['email'   ]
        password         = request.form['password']
        confirm_password = request.form['repeat_password']

        url = UDAPI_URL + "/resetpassword"
        payload = {
            "email":email,
            "new_password":password,
            "confirm_password":confirm_password
        }
        response = requests.post(url, json=payload)
        data = response.json()

        if data['success']:
            return render_template( 'login/resetpassword.html', success='Password reseted successfully please <a href="/login">login</a>', form=reset_password_form)

        # Email not registerd.
        if data['error_code'] == 7000:
            return render_template( 'login/resetpassword.html', msg=data['message'], form=reset_password_form)
        
        # Passwords don't match
        if data['error_code'] == 7002:
            return render_template( 'login/resetpassword.html', msg=data['message'], form=reset_password_form)

        # Check if password is same as the previous password
        if data['error_code'] == 7003:
            return render_template( 'login/resetpassword.html', msg=data['message'], form=reset_password_form)

        return render_template( 'login/resetpassword.html', msg=data['message'], form=reset_password_form)

    else:
        return render_template( 'login/resetpassword.html', form=reset_password_form)



@blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('base_blueprint.login'))

@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('errors/page_403.html'), 403

@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page_404.html'), 404

@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page_500.html'), 500

@blueprint.app_errorhandler(404)
def handle_exceptions(e):
    return render_template('error-404.html'), 404

@blueprint.app_errorhandler(Exception)
def handle_unexpected_error(e):
    msg = "UnexpectedError: " + str(e)
    log.exception(f"{bcolors.FAIL}{msg}{bcolors.WARNING}")
    print(f"{bcolors.ENDC}")
    return render_template('error-500.html'), 500