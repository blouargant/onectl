#!/usr/bin/python -u

from includes import pluginClass
from includes import ifconfig
from includes import *
import os
import sys
import re
import subprocess
import inspect

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Add options after alias plugin '''
		
		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'DEV:NUM'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Create IP Alias(s)'
		dic.append(opt)
		
		### OPTION: add
		opt = {}
		opt['name'] = '--add'
		opt['metavar'] = 'DEV:NUM'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Add IP Alias(s).'
		dic.append(opt)
		
		
		### OPTION: remove
		opt = {}
		opt['name'] = '--remove'
		opt['metavar'] = 'DEV:NUM'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Remove IP Alias.'
		dic.append(opt)
		
		return dic
		
	def info(self):
		''' Information for the plugin'''
		title = self.PluginName+" configuration"
		msg = "Create or remove IP Aliases.\n"
		msg += "--set ETHX:NUM ETHX:NUM ... \n"
		msg += "                   : List of  subinterfaces to create.Deletes the existing aliases\n"
		msg += "                     eg: --set eth0:1 eth1:2 \n"
		msg += " \n"
		msg += "--add  ETHX:NUM ETHX:NUM    : Add IP aliase(s) to existing ones \n"
		msg += "--remove  ETHX:NUM ETHX:NUM : Remove IP aliase(s) \n"
		msg += " NB: After creating an IP alias an IP should be set via onectl net.conf.aliases.ethX:NUM.ip.Then the alias will be activated\n"
		self.output.help(title, msg)

	def get_active(self):
		netlib = ifconfig.Interface()
		aliases = netlib.get_active_aliases()
		return aliases


	def get(self):
		try:
			''' Get configured IP aliases '''

			# Get the configured aliases
			netlib = ifconfig.Interface()
			RunningAliases = netlib.get_active_aliases()
			BootAliases = netlib.get_boot_aliases()
			RunningAliases = sorted(RunningAliases)
			BootAliases = sorted(BootAliases)
			self.output.title("Current active " + self.PluginName + ":")
			self.output.info(' '.join(RunningAliases))
			self.output.title("Onboot " + self.PluginName + ":")
			self.output.info(' '.join(BootAliases))
		
		except:
			self.printError("Getting "+self.PluginName+" : ")
			return 1

		return 0
	
	def inputValidation(self, data):
		try:
			if not data:
				return data

			input_list = list(set(data))
			input_list = sorted(input_list)
			plugin = self.PluginFqn

			self.output.debug("Checking input :" + str(data))

			netlib = ifconfig.Interface()
			netDevs = netlib.list_ifs(False)
			## Check that data input is correct
			for check_alias in input_list:

				if not re.search('\:', check_alias):
					raise ValueError('Invalid format - should be dev:NUM')

				dev = check_alias.split(':',1)
				phydev = dev[0]
				if phydev  not in netDevs:
					raise ValueError('Device %s is not valid or up' %phydev)

				# Check if main device is a bond slave
				if netlib.is_bond_slave(phydev):
					raise ValueError('Device %s is part of a bond' %phydev)

		except:
			self.printError("Validation failure for "+self.PluginName+" : ")
			return None

		
		self.output.debug("Data is OK")
		return input_list


	def set(self, data):
		''' Create new alias and remove all existing ones'''
		try:
			
			# validate and transform input to list
			in_data = self.validate_input_data(data)

			# find the existing aliases on the system
			netlib = ifconfig.Interface()
			netAliases = netlib.get_active_aliases()


			ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
			for afile in ifcfg_list:
				if "ifcfg-" in afile:
					if re.search(':', afile):
						subif = re.sub('.*ifcfg-', '', afile)
						if subif not in in_data:
							self.output.debug("Alias set: removing "+str(afile))
							os.remove("/etc/sysconfig/network-scripts/"+afile)


			# Remove each existing alias
			for alias in netAliases:
				if alias not in in_data:
					#if self.live_update:
					netlib.set_ip('0.0.0.0', alias)

			# Get the current config and remove plug-ins
			curr_config = self.get_current_config(self.PluginFqn)
			for curr in curr_config:
				if curr not in in_data:
					ip_alias_plugin = "net.conf.aliases."+curr+".ip"
					self.removePlugin(ip_alias_plugin)

			# no information to add
			if not in_data:
				return 0

			for alias in in_data:

				config_file = "/etc/sysconfig/network-scripts/ifcfg-" + alias
				ip_alias_plugin = "net.conf.aliases."+alias+".ip"

				# Create the plugin. On setting the IP it is enabled
				self.createPlugin("network/plugin_ip.py", ip_alias_plugin)
				self.createPlugin("network/iface_gateway.py", "net.conf.aliases."+alias+".gateway")
			
				if os.path.exists(config_file):
					final_lines = []
					tmp_lines = open(config_file, 'r').readlines()
					for line in tmp_lines:
						if "ONBOOT" in line:
							line = 'ONBOOT="yes\n'
						if "NM_CONTROLLED" in line:
							line = 'NM_CONTROLLED=no\n'
						final_lines.append(line)
					open(config_file, 'w').writelines(final_lines)
				else:
					lines = []
					lines.append('DEVICE="'+alias+'"\n')
					lines.append('ONBOOT="yes\n')
					lines.append('NM_CONTROLLED=no\n')
					open(config_file, 'w').writelines(lines)

				os.chmod(config_file, 0440)

			self.output.info("Created alias(es) "+' '.join(in_data))
		except:
			self.printError("Set failure for "+self.PluginName+" : ")
			return 1

		return 0

	def check(self):
		''' Used for the diff '''
		self.output.disable()
		self.get()
		get_result = self.messages["info"]
		view_output = ''
		# get command returns servers separated by \n.Replace \n with a space
		if get_result:
			view_output = re.sub(',', ' ', get_result[0])
			# remove the ending space
			view_output = re.sub(re.escape(' ') + '$', '', view_output)
		self.output.clear_messages()
		self.output.enable()
		self._check(info_get=view_output)


	def add(self, data=''):
		''' Add new aliases to already existing config
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
				netlib = ifconfig.Interface()
				curr_config = netlib.get_active_aliases()

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
			#self.output.disable()
			res = self.set(curr_config)
			#self.output.enable()

			# if set was ok
			if res == 0:
				self.output.info("Added alias(es) "  + ' '.join(toadd))
		except:
			self.printError("Adding "+self.PluginName+" " + ' '.join(toadd)+": ")
			return 1

		return 0


	def remove(self, data=''):
		''' Delete server lists
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
			
			#self.output.disable()
			res = self.set(current_config)
					
			if res == 0:
				self.output.info("Deleted alias(es) "  + ' '.join(todel))
		except:
			self.printError("Removing "+self.PluginName+" " + ' '.join(todel)+": ")
			return 1
		return 0





