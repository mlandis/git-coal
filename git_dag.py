import time
import os,sys
import scipy.stats
import subprocess

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

    def bd_llik(self,birth_rate=1.0,death_rate=1.0):
        T = sorted(self.count.keys())
        llik = 0.
        old_n = 1
        old_t = 0.
        for i,t in enumerate(T):
            if i == 0:
                old_t = t
                continue

            n = self.count[t]
            if n > old_n:
                r = birth_rate
            elif n < old_n:
                r = death_rate
            else:
                continue

            llik += scipy.log(r) - n * (death_rate + birth_rate) * (t - old_t)
            print n,t,llik

            old_n = n 
            old_t = t
        
        return(llik)

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

