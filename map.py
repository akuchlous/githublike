#!/usr/bin/env python
from multiprocessing import Pipe
from multiprocessing import Process
from multiprocessing import Queue
import sys
import os
import time
import random
import requests

# import Queue
import pdb

class Like:
	def __init__(self, cpu, dumpDir):
		self.r2u = None
		self.u2r = None
		self.cpu = cpu
		self.processRepo = Queue()
		self.topLikes = Queue()
		self.process = []
		for c in range(cpu):
			self.process.append(None)
		if (os.path.exists(dumpDir) == False):
			os.mkdir(dumpDir)
		self.dumpDir = dumpDir
		
	def getTopLikes(self, allLikes, max=8):
		''' sort by key value '''
		tLikes = []
		for w in sorted(allLikes, key=allLikes.get, reverse=True):
			# tLikes.append(w)
			tLikes.append((w, allLikes[w]))
		return tLikes[1:14]

	def writeLikes(self):
		name = self.dumpDir+".like.txt"
		print ("write likes to file %s" % name)
		f  = open(name, "w")
		while( self.topLikes.empty() == False):
			(r, likes) =  self.topLikes.get()
			f.write("%s" % r)
			for k in likes:
				f.write(" %s" % k[0])
		 	f.write("\n")
		f.close()


	def findLikes(self, repo):
		sRepos = {}
		for u in self.r2u[repo]:
			for r in self.u2r[u]:
				if (r not in sRepos):
					sRepos[r] = 0
				sRepos[r] += 1
		self.topLikes.put((repo, self.getTopLikes(sRepos)))


	def readData(self, fileName):
		print ("read data ")
		self.r2u = {}
		self.u2r = {}
		f = open(fileName, "r")
		for line in f:
			(r, u) = line[:-1].split(" ")
			if (r not in self.r2u):
				self.r2u[r] = {}
			self.r2u[r][u] = 1
			if (u not in self.u2r):
				self.u2r[u] = {}
			self.u2r[u][r] = 1
		f.close()
		print ("Total Uniq Repos : %d" % len(self.r2u.keys()))
		print ("Total Uniq Users : %d" % len(self.u2r.keys()))

	def makeRepoQueue(self, fileName):
		print ("read repo list")
		f = open(fileName, "r")
		for line in f:
			self.processRepo.put(line[:-1])
		f.close()

	def startWorkers(self):
		print ("start workers")
		while(self.processRepo.empty() == False):
			for idx in range(self.cpu):
				p = self.process[idx]
				if ((self.processRepo.empty() == False) and ((p == None) or (p.is_alive() == False))):
					d = self.processRepo.get()
					print ("processing repo %s" % d)
					p = Process(target=self.findLikes, args=(d,))
					p.start()
					self.process[idx] = p

	def letItFinish(self):
		print "let all child process finish"
		for idx in range(self.cpu):
			p = self.process[idx]
			if ((p != None) and p.is_alive()):
				print "wait for process to get over"
				p.join()
				self.process[idx] = None
		print "all child process finished"

def main():
	# python  <> DB/repoWatchers.txt 4 /tmp/abcd
	db = sys.argv[1]
	nCpu = int(sys.argv[2])
	repoList = sys.argv[3]
	
	l = Like(nCpu, repoList)
	l.readData(db)
	
	l.makeRepoQueue(repoList)

	l.startWorkers()
	l.letItFinish()

	l.writeLikes()
	
if __name__ == "__main__":
	main()
