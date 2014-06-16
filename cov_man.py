from subprocess import call
from flask import Flask, request, render_template, redirect, session, \
        url_for, flash

from flask_login import LoginManager, login_required, login_user, \
        logout_user, current_user

from os import path
from pwd import getpwnam
import thread
#User classes
from user_classes import User, CoverageFunc, Proj_Attr
import constants
from time import sleep
import pexpect

#App setup
app = Flask(__name__)

#TODO
#Clear Debug, and set secret key to random
app.config.update(dict(
    DEBUG=False,
    SECRET_KEY='\x93$\xbeM\x88sV\xe1\xf0\x03G\xd8M\x9dlE\xf8dC2\xa0\x1f%\xb7',
))

#login manager setup
login_manager = LoginManager()

login_manager.init_app(app)

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
#    return None
#TODO remove afetr testing
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
        session.pop('_fresh',None) 
        return redirect(url_for('go_to'))
         
#Login Page
@app.route('/login', methods=['GET','POST'])
def login():
    global user_in

    #Session variable for checkign if login present.
    #TODO setup remember me?
    if request.method == 'POST':

        #Setting up user object
        try:
            getpwnam(request.form['username'])
        except KeyError:
            error = 'Illegal Username given. Try again.'
            return render_template('login.html',error = error)
        else:
            user_in = User(username=request.form['username'])

        #authenticating the user
        user_auth=user_in.authenticate(request.form['password'])

        if user_auth == 1:
            k = login_user(user_in,remember=True)

            if k==True:
                flash("Logged in successfully.")
                session['real_name'] = current_user.first_name()
                return redirect(url_for('cov_select'))

        elif user_auth == 0:
            error = 'The password given is wrong. Try again.'
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
@login_required
#after login is properly done redirect to this url, 
def cov_select():
    error = None
    global cov_type, cov_path, p_user, rm_toggle
    session.pop('cov_type_set', None)
    if request.method == 'POST':
        cov_type = request.form['cov_type']
        cov_path = request.form['cov_path']
        p_inp = request.form['proj_select']

        if not path.exists(cov_path):
            error = 'Invalid path given, please check path'
            return render_template('entry.html',error=error)

        #TODO need to fix this to take rm_old as input
        rm_toggle=request.form['rm_old']

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

@app.route('/to_do',methods=['GET','POST'])
@login_required
def sel_opt():
    global run
    if request.method == 'GET':
        run = CoverageFunc(path=cov_path,covtype=cov_type,user= user_in)
        return render_template('opt_list.html',ucdb_no = run.ucdb_no)
    
    else:
        merge_goto = request.form['merge_goto']

        if int(merge_goto)==1:
            thread.start_new_thread(run.merge_ucdb,(p_user.p_code,rm_toggle,))
            return redirect(url_for('merge_page'))

@app.route('/merge')
@login_required
def merge_page():
    sleep(3)
    return render_template('merge_done.html',level=run.level,jobid=run.jobid \
            ,jobs_done=run.jobs_done,jobs_submitted=run.jobs_submitted, \
            exit_code=run.exit_code)
#OS.Error when server restarted, need to deal with it? TODO

@app.route('/merge_failed')
@login_required
def merge_fail():
    return render_template('merge_fail.html')

@app.route('/merge_passed')
@login_required
def merge_pass():
    return render_template('merge_pass.html')

if __name__ == '__main__':
    app.run()
