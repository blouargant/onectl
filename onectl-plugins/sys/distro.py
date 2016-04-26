#!/usr/bin/python -u
# Name: sys.distro

from includes import pluginClass
from includes import *
import os
import sys
import re
import subprocess

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		dic = []
		### OPTION: showall
		opt1 = {}
		opt1['name'] = '--showall'
		opt1['metavar'] = ''
		opt1['action'] = 'store_true'
		opt1['nargs'] = ''
		opt1['help'] = 'Show all Operating System information.'
		dic.append(opt1)
		
		### NO OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = ''
		opt['action'] = ''
		opt['nargs'] = ''
		opt['help'] = ''
		dic.append(opt)
		
		return dic
		
	def info(self):
		''' Show information about the operationg system'''
		title = "Distro plugin"
		msg = "Provide information about the installed OS (Version and Profile)\n"
		msg += "This plugin is readonly."
		self.output.help(title, msg)
		
	def get_active(self):
		''' Show Actual OS information '''
		try:
			outmsg=''
			os_lines = []
			if os.path.exists("/etc/redhat-release"):
				f_os = open("/etc/redhat-release", 'r')
				os_lines = f_os.readlines()
				f_os.close()
			else:
				raise ValueError('Unknow operating system.')

			#esult['msg'] = os_lines[len(os_lines)-1]
			for aline in os_lines:
				if not re.match("^$", aline):
					outmsg+=aline.strip()+'\n'
		except:
			raise

		return outmsg

	def get(self):
		try:
			out = self.get_active()
			self.output.info(out)
		except:
			self.printError()
			return 1
		return 0


	def showall(self, *args):
		self.output.enable()
		return self.get()


	def set(self, data):
		''' Nothing to do when --set [ARGS] is called '''
		result = {}
		result['error'] = ''
		result['msg'] = 'Unsupported option'
		self.output.info("Read Only plugin !\n"+data)
		return result
