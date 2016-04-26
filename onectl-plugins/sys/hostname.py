#!/usr/bin/python -u

from includes import pluginClass
from includes import ipvalidation
import os
import sys
import re
import subprocess
import socket

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Add options after hostname plugin '''
	
		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'HOSTNAME'
		opt['action'] = 'store'
		opt['help'] = 'Set hostname'
		dic.append(opt)
		
		return dic
		
	def info(self):
		''' Information for the plugin'''
		title = self.PluginName+" configuration"
		msg = "Change the name of the system.\n"
		msg += "--set HOSTNAME \n"
		msg += "      : Set a new hostname.HOSTNAME should be a valid new hostname for the system\n"
		msg += "      eg: --set vi3server \n"
		self.output.help(title, msg)
		
	def get_active(self):
		# Get the configured hostname
		hostname = socket.gethostname()
		return hostname
		
	def get(self):
		try:
			''' Get configured hostname '''
			
			# Get the configured hostname
			hostname = self.get_active()
			self.output.title("Current hostname:")
			self.output.info(hostname)
		
		except:
			self.printError("Getting "+self.PluginName+" : ")
			return 1
			
		return 0
		
	def inputValidation(self, data):
		try:
			data = self.validate_input_data(data)
			hostname=data[0]
			plugin = self.PluginFqn

			if not hostname:
				raise ValueError("No hostname specified.")
			#for hostname in input_list:
			if (ipvalidation.is_hostname_valid(hostname) is False):
				 raise ValueError("Hostname "+str(hostname)+" is not in a valid format! Aborting.")
		except:
			self.printError("Validation failure for "+self.PluginName+" : ")
			return None
	
		self.output.debug("Data is OK")
		return hostname


	def set(self, data):
		''' Create new alias and remove all existing ones'''
		try:
			
			# validate and transform input to list
			data = self.validate_input_data(data)
			hostname = data[0]
			oldhostname = socket.gethostname()


			file = "/etc/sysconfig/network"
			file_config = open(file, 'r')
			file_lines = file_config.readlines()
			file_config.close()
			
			output_file = []
			for line in file_lines:
				if re.search('HOSTNAME', line):
					output_file.append('HOSTNAME='+hostname+'\n')
				else:
					output_file.append(line)
			
			open(file, 'w').writelines(output_file)

			# live update
			if self.live_update:
				os.system('hostname '+hostname)

			# Change if entry for old name
			hosts_file='/etc/hosts'
			file_config = open(hosts_file, 'r')
			file_lines = file_config.readlines()
			file_config.close()

			output_file = []
			bHostsMod = False
			for line in file_lines:
				if re.search(oldhostname, line):
					line=re.sub(r'\b%s\b' % oldhostname,hostname,line)
					bHostsMod=True
				output_file.append(line)
			# if modified save changes and restart service
			if bHostsMod:
				open(hosts_file, 'w').writelines(output_file)

			self.output.title('Hostname configured:')
			self.output.info(hostname)

		except:
			self.printError("Set failure for "+self.PluginName+" : ")
			return 1

		return 0

	def check(self):
		''' Used for the diff '''
		self.output.disable()
		self.get()
		get_result = self.messages["info"]
		# get command returns servers separated by \n.Replace \n with a space
		if get_result:
			view_output = re.sub(',', ' ', get_result[0])
			# remove the ending space
			view_output = re.sub(re.escape(' ') + '$', '', view_output)
		else:
			view_output = ''
		self.output.clear_messages()
		self.output.enable()
		self._check(info_get=view_output)







