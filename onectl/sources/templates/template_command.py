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

# self.output => screen output
# Available outputs:
# self.output.title, self.output.info, self.output.error, self.output.warning, self.output.debug
# Output messages are stored in self.messages dictionnary that contains the 
# following List entries: self.messages["info"], self.messages["error"], 
# self.messages["warning"], self.messages["error"]
#
# self.log => logger
# Available logs :
# self.log.error, self.log.warning, self.log.info, self.log.debug


	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		'''
		## The dictionnary created in this function will is used to create/modify options parsed in the command line.  
		##
		## create an entry for each additional option
		## opt = {}
		## opt["name"] = "option_name" ; eg --clear
		##
		## opt["help"] = "help message" ; the help message to display 
		##
		## opt["metavar"] = "A_VAR_NAME" ; Optional: the variable's name shown in the help message
		##
		## opt["action"] = store_action
		## where store_action can be one of the following:
		##  'store'                        ; just stores the argument's value.
		##  'store_const'                  ; stores the value specified by the const keyword argument.
		##  'store_true' and 'store_false' ; These are special cases of 'store_const' using for storing the values True and False respectively.
		##  'append'                       ; stores a list, and appends each argument value to the list.
		##  'append_const'                 ; stores a list, and appends the value specified by the const keyword argument to the list.
		##	''                             ; disable the key (for exemple use it to disable the --set options). 
		##
		## with 'store' and 'store_const' actions you can add an additional parameter:
		## opt['nargs'] = NUMBER_OF_ARGUMENTS ; where NUMBER_OF_ARGUMENTS can be:
		##  N (an integer)      ; N arguments from the command line will be gathered together into a list.
		##  '?'                 ; One argument will be consumed from the command line if possible, and produced as a single item.
		##  '*'                 ; All command-line arguments present are gathered into a list.
		##  '+'                 ; Just like '*', all command-line args present are gathered into a list. Additionally, an error message will be generated if there wasn't at least one command-line argument present.
		##  argparse.REMAINDER  ; All the remaining command-line arguments are gathered into a list. This is commonly useful for command line utilities that dispatch to other command line utilities
		##
		## NB: The argparse library is used to parse command line options.
		##     Checkout its documentation for more in depth understanding on how it works.
		'''
		
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
			
			self.output.info("a status")
		
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
	
	def start(self, data=''):
		''' Start something '''
		try:
			print "start"
			#res = dosomething
			#if "Error:" not in res:
			#self.output.info(res)
			#else:
			#	self.log.error(res.replace('Error: ', ''))
			return 0
		except:
			err = str(sys.exc_info()[1])
			self.log.error("dothat "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def stop(self, data=''):
		''' Stop something '''
		try:
			#res = dosomething
			#if "Error:" not in res:
			#self.output.info(res)
			#else:
			#	self.log.error(res.replace('Error: ', ''))
			return 0
		except:
			err = str(sys.exc_info()[1])
			self.log.error("dothat "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def restart(self, data=''):
		''' Restart something '''
		try:
			#res = dosomething
			#if "Error:" not in res:
			#self.output.info(res)
			#else:
			#	self.log.error(res.replace('Error: ', ''))
			return 0
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
		and should not display anything with _check'''
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


