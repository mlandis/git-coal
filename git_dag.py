import time
import os,sys
import scipy.stats, scipy.optimize
import subprocess
from scipy.optimize import minimize

class GitGraph(object):
    def __init__(self):
        self.nodes = {}
        self.count = {}
        self.gain = {}
        self.loss = {}

    def make_graph(self):
        cmd_str = 'git log --date=raw --pretty=format:\"%h,%p,%ad,%s\"'
        lines = subprocess.check_output(cmd_str.split(' ')).splitlines()
        lines.reverse()

        n_branches = 0
        n_gain = 0
        n_loss = 0
        
        for l in lines:
            nd_args = l.strip('\"').split(',')
            #print nd_args
            
            nd_sha = nd_args[0]
            nd_t = float(nd_args[2].split(' ')[0])
            nd_msg = nd_args[3]

            # add new nodes to graph
            if nd_sha not in self.nodes:
                self.nodes[nd_sha] = GitNode(nd_sha,nd_t,nd_msg)
                n_branches += 1
                n_gain += 1

            # update parent/child relationship
            if nd_args[1] != '':
                pa_list = nd_args[1].split(' ')
                for pa_sha in pa_list:
                    self.nodes[nd_args[0]].add_parent(self.nodes[pa_sha])
                    self.nodes[pa_sha].add_child(self.nodes[nd_args[0]])

                if len(self.nodes[pa_sha].children) == 1:
                    n_branches -= 1
                    n_gain -= 1

                if len(self.nodes[nd_sha].parents) > 1:
                    n_branches -= 1
                    n_loss += 1

            # update counts
            self.count[nd_t] = n_branches
            self.gain[nd_t] = n_gain
            self.loss[nd_t] = n_loss

    def llik(self,args=[.1,.1,.1]):
        
        x=self.count
        branch_rate=args[0]
        merge_rate=args[1]
        commit_rate=args[2]
        
        llik = 0.
        old_n = 1
        old_t = 0.
        T = sorted(x.keys())
        for i,t in enumerate(T):
            if i == 0:
                old_t = t
                continue

            n = x[t]
            if n > old_n:
                r = branch_rate
            elif n < old_n:
                r = merge_rate
            else:
                r = commit_rate

            if n > 1: 
                llik += scipy.log(r) - n * (branch_rate + merge_rate + commit_rate) * (t - old_t)
            else:
                llik += scipy.log(r) - n * (branch_rate + commit_rate) * (t - old_t)

            #print n,t-old_t,branch_rate,merge_rate,commit_rate,llik

            old_n = n 
            old_t = t
        
        return(-llik)

    def find_mle(self):
        o = scipy.optimize.fmin_l_bfgs_b(func=self.llik,x0=scipy.stats.expon.rvs(.1,size=3),bounds=[(1e-9,None)]*3,approx_grad=True,factr=10.,epsilon=.0001,pgtol=1e-10)
        return o

class GitNode(object):
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

