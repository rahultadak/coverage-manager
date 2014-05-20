import os
import constants
from flask_login import UserMixin
import pexpect
from pwd import getpwnam
from math import ceil

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
    #path = ''
    #covtype = ''
    #ucdb_list = [] 
    #ucdb_no = 0
    #size = 0

    ##TODO debug
    #f1 = []
    #i1 = 0
    user = None
    """Use f for functional and c for code ? TODO"""

    def __init__(self, path, covtype, user):
        self.path = path
        self.covtype=covtype
        self.ucdb_list = []
        """Updates the list of ucdbs"""
        self.list_ucdbs(self.path)
        self.user = user
    def list_ucdbs(self,path_to_ucdbs):
        #TODO os.listdir does not have permission to read, figure out way use
        #     su
        full_list = os.listdir(path_to_ucdbs)
        for f in full_list:
            if not f.startswith('.'):
                if f.endswith('ucdb'):
                    self.ucdb_list.append(str(f))
                    self.ucdb_no = len(self.ucdb_list)

    def merge_ucdb(self,p_code):
        if self.covtype == 'f':
            self.size = constants.FCOV_GROUP
            self.mem = constants.FCOV_MEM
        elif self.covtype == 'c':
            self.size = constants.CCOV_GROUP
            self.mem = constants.CCOV_MEM

        cnt = self.ucdb_no
        m_count = 0
        while cnt > 1:
            cnt = int(ceil(float(cnt) / float(self.size)))
            m_count = m_count + 1

        cnt = self.ucdb_no
        for i in range(m_count):
            cnt = int(ceil(float(cnt) / float(self.size)))            
            if i == 0:
                self.cmd_file_gen(i,cnt,self.path)
                jobid = self.submit_merge(i,cnt,self.path,p_code)

            else:
                self.cmd_file_gen(i,cnt,self.path+'merge_l{}'.format(i))
                jobid = \
                self.submit_merge(i,cnt,self.path+'merge_l{}'.format(i),p_code)

            self.wait_merge(jobid)

    def cmd_file_gen(self,l,cnt,path_to_ucdbs):
        #Number of l# merges
        self.f1 = []
        ucdbs = []
        for i in range(cnt):
            ucdbs.append(' '.join(map(str, \
                    self.ucdb_list[ (i*self.size) : ((i+1)*self.size) ])))

            cmd_str = '#' + str(i+1) + '\n' + constants.vcover_m \
                    + path_to_ucdbs + '/' \
                    + constants.merge_file.format(l,l,i) + '.ucdb ' \
                    + ucdbs[i]

            if self.covtype == 'c':
                cmd_str = cmd_str + ' -ignoredusig ' + '| tee ' \
                    + path_to_ucdbs + '/' \
                    + constants.merge_file.format(l,l,i) + '.log \n\n'
            else:
                cmd_str = cmd_str + '| tee ' \
                    + path_to_ucdbs + '/' \
                    + constants.merge_file.format(l,l,i) + '.log \n\n'

            self.f1.append(cmd_str)

        fh = open(constants.tmp_dir + self.user.username+ \
                '_cmds_l{}'.format(l),"w")
        fh.writelines(self.f1)
        fh.close()
        cp_cmd = 'cp ' + constants.tmp_dir \
                + self.user.username + '_cmds_l{}'.format(l) \
                + ' ' + path_to_ucdbs + '/cmds_l{}'.format(l)

        cmd_file = pexpect.spawn('su ' + self.user.username)
        cmd_file.expect('word:')
        cmd_file.sendline(self.user.pswd)
        cmd_file.sendline(cp_cmd)
        cmd_file.expect('>')
        cmd_file.sendline('ls '+ path_to_ucdbs + '/cmds_l{}'.format(l))
        cp_suces = cmd_file.expect(['word','cmds_l{}'.format(l)])
        cmd_file.terminate(force=True)
        if cp_suces == 0:
            return 'error:file not created'
        else:
            os.remove(constants.tmp_dir + self.user.username \
                    + '_cmds_l{}'.format(l))

    def submit_merge(self,l,num_jobs,path_to_ucdbs,p_code):
        bs_cmd = constants.bs_cmd.format(self.covtype,self.covtype,num_jobs, \
                self.mem,360,p_code) + 'array_runner ' + path_to_ucdbs \
                + '/cmds_l{}'.format(l) 
        print bs_cmd 

        bs_sub = pexpect.spawn('su ' + self.user.username)
        bs_sub.expect('word:')
        bs_sub.sendline(self.user.pswd)
        bs_sub.sendline('cd ' + path_to_ucdbs)
        bs_sub.expect('>')
        bs_sub.sendline('mkdir merge_l{}'.format(l))
        bs_sub.expect('>')
        bs_sub.sendline('module load eda mentor/questasim/10.2')
        bs_sub.expect('>')
        bs_sub.sendline(bs_cmd)
        bs_sub.expect('>')
        print bs_sub.before
        bs_sub.terminate(force= True)
        return 1

    def wait_merge(self,jobid):
        pass

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
        

             

