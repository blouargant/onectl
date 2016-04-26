#!/usr/bin/python -u
# Name: sys.time.ntp.servers

from includes import pluginClass
from includes import ipvalidation
from includes import *
import os
import sys
import re
from includes import ntplib

class PluginControl(pluginClass.Base):
	# This plugin handles npt servers configuration
	
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		
		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'SERVER1 SERVER2 ..'
		opt['nargs'] = '+'
		opt['action'] = 'store'
		opt['help'] = 'Configure NTP server(s)'
		dic.append(opt)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: add
		opt = {}
		opt['name'] = '--add'
		opt['metavar'] = 'SERVER1 SERVER2 ..'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Add a server or list of servers to the startup config.'
		dic.append(opt)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: remove
		opt = {}
		opt['name'] = '--remove'
		opt['metavar'] = 'SERVER1 SERVER2 ..'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Remove a server or a list of NTP servers'
		dic.append(opt)
		
		return dic
	
	def info(self):
		title = "System NTP "+self.PluginName+" configuration"
		msg = "This plugin configures NTP servers\n"
		msg += "Current NTP configuration can be listed with the following command:\n"
		msg += " > onectl "+self.PluginFqn+" --view [actual|saved|diff]\n"
		msg += "NTP servers can be configured with the following command:\n"
		msg += " > onectl "+self.PluginFqn+" --set SERVER1 [SERVER2] [SERVER3] ..\n"
		msg += "                             e.g.:onectl sys.time.ntp.servers --set 62.161.167.250 2.centos.pool.ntp.org\n"
		msg += " NOTE: set command deletes all previously configured NTP servers and adds listed in the command\n"
		msg += "More NTP servers can be added with the following command:\n"
		msg += " > onectl "+self.PluginFqn+" --add SERVER1 [SERVER2] [SERVER3] ..\n"
		msg += "                             e.g.:onectl sys.time.ntp.server --add 62.161.167.280 0.centos.pool.ntp.org \n"
		msg += " NOTE:add command adds more servers to already configured\n"
		msg += "NTP servers can be removed with the following command:\n"
		msg += " > onectl "+self.PluginFqn+" --remove SERVER1 [SERVER2] [SERVER3] ..\n"
		msg += "                             e.g.:onectl sys.time.ntp.servers --remove 62.161.167.250 2.centos.pool.ntp.org\n"
		msg += " SERVERx is a valid server name or IP"
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		"""
			Validate servers entered at the command line
			Can be a valid IP address or name
		"""
		if not data:
			return

		#remove duplicate values if entered by user
		servers_list = list(set(data))
		
		for server in servers_list:
			# check if valid IP address
			if (ipvalidation.is_ipv4(server) is False) and (ipvalidation.is_ipv6(server) is False) and (ipvalidation.is_hostname_valid(server) is False):
				self.output.error("Setting NTP server:"+str(server)+" is not in a valid format! It should be a valid IP or name.Aborting.")
				return None
		
		for server in servers_list:
			# Retrieve time from server for server check
			try:
				ntpClient = ntplib.NTPClient()
				response = ntpClient.request(server)
			except:
				self.output.warning("NTP server "+str(server)+" is not active!")
		
		return data
	
	def get_active(self):
		"""
			Get current server config
		"""
		try:
			npt_servers_list = []
			if os.path.exists("/etc/ntp.conf"):
				ntp_config = open("/etc/ntp.conf", 'r')
				ntp_lines = ntp_config.readlines()
				ntp_config.close()
				for aline in ntp_lines:
					if not re.search("^ *#", aline):
						config_args = aline.split(' ')
						if "server" in config_args[0]:
							ntp_server = re.sub('"', '', config_args[1].strip())
							npt_servers_list.append(ntp_server)
			else:
				raise ValueError("Error: Cannot find NTP server configuration!")
		except:
			raise

		return npt_servers_list



	def get(self):
		"""
			Get current server config
		"""
		try:
			npt_servers_list = self.get_active()
			if npt_servers_list:
				npt_servers_list = ' '.join(npt_servers_list)
			self.output.title("Current NTP servers configured:")
			self.output.info(npt_servers_list)
		
		except:
			self.printError()
			return 1
		
		return 0
	
	def set(self, data):
		"""
			Configures a one or several NTP servers
			data can be a list of names or IPs
		"""
		try:
			server_list_to_append = []
			for server in data:
				#remove the duplicate values
				if "server "+server not in server_list_to_append:
					server_list_to_append.append("server "+server)
			
			# keeps output config to be written to /etc/ntp.conf
			output_file = []
			
			# read the conf file and skip all lines where server is configured
			file_lines = open('/etc/ntp.conf', 'r').readlines()
			for line in file_lines:
				if not re.search('server', line):
					output_file.append(line)
			
			# add the new NTP servers
			servers_str = '\n'.join(server_list_to_append)
			output_file.append(servers_str+'\n')
			# write the new config
			open('/etc/ntp.conf', 'w').writelines(output_file)
			
			self.output.title('NTP servers configured:')
			self.output.info(servers_str)
			
			# add a restart of ntpd if running for synchronization??
		except:
			self.printError("Setting "+self.PluginName+" " + ' '.join(data)+":")
			return 1
		return 0
	
	def check(self):
		''' Overwrite the check function.Needed for view diff.Check agains Onboot setup
		\n are removed from result from get function '''
		self.output.disable()
		self.get()
		get_result = self.messages["info"]
		# get command returns servers separated by \n.Replace \n with a space
		#view_output = re.sub('\n', ' ', get_result[0])
		if get_result:
			view_output = get_result[0]
			# remove the ending space
			view_output = re.sub(re.escape(' ') + '$', '', view_output)
		else:
			view_output = ''
		self.output.clear_messages()
		self.output.enable()
		self._check(info_get=view_output)
	
	def add(self, data=''):
		''' function adds new server(s) to already configured list
			Takes the current config changes it and calls the set function
			Return 0 for OK and 1 for error
		'''
		try:
			self.show(verbose=False)
			configured = []
			if len(self.messages["info"]) > 0:
				configured = self.messages["info"][0].strip()
			if len(configured) > 0:
				conf_list = configured.split(' ')
			else:
				conf_list = []
			
			if type(data) is list:
				toadd = data
			else:
				toadd.append(data)
			
			for aserv in list(toadd):
				if aserv in conf_list:
					toadd = list(filter(lambda srv: srv!= aserv, toadd))
			
			if not toadd:
				self.output.info("NTP servers are already configured")
				return 0;
			
			conf_list.extend(toadd)
			# set new values
			res = self.set(conf_list)
			
			# if set was ok
			if res == 0:
				self.output.info("NTP server(s) added " + ' '.join(toadd))
			else:
				#messages are printed in set function
				return 1
		
		except:
			self.printError("Adding "+self.PluginName+" " + ' '.join(data)+": ")
			return 1
		
		return 0
	
	def remove(self, data=''):
		''' Delete server lists
			Return 0 for OK and 1 for error
		'''
		try:
			#Get the configured servers
			self.show(verbose=False)
			configured = []
			if len(self.messages["info"]) > 0:
				configured = self.messages["info"][0].strip()
			if len(configured) > 0:
				conf_list = configured.split(' ')
			else:
				conf_list = []
			
			if not conf_list:
				self.output.error("No NTP Servers configured to be deleted")
				return 0
			
			todel = []
			if type(data) is list:
				todel = data
			else:
				todel.append(data)
			
			bEntryRemoved=False
			for entry in list(todel):
				if entry in conf_list:
					conf_list = list(filter(lambda srv: srv!= entry, conf_list))
					bEntryRemoved=True
			
			if not bEntryRemoved:
				self.output.error('NTP Server(s) '+' '.join(todel)+ " are not configured")
				return 0
			
			#self.output.disable()
			res = self.set(conf_list)
			#self.output.enable()
			
			if res == 0:
				self.output.info("NTP server(s) deleted " + ' '.join(todel))
			else:
				#messages are printed in set function
				return 1
		
		except:
			self.printError("Removing "+self.PluginName+" " + ' '.join(data)+": ")
			return 1
		
		return 0
