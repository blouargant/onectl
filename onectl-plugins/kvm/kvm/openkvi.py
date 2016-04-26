#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import *
import os
import sys
import re
import subprocess

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
	
		dic = []
		### OPTION: set [enable disable]
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'enable/disable'
		opt['action'] = 'store'
		opt['help'] = 'Enable or disable OpenKVI'
		dic.append(opt)
		return dic
	
	
	
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" configuration"
		msg = "Enable or disable OpenKVI VM.\n"
		msg += "--set [enable/disable]\n"
		msg += "                   : Enable or disable OpenKVI\n"
		msg += "                    If enabled, then openkvi.vm, openkvi.access and openkvi.mode plugins are created\n"
		msg += " \n"
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		if data not in ["enable", "disable"]:
			self.output.error('Either set openkvi to "enable" or "disable".')
			return None
		return data
	
	def get(self):
		self.show()
		return 0
	
	def set(self, data):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			'''Implement set functionality '''
			if data == "enable":
				self.createPlugin("kvm/openkvi_vm_access.py", "openkvi.access.mode")
				self.createPlugin("kvm/openkvi_vm_access.py", "openkvi.access.bridge")
				self.createPlugin("kvm/openkvi_vm.py", "openkvi.vm")
				self.output.title('You can now use openkvi.* plugins to configure OpenKVI:')
				self.output.title(' -> First set access bridge (openkvi.access.bridge)')
				self.output.title('    then set access mode (openkvi.access.mode)')
				self.output.title('    finally create OpenKVI (openkvi.vm --create [ISO]).')
			else:
				self.executePlugin('openkvi.vm', 'destroy')
				self.removePlugin("openkvi.access.mode")
				self.removePlugin("openkvi..access.bridge")
				self.removePlugin("openkvi.vm")
				self.output.title('OpenKVI VM has been disabled.')
			self.log.info(self.PluginName+" set to "+data)
			
		except:
			err = str(sys.exc_info()[1])
			self.log.error("setting "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
		
		return 0
