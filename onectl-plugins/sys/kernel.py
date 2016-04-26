#!/usr/bin/python -u
# Name: sys.kernel 

from includes import pluginClass
from includes import *
import sys
import platform

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		
		### the line below is mandatory for bash autocompletion
		### NO OPTION: set
		dic = []
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = ''
		opt['action'] = ''
		opt['nargs'] = ''
		opt['help'] = ''
		dic.append(opt)
		return dic
		
	def info(self):
		''' Show information about the Kernel'''
		title = "Kernel plugin"
		msg = "Provide information about the running kernel\n"
		msg += "This plugin is readonly."
		self.output.help(title, msg)
		
	def get_active(self):
		msg = platform.system()+' '+platform.release()+' (processor:'+platform.processor()+')'
		return msg
		
	def get(self):
		''' Show OS information '''
		try: 
			msg = self.get_active()
			self.output.info(msg)
		
		except:
			self.printError()
			return 1
			
		return 0
		
	def set(self):
		''' Nothing to do when --set [ARGS] is called '''
		return 0
		
	#Hook function called from distro prugin for showall command
	#Show info for platform
	def kernelShowAll(self, *args):
		''' hooking function '''
		self.output.enable()
		self.get()

