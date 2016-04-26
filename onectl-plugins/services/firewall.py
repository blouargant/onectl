#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import bash
from includes import *
import os
import sys
import re
import subprocess
import json

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		
		# you will find below an example for a command plugin implementation
		# change the start,stop,restart and status command by whatever commands you
		# need to support.
		
		dic = []
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: start
		opt1 = {}
		opt1['name'] = '--start'
		opt1['metavar'] = ''
		opt1['action'] = 'store_true'
		opt1['nargs'] = ''
		opt1['help'] = 'Start something'
		dic.append(opt1)
		### OPTION: stop
		opt2 = {}
		opt2['name'] = '--stop'
		opt2['metavar'] = ''
		opt2['action'] = 'store_true'
		opt2['nargs'] = ''
		opt2['help'] = 'Stop something'
		dic.append(opt2)
		### OPTION: restart
		opt3 = {}
		opt3['name'] = '--restart'
		opt3['metavar'] = ''
		opt3['action'] = 'store_true'
		opt3['nargs'] = ''
		opt3['help'] = 'Restart something'
		dic.append(opt3)
		### OPTION: status
		opt4 = {}
		opt4['name'] = '--status'
		opt4['metavar'] = ''
		opt4['action'] = 'store_true'
		opt4['nargs'] = ''
		opt4['help'] = 'Display a status.'
		dic.append(opt4)
		
		## To disable the --set options - for a command plugin
		### NO OPTION: set
		opt10 = {}
		opt10['name'] = '--set'
		opt10['metavar'] = ''
		opt10['action'] = ''
		opt10['nargs'] = ''
		opt10['help'] = ''
		dic.append(opt10)
		## To disable the --view options - for a command plugin
		### NO OPTION: view
		opt11 = {}
		opt11['name'] = '--view'
		opt11['metavar'] = ''
		opt11['action'] = ''
		opt11['nargs'] = ''
		opt11['help'] = ''
		dic.append(opt11)
	
		return dic
	
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" commands"
		msg = "Manage something.\n"
		msg += "--start           : Start something\n"
		msg += "--stop            : Stop something\n"
		msg += "--restart         : Restart something\n"
		msg += "--status          : Display a status\n"
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		''' TO OVERWRITE IN PLUGINS -- MANDATORY --
		In this function, plugin creator must implement a data input validator
		If input is valid then the function must return the data, or else it must return None.
		You can also use this to alter input data in order to support multiple input format.
		This function is automatically called, there is no need to call it within <set> function.
		'''
		#return None
		return data

	
	def get(self):
		try:
			''' Get status '''
			res, err = bash.run('service iptables status')
			self.output.info(res)
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error("getting "+self.PluginName+" : "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def view(self, *args, **kwds):
		''' override the view function as no data is saved with this plugin '''
		res = self.get()
		return res
	
	def set(self, data):
		return 0
	
	def _save_cleared_rules(self):
		res, err = bash.run('iptables-save')
		existing_rules = []
		lines = res.split('\n')
		table = "filter"
		for line in lines:
			if re.match('^\*[a-zA-Z]', line):
				table = re.sub('^\*', '', line).strip()
			if re.match('^-. ', line):
				if line in existing_rules:
					rule = re.sub('^-. ', '', line)
					res, err = bash.run('iptables -t '+table+' -D '+rule)
				else:
					existing_rules.append(line)
		# save cleared rules
		bash.run('rm -f /etc/sysconfig/iptables')
		bash.run('service iptables save')
	
	def start(self, data=''):
		''' Start something '''
		try:
			res, err = bash.run('service iptables start')
			self.output.info(res)
			self._save_cleared_rules()
		except:
			err = str(sys.exc_info()[1])
			self.log.error("dothat "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def stop(self, data=''):
		''' Stop something '''
		try:
			res, err = bash.run('service iptables stop')
			self.output.info(res)
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error("dothat "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def restart(self, data=''):
		''' Restart something '''
		try:
			res, err = bash.run('service iptables restart')
			self.output.info(res.strip())
			self._save_cleared_rules()
		except:
			err = str(sys.exc_info()[1])
			self.log.error("dothat "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def status(self, data=''):
		res = self.get()
		return res
	
	def _check(self, *args, **kwargs):
		''' Overwrite _check function, because this is a command plugin
		    and should not display anything with _check
		'''
		return 0

	def hook(self, *args):
		''' hooking function '''
		try:
			print args
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error("setting "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1

		return 0


