#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import ifconfig
from includes import ipvalidation
from includes import ipaddr
from includes import *
import os
import sys
import re
import subprocess
import time
import signal 



class PluginControl(pluginClass.Base):

	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		dic = []
		### OPTION: set
		opt0 = {}
		opt0['name'] = '--set'
		opt0['metavar'] = 'param:VALUE'
		opt0['action'] = 'store'
		opt0['nargs'] = '+'
		opt0['help'] = 'Configure device. Valid entries are dhcp  or IPADDR/MASK'
		dic.append(opt0)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: ip
		opt1 = {}
		opt1['name'] = '--ip'
		opt1['metavar'] = 'IPADDR'
		opt1['action'] = 'store'
		#opt1['nargs'] = '?'
		opt1['help'] = 'Set IP address. Use dhcp key word to use dhcp mode.'
		dic.append(opt1)
		
		### OPTION: mask
		opt2 = {}
		opt2['name'] = '--mask'
		opt2['metavar'] = 'NETMASK'
		opt2['action'] = 'store'
		#opt2['nargs'] = '?'
		opt2['help'] = 'Set Netmask address.'
		dic.append(opt2)
		
		### __OPTION: gate
		#opt3 = {}
		#opt3['name'] = '--gate'
		#opt3['metavar'] = 'GATEWAY'
		#opt3['action'] = 'store'
		##opt3['nargs'] = '?'
		#opt3['help'] = 'Set Gateway address.'
		#dic.append(opt3)
		
		return dic
	
	def info(self):
		''' MANDATORY !'''
		title = "IP configuration"
		msg = "\n"
		msg += "--set IPADDR/MASK  : Take an ip address and a mask to set the device.\n"
		msg += "                     The 'dhcp' keyword can also be used for dynamic IP configuration.\n"
		msg += "                     eg: --set 192.168.1.1/24 \n"
		msg += "                     or: --set dhcp \n"
		msg += '                     To unset an interface ip you can use either "0.0.0.0/0" or "none".\n'
		msg += " \n"
		msg += "--ip   IPADDR      : Modify the IP address\n"
		msg += "--mask NETMASK     : Modify the netmask (eg --mask 255.255.255.0) \n"
		msg += "NB: An interface must first be activated before being able to proceed with its configuration.\n"
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		''' TO OVERWRITE IN PLUGINS -- MANDATORY --
		In this function, plugin creator must implement a data input validator
		If input is valid then the function must return 0, else it must return 1
		This function is automatically called, there is no need to call it within <set> function.
		'''
		data_res = None
		errmsg = ""
		
		data = self.getBoundValue(data)
		
		self.output.debug("Validating "+str(data))
		if len(data) == 1:
			err = False
			if not data[0]:
				data[0] = 'none'
			
			if data[0] == 'dhcp':
				self.output.debug(str(data)+" validated")
				return data
			else:
				if data[0] == 'none':
					data[0] = '0.0.0.0/0'
					
				if re.search('/', data[0]):
					tmp = data[0].split('/')
					ip = tmp[0]
					mask = tmp[1]
					if not ipvalidation.is_ipv4(ip):
						err = True
						errmsg = ip+" is not in a valid format! Aborting."
					
					try:
						if not int(mask) in range(0,33):
							err = True
							errmsg = "mask "+str(mask)+" is not in a valid format! Aborting."
					except:
						if ipvalidation.is_ipv4(mask):
							ipv4 = ipaddr.IPv4Network(ip+'/'+mask)
							newmask = int(ipv4.prefixlen)
							data = [ip+'/'+str(newmask)]
						else:
							err = True
							errmsg = "mask "+str(mask)+" is not in a valid format! Aborting."
							
					
					if not err:
						data_res = data
				else:
					errmsg = data[0]+" is not in a valid format! Aborting."
					err = True
						
		else:
			valid_params = ['ip', 'netmask']
			err = False
			netmask = ""
			ip = ""
			for entry in data:
				if not err:
					if not re.search(':', entry):
						err = True
						errmsg = "Data input is incorrect! Aborting."
					if not err:
						infos = entry.split(':')
						if infos[0] not in valid_params:
							err = True
							errmsg = str(infos[0])+" is not a valid parameter! Aborting."
						else:
							valid_params.pop(valid_params.index(infos[0]))
							if infos[0] == "ip":
								ip = infos[1]
							elif infos[0] == "netmask":
								netmask = infos[1]
					
					if not err:
						if not ipvalidation.is_ipv4(infos[1]):
							err = True
							errmsg = str(infos[1])+" is not in a valid format! Aborting."
					if err:
						#self.log.error(errmsg)
						self.output.error(errmsg)
			
			if 'ip' in valid_params or 'netmask' in valid_params:
				err = True
				errmsg = "IP and Netmask parameters must be filled."
			else:
				ipv4 = ipaddr.IPv4Network(ip+'/'+netmask)
				mask = int(ipv4.prefixlen)
				data_res = [ip+'/'+str(mask)]
		
		if err:
			#self.log.error(errmsg)
			self.output.error(errmsg)
		
		self.output.debug(str(data_res)+" validated")
		return data_res
	
	def get_boot(self):
		''' Get the boot IP '''
		dev = self._get_device_name()
		dev_ip=''
		dev_mask=''
		if os.path.exists('/etc/sysconfig/network-scripts/ifcfg-' + dev):
			lines = open('/etc/sysconfig/network-scripts/ifcfg-' + dev, 'r').readlines()
			for aline in lines:
				if re.search("^ *#", aline) or re.search("^ *!", aline) or re.search("^ *;", aline):
					continue
				if re.search('^IPADDR=', aline):
					config_args = aline.split('=', 1)
					if not config_args:
						continue
					if 'IPADDR' in config_args[0]:
						dev_ip=config_args[1].strip()
						dev_ip = re.sub(r'^"|"$|\n|\r', '',dev_ip)
				if re.search('^NETMASK=', aline):
					config_args = aline.split('=', 1)
					if not config_args:
						continue
					if 'NETMASK' in config_args[0]:
						dev_mask=config_args[1].strip()
						dev_mask = re.sub(r'^"|"$|\n|\r', '', dev_mask)
				if dev_ip and dev_mask:
					break
			
			if ipvalidation.is_ipv4(dev_ip) and ipvalidation.is_ipv4(dev_mask):
				ipv4 = ipaddr.IPv4Network(dev_ip+'/'+dev_mask)
				dev_mask = int(ipv4.prefixlen)
				ipv4 = dev_ip+'/'+str(dev_mask)
			else:
				ipv4 = "0.0.0.0/0"
			#return ipv4
			self.output.info(ipv4)
		
		return 0
	
	def get_active(self):
		try:
			''' MANDATORY ! 
			    define how to retreive the running config '''
			dev = self._get_device_name()
			dhclient_pid = self._dhclient_running(dev)
			netlib = ifconfig.Interface()
			ip = str(netlib.get_ip(dev))
			mask = str(netlib.get_netmask(dev))
			
			if ip != "None":
				ipv4 = ipaddr.IPv4Network(ip+'/'+mask)
				netmask = str(ipv4.netmask)
			else:
				ip = "None"
				netmask = "None"
			
			if dhclient_pid:
				output='dhcp'
			else:
				if ip == "None":
					ip = "0.0.0.0"
				output=ip+'/'+mask
		
		except:
			raise
		return output
	
	def get(self):
		try:
			''' MANDATORY ! 
			    define how to retreive the running config '''
			dev = self._get_device_name()
			dhclient_pid = self._dhclient_running(dev)
			netlib = ifconfig.Interface()
			ip = str(netlib.get_ip(dev))
			mask = str(netlib.get_netmask(dev))
			mac = str(netlib.get_mac(dev))
			
			if ip != "None":
				ipv4 = ipaddr.IPv4Network(ip+'/'+mask)
				netmask = str(ipv4.netmask)
			else:
				ip = "None"
				netmask = "None"
			self.output.title(dev+': HWaddr '+mac+'; IP:'+ip+'; Mask:'+netmask)
			
			if dhclient_pid:
				self.output.info("dhcp")
			else:
				if ip == "None":
					ip = "0.0.0.0"
				self.output.info(ip+'/'+mask)
		
		except:
			err = str(sys.exc_info()[1])
			#self.log.error("getting "+self.PluginName+": "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def set(self, data):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			# Set IP active
			self.set_active(data)
			# Set the boot IP
			self.set_boot(data)
		
		except:
			err = str(sys.exc_info()[1])
			#self.log.error("setting "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
		
		self.output.title(self.PluginName+' correctly set.')
		self.output.info(self.listToString(data))
		return 0
	
	def set_active(self, data):
		''' Set the active config only '''
		try:
			if not self.live_update:
				return 0
			
			dev = self._get_device_name()
			netlib = ifconfig.Interface()
			if self.live_update:
				# Check if device is a slaved interface.
				if netlib.is_bond_slave(dev):
					self.output.error(dev+' is part of a bond')
					self.output.error('You cannot assign an IP to a slaved interface.')
					return 1
			
			
			if data[0] == 'dhcp':
				self.output.debug("Setting DHCP client")
				
				if self.live_update :
					# Start dhclient
					self.output.debug("starting dhclient")
					dhclient_pid = self._dhclient_running(dev)
					if dhclient_pid:
						os.kill(int(dhclient_pid), signal.SIGKILL)
						time.sleep(5)
					self._start_dhclient(dev)
			else:
				self.output.debug("setting "+data[0])
				tmp = data[0].split('/')
				infos = {}
				infos['ip'] = tmp[0]
				infos['mask'] = tmp[1]
				ipv4 = ipaddr.IPv4Network(infos['ip']+'/'+infos['mask'])
				infos['netmask'] = str(ipv4.netmask)
					
				if self.live_update :
					# Kill dhclient process if needed
					dhclient_pid = self._dhclient_running(dev)
					if dhclient_pid:
						os.kill(int(dhclient_pid), signal.SIGKILL)
				
				if self.live_update :
					# set running configuration:
					self.output.debug("call set_ip "+infos['ip']+" to "+dev)
					netlib.set_ip(infos['ip'], dev)
					if infos['mask'] != "0":
						self.output.debug("call set_maskip "+infos['mask']+" to "+dev)
						netlib.set_netmask(int(infos['mask']), dev)
		
		except:
			err = str(sys.exc_info()[1])
			self.output.error(err)
			return 1
		
		return 0
	
	def set_boot(self, data):
		''' Set the boot IP only '''
		try:
			dev = self._get_device_name()
			netlib = ifconfig.Interface()
			if self.live_update:
				# Check if device is a slaved interface.
				if netlib.is_bond_slave(dev):
					self.output.error(dev+' is part of a bond')
					self.output.error('You cannot assign an IP to a slaved interface.')
					return 1
			
			ifcfg_lines = []
			tmp_lines = []
			if os.path.exists('/etc/sysconfig/network-scripts/ifcfg-'+dev):
				tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+dev, 'r').readlines()
			
			if data[0] == 'dhcp':
				self.output.debug("Setting DHCP client")
				if tmp_lines:
					proto_set = False
					for line in tmp_lines:
						toadd = True
						if re.search('^BOOTPROTO=', line):
							line = 'BOOTPROTO="dhcp"\n'
							proto_set = True
						elif re.search('^IPADDR=', line):
							toadd = False
						elif re.search('^NETMASK=', line):
							toadd = False
						elif re.search('^GATEWAY=', line):
							toadd = False
						
						if toadd:
							ifcfg_lines.append(line)
					
					if not proto_set:
						ifcfg_lines.append('BOOTPROTO="dhcp"\n')
				else:
					ifcfg_lines.append('DEVICE="'+dev+'"\n')
					ifcfg_lines.append('BOOTPROTO="dhcp"\n')
					ifcfg_lines.append('ONBOOT="yes"\n')
				
			else:
				self.output.debug("setting "+data[0])
				tmp = data[0].split('/')
				infos = {}
				infos['ip'] = tmp[0]
				infos['mask'] = tmp[1]
				ipv4 = ipaddr.IPv4Network(infos['ip']+'/'+infos['mask'])
				infos['netmask'] = str(ipv4.netmask)
				if infos['ip'] == "0.0.0.0":
					plg_path = re.sub('.ip$', '', self.PluginFqn)
					res = self.executePluginLater(plg_path+".gateway", "set", "none")
					
				# set cold configuration
				if tmp_lines:
					ip_set = False
					mask_set = False
					proto_set = False
					gw_set = False
					for line in tmp_lines:
						toadd = True
						if re.search('^BOOTPROTO=', line):
							line = 'BOOTPROTO="static"\n'
							proto_set = True
						elif re.search('^IPADDR=', line):
							ip_set = True
							if infos['ip'] != "0.0.0.0":
								line = 'IPADDR="'+infos['ip']+'"\n'
							else:
								line = ''
						
						elif re.search('^NETMASK=', line):
							mask_set = True
							if infos['mask'] != '0': 
								line = 'NETMASK="'+infos['netmask']+'"\n'
							else:
								line = ''
						
						elif re.search('^GATEWAY=', line):
							if infos.has_key('gateway'):
								line = 'GATEWAY="'+infos['gateway']+'"\n'
								gw_set = True
							else:
								toadd = False
						if toadd:
							ifcfg_lines.append(line)
					
					if not proto_set:
						ifcfg_lines.append('BOOTPROTO="static"\n')
					if not ip_set and infos['ip'] != "0.0.0.0":
						ifcfg_lines.append('IPADDR="'+infos['ip']+'"\n')
					if not mask_set and infos['mask'] != '0':
						ifcfg_lines.append('NETMASK="'+infos['netmask']+'"\n')
					if infos.has_key('gateway') and not gw_set:
						ifcfg_lines.append('GATEWAY="'+infos['gateway']+'"\n')
				else:
					ifcfg_lines.append('DEVICE="'+dev+'"\n')
					ifcfg_lines.append('BOOTPROTO="static"\n')
					if infos['ip'] != "0.0.0.0":
						ifcfg_lines.append('IPADDR="'+infos['ip']+'"\n')
					if infos['mask'] != '0':
						ifcfg_lines.append('NETMASK="'+infos['netmask']+'"\n')
					ifcfg_lines.append('ONBOOT="yes"\n')
					if infos.has_key('gateway'):
						ifcfg_lines.append('GATEWAY="'+infos['gateway']+'"\n')
			
			open('/etc/sysconfig/network-scripts/ifcfg-'+dev, 'w').writelines(ifcfg_lines)
			os.chmod('/etc/sysconfig/network-scripts/ifcfg-'+dev, 0440)
		
		except:
			err = str(sys.exc_info()[1])
			self.output.error(err)
			return 1
		
		return 0
	
	def _dhclient_running(self, device):
		ret = None
		pid = ''
		if os.path.exists('/var/run/dhclient-'+device+'.pid'):
			with open('/var/run/dhclient-'+device+'.pid', 'r') as f:
				pid = f.readline().strip()
		if pid:
			cmdline = ''
			if os.path.exists('/proc/'+pid):
				with open('/proc/'+pid+'/cmdline', 'r') as f:
					cmdline = f.readline()
					if device in cmdline:
						ret = pid
		return ret
	
	def _start_dhclient(self, device):
		cmdline = '/sbin/dhclient -lf /var/lib/dhclient/dhclient-'+device+'.leases -pf /var/run/dhclient-'+device+'.pid '+device+' &'
		os.system(cmdline)
	
	def ip(self, data):
		''' function associated with the option previously defined in getopts 
	        You must have one function for each option ''' 
		try: 
			if data == 'dhcp':
				self.set([data])
			else:
				self.updateCurrentConfigNewValue(['ip:'+data])
		except:
			err = str(sys.exc_info()[1])
			#self.log.error(self.PluginName+" --mask "+data+" : "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def mask(self, data):
		''' function associated with the option previously defined in getopts 
		    You must have one function for each option ''' 
		try: 
			self.updateCurrentConfigNewValue(['netmask:'+data])
		except:
			err = str(sys.exc_info()[1])
			#self.log.error(self.PluginName+" --mask "+data+" : "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def gate(self, data):
		''' function associated with the option previously defined in getopts 
	        You must have one function for each option ''' 
		try: 	
			self.updateKeyListEntry(['gateway:'+data])
		except:
			err = str(sys.exc_info()[1])
			#self.log.error(self.PluginName+" --gate "+data+" : "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def _get_device_name(self):
		dev = re.sub('.*conf.', '', re.sub('.ip$', '', self.PluginFqn))
		if re.search('^vlan', dev):
			tmpstr = dev
			dev = re.sub('vlans.', '', tmpstr)
		if re.search('^bonds', dev):
			tmpstr = dev
			dev = re.sub('bonds.', '', tmpstr)
		if re.search('^aliases', dev):
			tmpstr = dev
			dev = re.sub('aliases.', '', tmpstr)
		return dev
	
	def updateCurrentConfigNewValue(self, data_list, separator = ':'):
		'''
			Takes the parameter of a short set command, ip or mask
			retrieve current configuration,change it with the new setting
			and set the new valid config
			Input:
			data_list contains a list of Key:Values.
			By default a Key and a Value is separated by ":".
			ip:1.1.1.1
			netmask:255.255.255.255
			gateway:10.165.20.1
			The separator can be overwriten by the "separator" parameter.
			Note that the separator must be the same that the one used in the original configuration.
		'''
		try:
			#keeps current config
			dic = {'ip':'0.0.0.0','netmask':'0'}
			#Get the current configuration
			org_list = self.getConfig().split(' ')
			
			IP_POS=0
			MASK_POS=1
			#get the current configured ip
			for entry in org_list:
				 if re.search('/', entry):
					 curr_ip = entry.split('/')
					 dic['ip']=curr_ip[IP_POS]
					 dic['netmask']=curr_ip[MASK_POS]
			
			#get the new config and change the old
			for newEntry in data_list:
				key_type,key = newEntry.split(separator)
				if re.search('/', key):
					ip_addr = key.split('/')
					dic['ip']=ip_addr[IP_POS]
					dic['netmask']=ip_addr[MASK_POS]
				else:
					if key_type == 'ip' or key_type == 'netmask':
						dic[key_type] = key
					elif key_type == 'gateway':
						self.log.error("Unsupported option gateway")
					else:
						self.log.error("Unsupported option in updateCurrentConfigNewValue")
						#todo
			
			
			# Finaly recreate the list with the updated content 
			list = []
			list.append(dic['ip']+'/'+dic['netmask'])
			self.set(list)
		except:
			err = str(sys.exc_info()[1])
			self.log.error("updateKeyListEntry "+self.PluginName+": "+err)
			self.output.error(err)
			return 1
		return 0
	
	def addSimpleListEntry(self, data_list):
		''' add data_list to plugin entry of type List.
			data_list contains a list of simple values to add.
		'''
		try:
			org_list = self.getConfig().split(',')
			org_list.extend(data_list)
			self.set(org_list)
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error("addSimpleListEntry "+self.PluginName+": "+err)
			self.output.error(err)
			return 1
		
		return 0


