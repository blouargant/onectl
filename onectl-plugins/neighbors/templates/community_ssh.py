#!/usr/bin/python -u

from includes import pluginClass
from includes import regexp
from includes import host
import os, errno
import sys
import re
import time
import socket
import paramiko

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		dic = []
		
		### OPTION: exchange
		opt0 = {}
		opt0['name'] = '--exchange'
		opt0['metavar'] = 'PASS'
		opt0['action'] = 'store'
		opt0['nargs'] = '?'
		opt0['help'] = 'Exchange ssh keys'
		dic.append(opt0)
		
		### OPTION: disable
		opt3 = {}
		opt3['name'] = '--disable'
		opt3['metavar'] = 'PASS'
		opt3['action'] = 'store'
		opt3['nargs'] = '?'
		opt3['help'] = 'Disable the ssh key.'
		dic.append(opt3)
		
		### NO OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = ''
		opt['action'] = ''
		opt['nargs'] = ''
		opt['help'] = ''
		dic.append(opt)
	
		### NO OPTION: view
		opt = {}
		opt['name'] = '--view'
		opt['metavar'] = ''
		opt['action'] = ''
		opt['nargs'] = ''
		opt['help'] = ''
		dic.append(opt)
	
		return dic
	
	def info(self):
		''' MANDATORY !'''
		title = "SSH configuration.\n"
		msg =  "--exchange [PASWORD] : Exchange DSA keys between the host and local machine. \n"
		msg += "--disable [PASWORD]  : Remove the ssh keys exchanged from both machines\n"
		msg += "As an optional argument password can be specified in the form PASWORD.\n"
		self.output.help(title, msg)
	
	def inputValidation(self, data=None):
		try:
			if not data:
				return data
			input_list = list(set(data))
			input_list = sorted(input_list)
			plugin = self.PluginFqn
			
			password = host._get_password(data)
			pattern=re.compile(regexp.PASSWORD, re.VERBOSE | re.IGNORECASE)
			if  pattern.match(password) is None:
				raise ValueError('Invalid password %s' %password)
		except:
			self.printError("Validation failure for "+self.PluginName+" : ")
			return None
		
		self.output.debug("Plugin: %s Data is OK" %plugin)
		return data
	

	def get_active(self):
		try:
			''' Get configured configuration  '''
			hostkeys = paramiko.HostKeys()
			hostkeys.load(os.path.expanduser('~/.ssh/known_hosts'))
			community = self._get_community_name(self.PluginFqn)
			lowhostname = hostname.lower()
			if hostname in hostkeys or lowhostname in hostkeys:
				return True
			else:
				return False
		except:
			raise
		return None
	
	def get(self):
		try:
			''' Get info '''
			bTrusted = self.get_active()
			community = self._get_community_name(self.PluginFqn)
			if bTrusted:
				self.output.info("%s is known host" %community)
			else:
				self.output.info("%s is unknown host" %community)
		
		except:
			self.printError("Get "+self.PluginName+" : ")
			return 1
		
		return 0
		
	def _get_community_name(self, plugin):
		''' get the community name from the plugin '''
		# neighbors.conf.communities.COMM1.members
		community = re.sub('.*communities.', '', re.sub('.ssh$', '', plugin))
		return community
		
	def exchange(self, data=None):
		''' exchange key with host '''
		try:
			password = data
			community = self._get_community_name(self.PluginFqn)
			members = []
			msg = self.executePlugin('neighbors.conf.communities.%s.members' %community, 'get')
			if re.search('Error', msg):
				raise ValueError('Can not get members for community %s' %community) 
			else:
				if msg:
					members = msg.split()
			self.community_action(members, 'exchange', password)
		except:
			self.printError("Exchanging "+self.PluginName+" : ")
			return 1
		
		return 0
		
	def community_action(self, members, action, password=None):
		''' exchange key between all hosts in the host_list '''
		try:
			password = host._get_password(password)
			username = host.getlogin()
			
			# get host list in the community
			#members = self.executePlugin('neighbors.conf.communities.%s.members' %community, 'get_active')
			# loop through the list of hosts to exchange keys
			# Can include the local host or not
			for position, srchost in enumerate(members):
				pair_list = members[position+1:]
				ssh_client = host.remote_host_connect(srchost, username, password)
				for dsthost in pair_list:
					#self.executePlugin('neighbors.conf.neighbor.%s.ssh' %srchost, 'community_action', srchost, dsthost, action, password)
					#members = self.executePlugin('neighbors.conf.communities.%s.members' %community, 'get_active')
					# connect to the host
					ip = None
					ip_plugin = "neighbors.conf." + dsthost + ".ip"
					msg = self.executePlugin(ip_plugin, "get")
					if not re.search('Error', msg):
						ip = msg
					else:
						raise ValueError('%s not configuged in neighbors plugin' %dsthost)
					cmd = 'onectl neighbors.names --add %s' %dsthost
					stdin, stdout, stderr = ssh_client.exec_command(cmd)
					cmd = 'onectl neighbors.conf.%s.ip --set %s' %(dsthost, ip)
					stdin, stdout, stderr = ssh_client.exec_command(cmd)
					cmd = 'onectl neighbors.conf.%s.ssh --%s %s' %(dsthost, action, password)
					stdin, stdout, stderr = ssh_client.exec_command(cmd)
					self.output.title('SSH keys %s correctly between %s %s' %(action, srchost, dsthost))
				ssh_client.close()
			#for hostname in host_list:
			#	ssh_client = self.remote_host_connect(hostname, username, password)
			#	self.upload_key(hostname, username, ssh_client)
			#	self.download_key(hostname, username, ssh_client)
			#	ssh_client.close()
		except:
			self.printError("Exchanging "+self.PluginName+" : ")
			return 1
		return 0
		
	def disable(self, data = None):
		''' remove exchanges keys '''
		try:
			password = data
			community = self._get_community_name(self.PluginFqn)
			members = []
			msg = self.executePlugin('neighbors.conf.communities.%s.members' %community, 'get')
			if re.search('Error', msg):
				raise ValueError('Can not get members for community %s' %community) 
			else:
				if msg:
					members = msg.split()
			self.community_action(members, 'disable', password)
	
		except:
			self.printError("Disabling "+self.PluginName+" : ")
			return 1
		
		self.output.title('SSH settings for neighbour removed.')
		return 0
		
	def set(self, data):
		''' Nothing to do when --set [ARGS] is called '''
		return 0
	

