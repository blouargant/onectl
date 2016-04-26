#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import ipvalidation
from includes import ifconfig
from includes import bash
from includes import *
import os
import sys
import re
import subprocess

class PluginControl(pluginClass.Base):

	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		
		dic = []
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: set
		opt1 = {}
		opt1['name'] = '--set'
		opt1['metavar'] = 'GATEWAY'
		opt1['action'] = 'store'
		opt1['nargs'] = 1
		opt1['help'] = 'Set default gateway GATEWAY.'
		dic.append(opt1)
		
		### OPTION: remove
		opt1 = {}
		opt1['name'] = '--remove'
		#opt1['metavar'] = ''
		opt1['action'] = 'store_true'
		#opt1['nargs'] = 1
		opt1['help'] = 'Remove default gateway.'
		dic.append(opt1)
		
		return dic
		
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" configuration"
		msg = "Set default gateway, it can either be a device or an IP address.\n"
		msg += "--set GATEWAY      : set GATEWAY as the default gateway\n"
		msg += "                    eg: --set 10.165.110.254 \n"
		msg += "Remove default gateway, it can either be a device or an IP address.\n"
		msg += "--remove GATEWAY   : remove GATEWAY as the default gateway\n"
		msg += "                    eg: --remove 10.165.110.254 \n"
		msg += " \n"
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		try:
			if not data:
				raise ValueError('No input data. Please enter a default gateway  ' )
			data = self.validate_input_data(data)
			ip = data[0]
			if not ip:
				raise ValueError('No input data. Please enter a valid IP address for gateway' )
			if ip == '0.0.0.0/0' or ip == 'none':
				raise ValueError('No input data. Please enter a valid IP address for gateway' )
			if not ipvalidation.is_ipv4(ip):
				raise ValueError(str(ip)+" is not in a valid format!Aborting.")
			plugin_config = self.load_data()
			for plugin in plugin_config:
				if re.search('gateway', plugin) and not re.search('^net.conf.gateway.*', plugin):
					if ip == plugin_config[plugin]:
						raise ValueError(ip+" is already used in " + plugin.strip())
			
		except:
			raise
		return data
		
	def get_active(self):
		try:
			''' MANDATORY !
			    define how to retreive the running config '''
			
			proc = subprocess.Popen(['ip', 'route', 'show'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
			code = proc.wait()
			routes = []
			for aline in proc.stdout:
				routes.append(aline.strip())
			
			gateway = 'none'
			for route in routes:
				if re.search('default via ', route):
					# gateway is ip
					gateway = route.split(' ')[2]
					
				elif re.search('default dev ', route):
					# gateway is dev
					gateway = route.split(' ')[2]
				
		except:
			raise
		return gateway
		
	def get(self):
		try:
			
			gateway = self.get_active()
			self.output.info(gateway)
		except:
			err = str(sys.exc_info()[1])
			self.output.error(err)
			return 1
		return 0

	def set(self, data):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			#ip route add default dev bond0
			#ip route add default via 10.165.110.254
			info = data[0]
			netlib = ifconfig.Interface()
			devlist = netlib.list_ifs(False)
			if info in devlist:
				cmd_gateway = ['ip', 'route', 'add', 'default', 'dev', info]
				gateline = "GATEWAYDEV="+info
			else:
				cmd_gateway = ['ip', 'route', 'add', 'default', 'via', info]
				gateline = "GATEWAY="+info
				
			# search for existing default gateway
			proc = subprocess.Popen(['ip', 'route', 'show'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
			code = proc.wait()
			routes = []
			toadd = True
			for aline in proc.stdout:
				routes.append(aline.strip())
			for route in routes:
				if re.search('default ', route):
					old_gateway = route.split(' ')[2]
					if old_gateway != info:
						if self.live_update:
							# Then remove it
							proc = subprocess.Popen(['ip', 'route', 'del', 'default'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
							code = proc.wait()
					else:
						toadd = False

			# if gateway is none then remove it from /etc/sysconfig/network and we stop here
			if info == "none":
				netlines = []
				tmp_lines = open('/etc/sysconfig/network', 'r').readlines()
				for line in tmp_lines:
					if not re.search('^GATEWAY', line):
						netlines.append(line)
				
				open('/etc/sysconfig/network', 'w').writelines(netlines)
				return 0
				
			# Add if not present
			if toadd and self.live_update:
				proc = subprocess.Popen(cmd_gateway, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
				code = proc.wait()
			
			netlines = []
			notfound = True
			tmp_lines = open('/etc/sysconfig/network', 'r').readlines()
			for line in tmp_lines:
				if not re.search('^GATEWAY', line):
					netlines.append(line)
				else:
					netlines.append(gateline+"\n")
					notfound = False
			if notfound:
				netlines.append(gateline+"\n")

			open('/etc/sysconfig/network', 'w').writelines(netlines)

			self.output.title('Default gateway set to')
			self.output.info(info)

		except:
			err = str(sys.exc_info()[1])
			#self.log.error("setting "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1

		return 0

	def remove(self):
		self.set(['none'])
