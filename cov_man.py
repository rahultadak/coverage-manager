from subprocess import call
from flask import Flask, request, render_template, redirect, session, \
        url_for, flash

from flask_login import LoginManager, login_required, login_user, \
        logout_user, current_user

from os import path
from pwd import getpwnam
#User classes
from user_classes import User, CoverageFunc, Proj_Attr
import constants

#App setup
app = Flask(__name__)

#login manager setup
login_manager = LoginManager()
login_manager.init_app(app)

#TODO
#Clear Debug, and set secret key to random
app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='dev_key',
))

#login_manager.login_view = "users.login"

#TODO
"""
user_loader(callback)[source]
This sets the callback for reloading a user from the session. The function you 
set should take a user ID (a unicode) and return a user object, or None if the 
user does not exist.
"""
"""Here the method expects to send back the user object on every request. Since
we do not use a database, the user object to be returned is called based on the
user id which is stored upon log in. The pythom pwd module is used for the same
since the user id attribute is also taken from the same module refer to the
following link for more details:
http://stackoverflow.com/questions/12075535/flask-login-cant-understand-how-it-works """
@login_manager.user_loader
def load_user(id):
#_fresh flag is set when the user has logged in and it was a success
    if not '_fresh' or '_fresh' not in session:
        return None
    else:
        return user_in


@app.route('/')
def go_to():
    if not '_fresh' or '_fresh' not in session:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('cov_select'))

#Login Page
@app.route('/login', methods=['GET','POST'])
def login():
    global user_in

    #Session variable for checkign if login present.
    #TODO setup remember me?
    if request.method == 'POST':

        #Setting up user object
        user_in = User(username=request.form['username'])

        #authenticating the user
        user_auth=user_in.authenticate(request.form['password'])

        if user_auth == 1:
            k = login_user(user_in)

            if k==True:
                flash("Logged in successfully.")
                session['real_name'] = current_user.first_name()
                return redirect(url_for('cov_select'))

        else:
            error = request.form['error']
            return render_template('login.html',error = error)

    return render_template('login.html',error = None)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('real_name',None)
    return render_template('logout.html')
#redirect(url_for('logout'))

@login_manager.unauthorized_handler
def unauthorized():
    return render_template('un_auth.html')

@app.route('/select', methods=['GET','POST'])
#after login is properly done redirect to this url, 
@login_required
def cov_select():
    error = None
    global cov_type, cov_path, p_user
    session.pop('cov_type_set', None)
    if request.method == 'POST':
        cov_type = request.form['cov_type']
        cov_path = request.form['cov_path']
        p_inp = request.form['proj_select']

        if not path.exists(cov_path):
            error = 'Invalid path given, please check path'
            return render_template('entry.html',error=error)

        p_user = Proj_Attr(p_name=p_inp)

        session['cov_type_set'] = True
        return redirect(url_for('cov_sel_confirm'))
    return render_template('entry.html',error=error)

@app.route('/confirm',methods=['GET','POST'])
def cov_sel_confirm():
    if cov_type == 'c':
        cov_type_s = 'Code Coverage'
    elif cov_type == 'f':
        cov_type_s = 'Functional Coverage'
    
    if request.method == 'POST':
        next_to = request.form['next_to']
        if int(next_to) == 1:
            return redirect(url_for('sel_opt'))
        elif int(next_to) == -1:
            return redirect(url_for('cov_select'))

    return render_template('entry.html',cov_type_s=cov_type_s, \
            cov_path_ip=cov_path,p_user=p_user.p_name, \
            p_code=p_user.p_code)

@app.route('/to_do')
def sel_opt():
    run = CoverageFunc(path=cov_path,covtype=cov_type)
    return render_template('opt_list.html',ucdb_no = run.ucdb_no)
#OS.Error when server restarted, need to deal with it? TODO

if __name__ == '__main__':
    app.run()
