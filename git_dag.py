import time
import os,sys
import scipy.stats
import subprocess

class GitGraph(object):
    def __init__(self):
        self.nodes = {}
        self.count = {}

    def make_graph(self):
        cmd_str = 'git log --date=raw --pretty=format:\"%h,%p,%ad,%s\"'

        lines = subprocess.check_output(cmd_str.split(' ')).splitlines()
        lines.reverse()
        n_branches = 0
        
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

            # update parent/child relationship
            if nd_args[1] != '':
                pa_list = nd_args[1].split(' ')
                for pa_sha in pa_list:
                    self.nodes[nd_args[0]].add_parent(self.nodes[pa_sha])
                    self.nodes[pa_sha].add_child(self.nodes[nd_args[0]])

                if len(self.nodes[pa_sha].children) == 1:
                    n_branches -= 1

                if len(self.nodes[nd_sha].parents) > 1:
                    n_branches -= 1

            # update counts
            self.count[nd_t] = n_branches


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

