from os import listdir
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
    path = ''
    covtype = ''
    ucdb_list = [] 
    ucdb_no = 0
    size = 0

    #TODO debug
    f1 = []
    i1 = 0
    """Use f for functional and c for code ? TODO"""

    def __init__(self, path, covtype):
        self.path = path
        self.covtype=covtype
        self.ucdb_list = []
        """Updates the list of ucdbs"""
        self.list_ucdbs()

    def list_ucdbs(self):
        full_list = listdir(self.path)
        for f in full_list:
            if not f.startswith('.'):
                if f.endswith('ucdb'):
                    self.ucdb_list.append(str(f))
                    self.ucdb_no = len(self.ucdb_list)

    def merge_ucdb(self):
        if self.covtype == 'f':
            self.size = constants.FCOV_GROUP
        elif self.covtype == 'c':
            self.size = constants.CCOV_GROUP
        return self.cmd_file_gen(0)

    def cmd_file_gen(self,l):
        #Number of l# merges
        ucdbs = []
        self.i1 = int(ceil(float(self.ucdb_no) / float(self.size)))
        for i in range(self.i1):
            ucdbs.append(' '.join(map(str, \
                    self.ucdb_list[ (i*self.size) : ((i+1)*self.size) ])))
            self.f1.append('#' + str(i+1) + '\n' + constants.vcover + \
                    constants.merge_file.format(l,l,i) + ucdbs[i] + \
                    '| tee ' + constants.merge_file.format(l,l,i)) + '\n'

        return self.f1

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
        

             

