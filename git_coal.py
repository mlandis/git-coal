import time
import os,sys
import scipy.stats

def run(n_tip=4,coal_rate=1.,username='mlandis',password=''):

    if password == '':
        password = getpass.getpass()

    # init
    cmd_list = []
    times = []
    branch_names = [ "branch_"+str(n) for n in range(n_tip) ]
    for bn in branch_names:
        os.popen("git checkout master;git checkout -b origin/" + bn)

    # coalesce
    while len(branch_names) > 2:

        n = len(branch_names)
        nC2 = float(n*(n-1)/2)
        times.append(scipy.stats.expon.rvs(nC2*coal_rate))

        idx_1 = int(scipy.stats.uniform.rvs() * n)
        idx_2 = idx_1
        while idx_1 == idx_2:
            idx_2 = int(scipy.stats.uniform.rvs() * n)
        
        cmd_list.append("git merge origin/" + branch_names[idx_2] + "\n")
        cmd_list.append("git checkout origin/" + branch_names[idx_1] + "\n")

        branch_names.pop(idx_2)
        #branch_names=branch_names[0:idx_2-1]+branch_names[idx_2:n]

        print len(branch_names)

        #stream = os.popen(coal_str)
        # stream_str = stream.readlines()

    # execute in block for speed
    while len(cmd_list) > 0:
        t = times.pop()
        print t
        time.sleep(t)
        os.popen(cmd_list.pop())
        os.popen(cmd_list.pop())

    os.popen("git commit -a -m \"mrca reached\"")

