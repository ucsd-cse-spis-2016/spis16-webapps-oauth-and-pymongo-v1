from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from flask import render_template, flash

import pprint
import os

if os.getenv('GITHUB_CLIENT_ID') == None or \
        os.getenv('GITHUB_CLIENT_SECRET') == None or \
        os.getenv('APP_SECRET_KEY') == None:
    raise GithubOAuthVarsNotDefined('''
      Please define environment variables:
         GITHUB_CLIENT_ID
         GITHUB_CLIENT_SECRET
         APP_SECRET_KEY
      ''')

app = Flask(__name__)

app.debug = True

app.secret_key = os.environ['APP_SECRET_KEY']
oauth = OAuth(app)

# This code originally from https://github.com/lepture/flask-oauthlib/blob/master/example/github.py
# Edited by P. Conrad for SPIS 2016 to add getting Client Id and Secret from
# environment variables, so that this will work on Heroku.

class GithubOAuthVarsNotDefined(Exception):
    '''raise this if the necessary env variables are not defined '''

github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'],
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize'
)


@app.context_processor
def inject_logged_in():
    print "Checking isLoggedIn"
    return dict(logged_in=('github_token' in session))

@app.route('/')
def home():
    return render_template('home.html')
    '''
    if 'github_token' in session:
        me = github.get('user')
        return jsonify(me.data)
    return redirect(url_for('login'))
    '''

@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True))

@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out')
    return redirect(url_for('home'))


#@app.route('/logout')
#def logout():
#    session.pop('github_token', None)
#    return redirect(url_for('index'))


@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        login_error_message = 'Access denied: reason=%s error=%s' % (
            request.args['error'],
            request.args['error_description']
        )        
        flash(login_error_message, 'error')
    else:
        try:
            session['github_token'] = (resp['access_token'], '')
            session['user_data']=github.get('user').data
            flash('You were successfully logged in')
        except:
            session.clear()
            flash('Unable to login, please try again',error)
    return redirect(url_for('home'))


@app.route('/page1')
def renderPage1():
    if 'user_data' in session:
        user_data_pprint = pprint.pformat(session['user_data'])
    else:
        user_data_pprint = '';
    return render_template('page1.html',dump_user_data=user_data_pprint)

@app.route('/page2')
def renderPage2():
    return render_template('page2.html')


@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run()
