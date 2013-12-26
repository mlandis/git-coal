import time
import os,sys
import scipy.stats
import getpass
from random import choice,shuffle

def run(n_tip=4,coal_rate=.1):

    clean_git(n_tip=n_tip)

    # init
    cmd_list = []
    times = []
    branch_names = [ 'branch_'+str(n) for n in range(n_tip) ]
    for bn in branch_names:
        os.popen('git checkout master;git checkout -b '+bn+';git push origin '+bn)


    # coalesce
    n_choose_2 = [ None ]*2 + [ float(n*(n-1)/2) for n in range(2,n_tip+1) ]
    while len(branch_names) > 1:

        # sample time
        n = len(branch_names)
        times.append(scipy.stats.expon.rvs(n_choose_2[n]*coal_rate))

        # sample pair
        idx_1 = int(scipy.stats.uniform.rvs(0,n))
        idx_2 = idx_1
        while idx_1 == idx_2:
            idx_2 = int(scipy.stats.uniform.rvs(0,n))
        print idx_1,idx_2

        print 'merge',branch_names[idx_1],'and',branch_names[idx_2],'dt',times[-1]

        # generate merge/coalesce commands
        cmd_list.append('git checkout ' + branch_names[idx_1] + '\n')
        cmd_list.append('git merge ' + branch_names[idx_2] + '\n')

        # remove 2nd lineage from pool
        branch_names.pop(idx_2)


        #stream = os.popen(coal_str)
        # stream_str = stream.readlines()

    # execute in block for speed
    while len(cmd_list) > 0:
        t = times.pop()
        print t
        time.sleep(t)
        os.popen(cmd_list.pop())
        os.popen(cmd_list.pop())

    os.popen('git commit -a -m \"mrca reached\"')


def clean_git(n_tip=4):
    
    os.popen('git checkout master')
   
    # wipe remote
    clean_str = 'git push origin'
    branch_names = [ 'branch_'+str(n) for n in range(n_tip) ]
    for bn in branch_names:
        clean_str += ' :' + bn
    clean_str += '\n'
    s = os.popen(clean_str)

    # wipe local
    clean_str = 'git branch -D'
    branch_names = [ 'branch_'+str(n) for n in range(n_tip) ]
    for bn in branch_names:
        clean_str += ' ' + bn
    clean_str += '\n'
    s = os.popen(clean_str)

