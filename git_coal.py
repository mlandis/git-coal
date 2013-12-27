import time
import os,sys
import scipy.stats

def sim(n_tip=10,Ne=1000.,coal_rate=.1):

    #clean_git(n_tip)

    # init
    cmd_list = []
    times = []
    branch_names = [ 'branch_'+str(n) for n in range(n_tip) ]
    for bn in branch_names:
        os.popen('git checkout master')
        os.popen('git branch ' + bn)
        os.popen('git checkout ' + bn)
        os.popen('touch ' + bn + '.txt')
        os.popen('git add ' + bn + '.txt')
        os.popen('git commit -a -m \"add ' + bn + '\"')
        os.popen('git push origin ' + bn)

    # coalesce
    n_choose_2 = [ None ]*2 + [ float(n*(n-1)/2) for n in range(2,n_tip+1) ]
    while len(branch_names) > 1:

        # sample time
        n = len(branch_names)
        times.append(scipy.stats.expon.rvs(1./(n_choose_2[n]*coal_rate)))

        # sample pair
        idx_1 = int(scipy.stats.uniform.rvs(0,n))
        idx_2 = idx_1
        while idx_1 == idx_2:
            idx_2 = int(scipy.stats.uniform.rvs(0,n))
        bn = [ branch_names[idx_1], branch_names[idx_2] ]

        #print 'merge',branch_names[idx_1],'and',branch_names[idx_2],'dt',times[-1]

        # generate merge/coalesce commands
        cmd_block = []
        cmd_block.append('git checkout ' + bn[0])
        #cmd_block.append('git add ' + bn[1] + ".txt")
        cmd_block.append('git merge --commit ' + bn[1] + ' -m \"coalesce ' + bn[0] + ' and ' + bn[1] + ' at time ' + str(scipy.sum(times)) + '\"') 
        #cmd_block.append('git commit -a -m \"merge ' + bn[1] + '\"')
        cmd_block.append('git push origin ' + bn[0])
        cmd_list.append(cmd_block)

        # remove 2nd lineage from pool
        branch_names.pop(idx_2)

    # execute in block for speed
    for idx,cmd_block in enumerate(cmd_list):
        #time.sleep(times[idx])
        for cmd in cmd_block:
            time.sleep(0.1) # to avoid .git/index.lock errors
            print cmd
            os.popen(cmd)
        #raw_input('next')

    os.popen('git checkout master')
    #os.popen('git merge ' + branch_names[0])
    #os.popen('git commit -a -m \"merge mrca w master\"')
    #os.popen('git push origin master')


def clean_git(n_tip=10):
    
    os.popen('git checkout master')
    
    # clean local files
    os.popen('rm branch_*.*')
   
    # wipe remote
    for bn in [ 'branch_'+str(n) for n in range(n_tip) ]:
        os.popen('git push origin  :' + bn)

    # wipe local
    clean_str = 'git branch -D'
    branch_names = [ 'branch_'+str(n) for n in range(n_tip) ]
    for bn in branch_names:
        clean_str += ' ' + bn
    clean_str += '\n'
    s = os.popen(clean_str)

