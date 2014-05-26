import os
import constants
from flask import render_template
from flask_login import UserMixin
import pexpect
from pwd import getpwnam, getpwall
from math import ceil
import re

from time import sleep

class User(UserMixin):

    def __init__(self,username):
        self.username = username
         
    def authenticate(self,pswd):
        self.pswd = pswd
        auth = pexpect.spawn('su ' + self.username)
        auth.expect('word:')
        auth.sendline(self.pswd)
        auth.sendline('whoami')
        self.auth_op = auth.expect(['incorrect password', self.username])
        auth.terminate()

        self.id = getpwnam(self.username)[2]
        return self.auth_op

    def first_name(self):
        return getpwnam(self.username)[4]

    def is_authenticated(self):
        if not self.auth_op:
            return False
        return True
 
    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

class CoverageFunc:
    """This is the class for all the project variables"""
    user = None
    """Use f for functional and c for code ? TODO"""

    def __init__(self, path, covtype, user):
        self.path = path
        self.covtype=covtype
        self.user = user        
        """Updates the list of ucdbs"""
        self.list_ucdbs(self.path)

    def list_ucdbs(self,path_to_ucdbs):
        #TODO os.listdir does not have permission to read, figure out way use
        #     su
        perm_fix = pexpect.spawn('su ' + self.user.username)
        perm_fix.expect('word:')
        perm_fix.sendline(self.user.pswd)
        perm_fix.sendline('chmod a+rx ' + path_to_ucdbs)
        perm_fix.expect('.*')
        perm_fix.terminate(force = True)

        full_list = os.listdir(path_to_ucdbs)
        ucdb_list=[]
        for f in full_list:
            if not f.startswith('.'):
                if f.endswith('ucdb'):
                    ucdb_list.append(str(f))

        if path_to_ucdbs == self.path:
            self.ucdb_no = len(ucdb_list)

        return ucdb_list

    def merge_ucdb(self,p_code,rm_toggle=0):
        if self.covtype == 'f':
            self.size = constants.FCOV_GROUP
            self.mem = constants.FCOV_MEM
        elif self.covtype == 'c':
            self.size = constants.CCOV_GROUP
            self.mem = constants.CCOV_MEM

        """ Init of variables for view """
        self.jobid = 0
        self.jobs_done = 0
        self.jobs_submitted = 0
        self.exit_code = 0
        
        if rm_toggle:
            rm_old = pexpect.spawn('su ' + self.user.username)
            rm_old.expect('word:')
            rm_old.sendline(self.user.pswd)
            rm_old.expect('.*')
            rm_old.sendline('rm -rf cmds_l* merge_l* fcov_bsub_log \
                    ccov_bsub_log')
            rm_old.expect('.*')
            rm_old.terminate(force=True)

        cnt = self.ucdb_no
        m_count = 0
        while cnt > 1:
            cnt = int(ceil(float(cnt) / float(self.size)))
            m_count = m_count + 1

        cnt = self.ucdb_no
        for self.level in range(m_count):
            #cnt is the number of merges that will be output at this level
            #i is the level of the merge
            cnt = int(ceil(float(cnt) / float(self.size)))            
            if self.level == 0:
                ucdb_list = self.list_ucdbs(self.path)

            else:
                ucdb_list = self.list_ucdbs(self.path \
                        + '/merge_l{}'.format(self.level-1))                


            self.cmd_file_gen(self.level,ucdb_list,cnt) 
            self.submit_merge(self.level,cnt,p_code)
            exit_c = self.wait_merge()
            if exit_c == 127:
                self.exit_code = 127
                print self.exit_code
                return self.exit_code
        
        self.exit_code = 1
        print 'exit_code'
        print self.exit_code
        return self.exit_code

    def cmd_file_gen(self,l,ucdb_list,cnt):
        #Number of l# merges
        self.f1 = []
        ucdbs = []
        cmd_str = ''

        for i in range(cnt):
            if l > 0:
                ucdb_list = ['merge_l{}/'.format(l-1) + e for e in ucdb_list]

            ucdbs.append((' ').join(map(str, \
                    ucdb_list[ (i*self.size) : ((i+1)*self.size) ])))

            cmd_str = '#' + str(i+1) + '\n' + constants.vcover_m \
                    + self.path + '/' \
                    + constants.merge_file.format(l,l,i) + '.ucdb ' \
                    + ucdbs[i]

            if self.covtype == 'c':
                cmd_str = cmd_str + ' -ignoredusig ' + '| tee ' \
                    + self.path + '/' \
                    + constants.merge_file.format(l,l,i) + '.log \n\n'
            else:
                cmd_str = cmd_str + '| tee ' \
                    + self.path + '/' \
                    + constants.merge_file.format(l,l,i) + '.log \n\n'

            self.f1.append(cmd_str)

        fh = open(constants.tmp_dir + self.user.username+ \
                '_cmds_l{}'.format(l),"w")
        fh.writelines(self.f1)
        fh.close()
        while not os.path.isfile(constants.tmp_dir + self.user.username+ \
                '_cmds_l{}'.format(l)):
            sleep(2)

        cp_cmd = 'cp ' + constants.tmp_dir \
                + self.user.username + '_cmds_l{}'.format(l) \
                + ' ' + self.path + '/cmds_l{}'.format(l)

        cmd_file = pexpect.spawn('su ' + self.user.username)
        cmd_file.expect('word:')
        cmd_file.sendline(self.user.pswd)
        cmd_file.expect('.*')
        cmd_file.sendline(cp_cmd)
        cmd_file.expect('.*')
        cmd_file.sendline('ls '+ self.path + '/cmds_l{}'.format(l))
        cp_suces = cmd_file.expect(['word','cmds_l{}'.format(l)])

        while not os.path.isfile(self.path + '/cmds_l{}'.format(l)):
            sleep(1)

        cmd_file.terminate(force=True)
        if cp_suces == 0:
            print 'error:file not created'
        else:
            os.remove(constants.tmp_dir + self.user.username \
                    + '_cmds_l{}'.format(l))

    def submit_merge(self,l,num_jobs,p_code):
        bs_cmd = constants.bs_cmd.format(self.covtype,self.covtype,num_jobs, \
                self.mem,360,p_code) + 'array_runner ' + self.path \
                + '/cmds_l{}'.format(l) 

        bs_sub = pexpect.spawn('su ' + self.user.username)
        bs_sub.expect('word:')
        bs_sub.sendline(self.user.pswd)
        bs_sub.sendline('cd ' + self.path)

        bs_sub.expect('.*')
        bs_sub.sendline('mkdir merge_l{}'.format(l))
        bs_sub.expect('.*')
        bs_sub.sendline('module load eda mentor/questasim/10.2')
        bs_sub.expect('.*')

        bs_sub.expect('.*')        

        bs_sub.sendline(bs_cmd)
        bs_sub.expect(' is submitted to queue')
        reply = bs_sub.before
        bs_sub.terminate(force= True)
        jobid_regex = re.search("Job <(\d+)>",reply)
        self.jobid = jobid_regex.groups()[0]
    #TODO needs to return job id for the wait macro

    def wait_merge(self):
    
        #Initialising vars
        pending = 1
        exited = 0

        wait_chk = pexpect.spawn('su ' + self.user.username)
        wait_chk.expect('word:')
        wait_chk.sendline(self.user.pswd)
        wait_chk.expect('.*')

        while (pending != 0 & exited == 0):
            wait_chk.sendline('bjobs -A ' + self.jobid)
            wait_op = wait_chk.expect(['not found','PSUSP'])
               
            while wait_op == 0:
                sleep(2)
                wait_chk.sendline('bjobs -A ' + self.jobid)
                wait_op = wait_chk.expect(['not found','PSUSP'])

            wait_chk.sendline('echo marker')
            wait_chk.expect('marker')
            wait_op = wait_chk.before.split()
            
            self.jobs_submitted = int(wait_op[3])
            self.jobs_done = int(wait_op[5])
            pending = int(wait_op[4])
            exited = int(wait_op[7])

            sleep(3)

        wait_chk.terminate(force=True)
        if exited != 0:
            return 127

        if self.jobs_done == self.jobs_submitted:
            return 0
    
"""This class sets up Project attributes"""
class Proj_Attr:
    p_name = ''
    p_code = ''
    f_mem = int()
    c_mem = int()

    def __init__(self,p_name):
        #,f_mem=None,c_mem=None):
        
        self.f_mem = constants.FCOV_MEM
        self.c_mem = constants.CCOV_MEM
        self.p_name = p_name
        self.p_code = constants.proj_list[p_name]
        

             

