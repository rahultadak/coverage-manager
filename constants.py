"""
constants.py
"""

"""
This file contains all the constants relating to the commands, projects, etc
which can be changed here to reflect in the programs
"""
        
"""
List of Projects currently supported
"""
proj_list = {   'Owl'       : 'pj00426',
                'Artemis'   : 'pj01208',
                'Atlas'     : 'pj',
                'Apollo'    : 'pj',
                'Pelican'   : 'pj',
            }

bs_cmd = 'bsub -o {}bsub_log -J {} -R "select [(rhe5||rhe6) && os64]" -M {} \
        -W {} '
vcover = 'vcover -64 -out '
merge_file = 'merge_l{}/merge_l{}_file{} '

FCOV_GROUP = 50
CCOV_GROUP = 25

FCOV_MEM = 4194304
CCOV_MEM = 20000000
