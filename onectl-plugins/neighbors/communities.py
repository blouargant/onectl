#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import regexp
import os
import sys
import re
import subprocess
import inspect

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'HOST'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Create communities plugins.'
		dic.append(opt)
		
		### OPTION: add
		opt = {}
		opt['name'] = '--add'
		opt['metavar'] = 'HOST'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Add a new community.'
		dic.append(opt)
		
		
		### OPTION: remove
		opt = {}
		opt['name'] = '--remove'
		opt['metavar'] = 'HOST'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Remove a community.'
		dic.append(opt)
		
		return dic
		
	def info(self):
		title = self.PluginName+" configuration"
		msg = "Create or remove hosts communities.\n"
		msg += "--set COM1 COM2   ... \n"
		msg += "                  : List of communities to be created.\n"
		msg += "                    eg: --set mgnt private \n"
		msg += " \n"
		msg += "--add COM_NAME    : Add community or list of communities to the existing ones.\n"
		msg += "--remove COM_NAME : Remove community(ies) plugin(s).\n"
		msg += "\n"
		msg += " NB: After creating a community plugin, configuration is set via neighbors.conf.communities. plugins.\n"
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		try:
			if not data:
				return data
			input_list = list(set(data))
			input_list = sorted(input_list)
			for hostname in input_list:
				if len(hostname) > 255:
					return False
					
				pattern=re.compile(regexp.HOSTNAME, re.VERBOSE | re.IGNORECASE)
				if  pattern.match(hostname) is None:
					raise ValueError('Invalid hostname %s' %hostname)
		except:
			self.printError("Validation failure for "+self.PluginName+" : ")
			return None
		
		return input_list
		
	def get_active(self):
		''' Get configured communities  '''
		file = inspect.getfile(self.__class__)
		base = re.sub('/plugins.*', '', file)
		path = os.path.join(base, "plugins/neighbors/conf/communities")
		
		communities = []
		if os.path.exists(path):
			communities = os.listdir(path)
		communities = sorted(communities)
		return communities
		
	def get(self):
		try:
			''' Print list of communities '''
			
			# Get the configured communities
			communities = self.get_active()
			self.output.title("Configured communities:")
			self.output.info(' '.join(communities))
			
		except:
			self.printError("Getting "+self.PluginName+" : ")
			return 1
		return 0
		
	def set(self, data):
		''' Create communities and remove all existing ones'''
		try:
			#neighbors.neighbors.communities -set  COMM1 COMM2 COMM3
			# validate and transform input to list
			in_data = self.validate_input_data(data)
			
			# find the existing aliases on the system
			com_config = self.get_active()
			for acom in com_config:
				if acom not in in_data:
					self.removePlugin("neighbors.conf.communities."+acom+".members")
					self.removePlugin("neighbors.conf.communities."+acom+".ssh")
				
			for community in in_data:
				self.createPlugin("neighbors/community_members.py", "neighbors.conf.communities." + community + ".members")
				self.createPlugin("neighbors/community_ssh.py", "neighbors.conf.communities." + community + ".ssh")
				
			self.output.info("Created plugins for communities: "  + ' '.join(in_data))
		except:
			self.printError("Set failure for "+self.PluginName+" : ")
			return 1
		return 0
			
	def check(self):
		''' Overwrite the check function.Needed for view diff.Check agains Onboot setup
		\n are removed from result from get function '''
		data_list = self.get_active()
		view_output = ' '.join(data_list)
		self._check(info_get=view_output)
	
	def add(self, data=''):
		''' Add new community plugins to already existing config
			Takes the current config changes it and calls the set function
			Return 0 for OK and 1 for error
		'''
		try:
			input_data = self.validate_input_data(data)
			toadd = input_data
			plugin = self.PluginFqn
			
			curr_config = self.get_current_config(self.PluginFqn)
			#if the plugin is called for the first time no info saves load the current config
			is_db_config = True
			if not curr_config:
				is_db_config = False
				curr_config = self.get_active()
				
			for item in list(toadd):
				# if item is already in the current config remove it from list for adding
				if item in curr_config:
					toadd = list(filter(lambda curr: curr!= item, toadd))
					
			# if list for elements to be added is empty and the db is  exit
			#if db is emtry save the current config
			if not toadd and is_db_config:
				self.output.info("Value(s) " + ' '.join(input_data) + " for plugin "  +self.PluginName +  " already configured")
				return 0;
				
			# add the new elements to the current config
			curr_config.extend(toadd)
				
			# set new values
			res = self.set(curr_config)
			
			# if set was ok
			if res == 0:
				self.output.info("Added plugins "  + ' '.join(toadd))
		except:
			self.printError("Adding "+self.PluginName+" " + ' '.join(toadd)+": ")
			return 1
		return 0
		
	def remove(self, data=''):
		''' Delete community plugins
			Return 0 for OK and 1 for error
		'''
		plugin = self.PluginFqn
		
		try:
			# Check input and transform it to a list
			# remove duplicate values
			input_data = self.validate_input_data(data)
			todel = input_data
			
			#Get the configured servers
			current_config = self.get_current_config(self.PluginFqn)
			
			if not current_config:
				self.output.info("No " + self.PluginName + "(s) configured to be deleted")
				return 0
				
			bEntryRemoved=False
			for entry in todel:
				# if the entry is in current config remove it
				if entry in current_config:
					# iterate through the current config and remove the entry from command
					current_config = list(filter(lambda curr: curr!= entry, current_config))
					bEntryRemoved=True
						
			# if no entries were removed show a message and exit
			if not bEntryRemoved:
				self.output.info("Value(s) " + ' '.join(input_data)  + " for plugin " + self.PluginName + " is(are) not configured.")
				return 0
			
			res = self.set(current_config)
					
			if res == 0:
				self.output.info("Deleted plugins "  + ' '.join(todel))
		except:
			self.printError("Removing "+self.PluginName+" " + ' '.join(todel)+": ")
			return 1
		return 0


