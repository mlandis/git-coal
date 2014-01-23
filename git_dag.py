import time
import random
import os,sys
import scipy.stats, scipy.optimize
import subprocess
from scipy.optimize import minimize

class GitNode(object):
    '''
    GitNode stores parent,child,time,msg,sha info from git history
    '''
    def __init__(self,sha='',t=0.,m=''):
        self.sha = sha
        self.time = t
        self.msg = m
        self.parents = [] 
        self.children = []

    def add_parent(self,parent):
        self.parents.append(parent)

    def add_child(self,child):
        self.children.append(child)

class GitGraph(object):
    '''
    GitGraph stores git-log history
    '''
    def __init__(self):
        self.nodes = {}
        self.count = {}
        self.change = {}
        self.time_list = []
        self.count_list = []

    def get_git_log(self,fp='.'):
        '''
        Populates GitGraph using GitNode objects.
        Reads git-log output from directory at fp.
        '''
        cwd=os.getcwd()
        os.chdir(fp)
        cmd_str = 'git log --date=raw --pretty=format:\"%h,%p,%ad,%s\"'
        lines = subprocess.check_output(cmd_str.split(' ')).splitlines()

        # makes dict of t-indexed gitlog tokens 
        t_args = {}
        for l in lines:
            print l
            args = l.strip('\"').split(',')
            t_tok = args[2].split(' ')
            t = int(t_tok[0]) # raw time (in s) 
            t += int(t_tok[1])*3600 # correct for timezone 
            args[2] = t
            args[3] = ','.join(args[3:]) 
            t_args[t] = args[0:4]

        os.chdir(cwd)
        return t_args


    def make_graph(self,git_log={},fp='.',in_days=True):
        '''
        Populates GitGraph using GitNode objects.
        Reads git-log output from directory at fp.
        '''

        if git_log == {}:
            t_args = self.get_git_log(fp)
        else:
            t_args = git_log
      
        for t in sorted(t_args.keys()):
            
            nd_sha,pa_tok,nd_t,nd_msg = t_args[t]
            if in_days:
                nd_t /= 86400.

            # add new nodes to graph
            dn = 0
            if nd_sha not in self.nodes:
                self.nodes[nd_sha] = GitNode(nd_sha,nd_t,nd_msg)
                dn = 1
            nd = self.nodes[nd_sha]

            # update parent/child relationship
            if pa_tok != '':
                pa_list = pa_tok.split(' ')

                # add missing parents to current time 
                for pa_sha in pa_list:
                    if pa_sha not in self.nodes:
                        self.nodes[pa_sha] = GitNode(pa_sha,nd_t,nd_msg)

                for pa_sha in pa_list:
                    nd.add_parent(self.nodes[pa_sha])
                    self.nodes[pa_sha].add_child(nd)

                if len(self.nodes[pa_sha].children) == 1:
                    dn = 0

                if len(self.nodes[nd_sha].parents) > 1:
                    dn = -len(self.nodes[nd_sha].parents)+1
            else:
                dn = 0

            # update counts
            self.change[nd_t] = dn

        n = 1
        for i,nd_t in enumerate(sorted(self.change.keys())):
            dn = self.change[nd_t]
            n += dn
            self.count[nd_t] = n
            self.count_list.append(n)
            self.time_list.append(nd_t)


    def llik(self,args=[.1,.1,.1]):
        '''
        Returns log likelihood of graph.
        Event types are B(ranch), M(erge), C(ommit; excluding branch/merge)
        All branches undergo events B,M,C at rates r_B,r_M,r_C respectively
        '''
        
        branch_rate,merge_rate,commit_rate=args
        
        llik = 0.
        old_n = 1
        old_t = 0.
        for i,t in enumerate(self.time_list):
            if i == 0:
                old_t = t
                continue
            
            n = self.count_list[i]
            dn = n - old_n
            dt = t - old_t
            if dt == 0:
                old_n = n
                continue

            if n > old_n: r = branch_rate
            elif n < old_n: r = merge_rate
            else: r = commit_rate

            if n > 1: 
                llik += scipy.log(r) - n * (branch_rate + merge_rate + commit_rate) * dt
            else:
                llik += scipy.log(r) - n * (branch_rate + commit_rate) * dt

            #print dt,dn,llik
            old_n = n 
            old_t = t

        return(llik)

    def find_mle(self):
        o = scipy.optimize.fmin_l_bfgs_b(func=self.llik,x0=scipy.stats.expon.rvs(.05,size=3),bounds=[(1e-9,None)]*3,approx_grad=True,factr=10.,epsilon=.0001,pgtol=1e-30)
        return o

    def run_mcmc(self,n=5000,prior=[1.]*3,proposal_tune=[1.]*3,thin=10,burn=0.2,fn='mcmc.txt',stdout=True):
        '''
        GitGraph.run_mcmc runs MCMC on GitGraph using GitGraph.llik
        '''
        # log mcmc output
        f = open(fn,'w')
        f.write('cycle\tlnPosterior\tlnLikelihood\tlnPrior\trate_branch\trate_merge\trate_commit\n')
        
        # initialize mcmc
        params=[ scipy.stats.expon.rvs(scale=1./p) for p in prior ]
        old_lnL = self.llik(params)
        old_lnP = sum( [scipy.stats.expon.logpdf(x=p,scale=1./prior[i]) for i,p in enumerate(params) ])

        # run mcmc
        for i in range(1,n+1):

            # propose state
            p_idx = random.sample(range(len(params)),1)[0]
            p_old = params[p_idx]
            r = scipy.exp(proposal_tune[p_idx]*(.5-scipy.stats.uniform.rvs()))
            params[p_idx] *= r
            lnMH = scipy.log(r)

            # evaluate MH ratio 
            new_lnL = self.llik(params)
            new_lnP = old_lnP + scipy.stats.expon.logpdf(x=params[p_idx],scale=1./prior[p_idx]) - scipy.stats.expon.logpdf(x=p_old,scale=1./prior[p_idx])
            lnR = (new_lnL - old_lnL) + (new_lnP - old_lnP) + lnMH
            
            # accept/reject
            accept = False
            if lnR < -300:
                accept = False
            elif lnR >= 0:
                accept = True
            elif scipy.stats.uniform.rvs() < scipy.exp(lnR):
                accept = True
            else:
                accept = False

            # update
            if accept == True:
                old_lnL = new_lnL
                old_lnP = new_lnP
            else:
                params[p_idx] = p_old

            # write to log
            if i % thin == 0:
                if stdout:
                    print i,old_lnL,old_lnP,params
                if i >= burn*n:
                    s = '\t'.join([ str(e) for e in [i,old_lnL+old_lnP,old_lnL,old_lnP]+params ]) + '\n'
                    f.write(s)
        f.close()
        if stdout:
            print 'Done!'
