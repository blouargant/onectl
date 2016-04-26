#!/usr/bin/python -u
"""
Loggin Library 
Available log function:
error, warning, info, event, and debug
"""
import os
import time

class Logger:
	def __init__(self, log_file):
		self.log_file = log_file

	def error(self, newline):
		self._log(newline, "ERROR")
	
	def warning(self, newline):
		self._log(newline, "WARNING")
	
	def info(self, newline):
		self._log(newline, "INFO")
	
	def event(self, newline):
		self._log(newline, "EVENT")
	
	def debug(self, newline):
		if debug :
			self._log(newline, "DEBUG")
	
	def _log(self, newline, level="INFO"):
		if os.path.isfile(self.log_file):
			LOG_SIZE = os.path.getsize(self.log_file)
			# if > 1M create a new file
			if LOG_SIZE > 1000000:
				if os.path.exists(self.log_file+".4"):
					os.remove(self.log_file+".4")
					os.rename(self.log_file+".3", self.self.log_file+".4")
				if os.path.exists(self.log_file+".3"):
					os.rename(self.log_file+".3", self.self.log_file+".4")
				if os.path.exists(self.log_file+".2"):
					os.rename(self.log_file+".2", self.self.log_file+".3")
				if os.path.exists(self.log_file+".1"):
					os.rename(self.log_file+".1", self.self.log_file+".2")
				
				os.rename(self.log_file, self.self.log_file+".1")
				logs = open(self.log_file,'w')
			else:
				logs = open(self.log_file,'a')
		else:
			logs = open(self.log_file,'w')

	 	timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
		logs.write(timestamp+"::["+level+"]::"+newline+"\n")
		logs.close()
	
	def print_debug(self, msg):
		if debug :
			debug(msg)
			print msg
