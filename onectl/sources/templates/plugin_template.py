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
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: dothat
		opt1 = {}
		opt1['name'] = '--dothat'
		opt1['metavar'] = 'THING'
		opt1['action'] = 'store'
		opt1['nargs'] = '?'
		opt1['help'] = 'Do that THING.'
		dic.append(opt1)
		
		## To disable the --set options - for a read-only plugin
		### NO OPTION: set
		#opt2 = {}
		#opt2['name'] = '--set'
		#opt2['metavar'] = ''
		#opt2['action'] = ''
		#opt2['nargs'] = ''
		#opt2['help'] = ''
		#dic.append(opt2)
	
		return dic
	
	
	
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" configuration"
		msg = "describe here what the plugin do.\n"
		msg += "--set VARS ... \n"
		msg += "                  : describe how to set the plugin, along with an exemple\n"
		msg += "                    eg: --set var1 var2 \n"
		msg += "                    You may add some additional information.\n"
		msg += " \n"
		msg += "--funct1           : describe additional function funct1 \n"
		msg += "--funct2 VAR1 VAR2 : cribe additional function funct2 \n"
		msg += " NB: additional information.\n"
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

	def get_active(self):
		try:
			''' MANDATORY ! 
			    get the active state .Return a list! '''
			
			## 
			## core of the function
			##	
			## self.output.info("plugin configuration")
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error("getting "+self.PluginName+" : "+err)
			self.output.error(err)
			return 1

		return 0
	

	def get(self):
		try:
			''' MANDATORY ! 
			    print the active config.Use get_active and print the output '''
			
			## 
			## core of the function
			##	
			## self.output.info("plugin configuration")
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error("getting "+self.PluginName+" : "+err)
			self.output.error(err)
			return 1

		return 0
	
	def set(self, data):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			'''Implement set functionality '''
			## 
			## core of the function
			##
			## If data setting is ok then log it:
			## self.log.info("setting to "+data+": "+err)

		except:
			err = str(sys.exc_info()[1])
			self.log.error("setting "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1

		return 0
	
	def dothat(self, data=''):
		''' function associated with the option previously defined in setOptions 
	        You must have one function for each option ''' 
		try:
			'''Specific commands '''
			## 
			## core of the function
			##
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error("dothat "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
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


