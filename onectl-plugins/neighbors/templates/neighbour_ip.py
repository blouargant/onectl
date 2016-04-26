#!/usr/bin/python -u

from includes import pluginClass
from includes import ipvalidation
from includes import ipaddr
import os
import sys
import re
import subprocess
import time

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		dic = []
		### OPTION: set
		opt0 = {}
		opt0['name'] = '--set'
		opt0['metavar'] = 'IPADDR'
		opt0['action'] = 'store'
		opt0['nargs'] = '+'
		opt0['help'] = 'Configure device. Valid entries are dhcp  or IPADDR/MASK'
		dic.append(opt0)
		
		### OPTION: disable
		opt1 = {}
		opt1['name'] = '--disable'
		opt1['metavar'] = ''
		opt1['action'] = 'store_true'
		opt1['nargs'] = ''
		opt1['help'] = 'Remove the entry for the host in /etc/hosts.'
		dic.append(opt1)
		
		return dic
	
	def info(self):
		''' MANDATORY !'''
		title = "Set IP to host mapping in /etc/hosts\n"
		msg = "--set IPADDR:   IP address to map to a hostname.\n"
		msg += "                     eg: --set 192.168.1.1/24 \n"
		msg += "--disable:     Remove the hostname mapping to an IP in /etc/hosts"
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		''' Validate input  '''
		try:
			self.output.debug("Validating "+str(data))
			if len(data) == 1:
					
				ip = data[0]
				if not ipvalidation.is_ipv4(ip):
					raise ValueError( ip+" is not in a valid format! Aborting.")
					
			self.output.debug(str(data)+" validated")
			return data
		except:
			self.printError("Validate "+self.PluginName+" " + ' '.join(data)+": ")
			return None
	
	def get_active(self):
		try:
			''' Ger active config '''
			hostname = self._get_hostname(self.PluginFqn)
			# Set IP active
			# Get the configured aliases
			hosts_file='/etc/hosts'
			file_config = open(hosts_file, 'r')
			file_lines = file_config.readlines()
			file_config.close()
			
			output = []
			bHostsMod = False
			for line in file_lines:
				if re.search(r'\b%s\b' % (re.escape(hostname)), line):
				#if re.search(hostname, line):
					result = line.split()
					ip = result[0]
					output.append(ip)
			return output
		except:
			raise
	
	def get(self):
		try:
			''' MANDATORY ! 
			    define how to retreive the running config '''
			self.output.title("self.PluginName mapped to:")
			ips = self.get_active()
			for ip in ips:
				self.output.info(ip)
		except:
			self.printError("Getting "+self.PluginName+" : ")
			return 1
		
		return 0
		
	def _get_hostname(self, plugin):
		''' get the hostname from the plugin '''
		# neighbors.conf.hosta.ssh
		hostname = re.sub('.*conf.', '', re.sub('.ip$', '', plugin))
		return hostname
		
	def set(self, data):
		''' Set new IP '''
		try:
			MAX_COL_WIDTH = 16
			data = self.validate_input_data(data)
			ip = data[0]
			hostname = self._get_hostname(self.PluginFqn)
			# Set IP active
			# Get the configured aliases
			hosts_file='/etc/hosts'
			file_config = open(hosts_file, 'r')
			file_lines = file_config.readlines()
			file_config.close()
			
			output_file = []
			bHostsMod = False
			for line in file_lines:
				#if re.search(ip, line) and not re.search(hostname, line):
				if re.search(r'\b%s\b' % (re.escape(ip)), line) and not re.search(r'\b%s\b' % (re.escape(hostname)), line):
					raise ValueError('IP %s is already configured in /etc/hosts for different hostname' %ip)
				if re.search(r'\b%s\b' % (re.escape(hostname)), line):
				#if re.search(hostname, line):
					components = line.split()
					components[0] = ip.ljust(MAX_COL_WIDTH)
					line = ' '.join(components) + '\n'
					bHostsMod=True
				output_file.append(line)
			if not bHostsMod:
				ip = ip.ljust(MAX_COL_WIDTH)
				line = "%s %s\n" %(ip, hostname)
				output_file.append(line)
			# if modified save changes and restart service
			open(hosts_file, 'w').writelines(output_file)
	
		except:
			self.printError("Setting "+self.PluginName+" : ")
			return 1
		
		self.output.title('IP mapping to neighbour correctly set.')
		self.output.info(self.listToString(data))
		return 0
	
	def disable(self):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			#ip = data[0]
			hostname = self._get_hostname(self.PluginFqn)
			# Set IP active
			# Get the configured aliases
			hosts_file='/etc/hosts'
			file_config = open(hosts_file, 'r')
			file_lines = file_config.readlines()
			file_config.close()
			
			output_file = []
			bHostsMod = False
			for line in file_lines:
				if re.search(r'\b%s\b' % (re.escape(hostname)), line):
				#if re.search(hostname, line):
					#line=re.sub(r'\b%s\b' % oldhostname,hostname,line)
					bHostsMod=True
					continue
				output_file.append(line)
			if bHostsMod:
				# if modified save changes and restart service
				open(hosts_file, 'w').writelines(output_file)
		except:
			self.printError("Setting "+self.PluginName+" : ")
			return 1
		self.output.title('Entry for neighbour removed in /etc/hosts.')
		return 0

