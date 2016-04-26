#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import ifconfig
from includes import *
import os
import sys
import re
import subprocess


class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin
		'''
		dic = []
		### OPTION: set
		opt0 = {}
		opt0['name'] = '--set'
		opt0['metavar'] = 'DEV:STATE'
		opt0['action'] = 'store'
		opt0['nargs'] = '+'
		opt0['help'] = 'Set devices states (either up or down)'
		dic.append(opt0)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: all [up down]
		opt1 = {}
		opt1['name'] = '--all'
		opt1['metavar'] = 'STATE'
		opt1['action'] = 'store'
		#opt1['nargs'] = '?'
		opt1['help'] = 'Set all devices on STATE [up/down].'
		dic.append(opt1)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: up
		opt1 = {}
		opt1['name'] = '--up'
		opt1['metavar'] = 'DEVICE'
		opt1['action'] = 'store'
		opt1['nargs'] = '+'
		opt1['help'] = 'Activate one or more device.'
		dic.append(opt1)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: down
		opt1 = {}
		opt1['name'] = '--down'
		opt1['metavar'] = 'DEVICE'
		opt1['action'] = 'store'
		opt1['nargs'] = '+'
		opt1['help'] = 'Deactivate one or more device.'
		dic.append(opt1)
		
		return dic
	
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" configuration"
		msg = "Activate or deactivate physical network interfaces.\n"
		msg += "--set ETH:STATE ETH:STATE ... \n"
		msg += "                  : take a list of interfaces devices with their associated state,\n"
		msg += "                    eg: --set eth0:up eth1:down \n"
		msg += "                    You can also use the option --all to set all devices at once,\n"
		msg += "                    see below.\n"
		msg += " \n"
		msg += "--all [up/down]   : Set all devices at once. eg --all up \n"
		msg += "--up ETH ETH...   : takes one or more interfaces to activate \n"
		msg += "--down ETH ETH... : takes one or more interfaces to deactivate \n"
		msg += " NB: It is mandatory to first activate a device before being able to proceed with its configuration.\n"
		self.output.help(title, msg)
	
	def get_active(self):
		''' get the active state in a list'''
		try:
			netlib = ifconfig.Interface()
			devlist = netlib.list_ifs()
			devStates = []
			for adev in sorted(devlist):
				if netlib.is_up(adev):
					state = 'up'
				else:
					state = 'down'
				if adev+':'+state not in devStates:
					devStates.append(adev+':'+state)
		except:
			raise
		
		return devStates
	
	def get(self):
		try:
			''' MANDATORY ! 
			    define how to retreive the running config '''
			
			devStates = self.get_active()
			
			netlib = ifconfig.Interface()
			devlist = netlib.list_ifs()
			bootStates = ''
			dev_list = []
			for adev in sorted(devlist):
				onboot = 'down'
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+adev):
					for line in open('/etc/sysconfig/network-scripts/ifcfg-'+adev).readlines():
						if "ONBOOT" in line:
							args = line.split("=")
							if "yes" in args[1]:
								onboot = "up"
				
				if adev+':'+onboot not in dev_list:
					dev_list.append(adev+':'+onboot)
			
			runStates = ' '.join(devStates)
			bootStates = ' '.join(dev_list)
			self.output.title("Links state:")
			self.output.info(runStates)
			self.output.title("Onboot setup:")
			self.output.info(bootStates)
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error(self.PluginName+" --get: "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def isDeviceConfigured(self,device):
		current_config = self.get_current_config(self.PluginFqn)
		for entry in current_config:
			if  re.search(':', entry):
				dev_opt = entry.split(':')
				config_device=dev_opt[0]
				#state=dev_opt[1]
				if (device == config_device):
					return True
		return False
	
	def inputValidation(self, data):
		try: 
			netlib = ifconfig.Interface()
			netDevs = netlib.list_ifs()
			## Check that data input is correct
			for info in data:
				if not re.search(':', info):
					raise ValueError('Data input %s is not correct. Should be DEV:up or DEV:down.Aborting' %(info))
				dev_opt = info.split(':')
				device=dev_opt[0]
				state=dev_opt[1]
				if state not in ["up", "down"]:
					raise ValueError('State %s is not correct.Can be up or down!Aborting' %state)
				
				# device does not exist
				if device not in netDevs:
					# in case eth was already configured allow down for config  update
					if not (self.isDeviceConfigured(device) and  state == "down"):
						raise ValueError('Device %s does not exist!Aborting' %(device))
		except:
			self.printError("")
			return None
		
		return data
	
	def set(self, data):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			netlib = ifconfig.Interface()
			netDevs = netlib.list_ifs()
			for info in data:
				dev = info.split(':')
				device = dev[0]
				state = dev[1]
				
				if state == "up":
					netlib.up(device)
					onboot="yes"
					self.createPlugin("network/plugin_ip.py", "net.conf."+device+".ip")
					self.createPlugin("network/iface_gateway.py", "net.conf."+device+".gateway")
				else:
					# if still active shutdown
					if device in netDevs:
						netlib.down(device)
					else:
						self.output.warning("Device %s does not exist. Configuration will be updated only" %device)
					
					onboot="no"
					self.removePlugin("net.conf."+device+".ip")
					self.removePlugin("net.conf."+device+".gateway")
			
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+device):
					final_lines = []
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+device, 'r').readlines()
					for line in tmp_lines:
						if "ONBOOT" in line:
							line = 'ONBOOT="'+onboot+'"\n'
						if not "NM_CONTROLLED" in line:
							final_lines.append(line)
					
					line = 'NM_CONTROLLED=no\n'
					final_lines.append(line)
					open('/etc/sysconfig/network-scripts/ifcfg-'+device, 'w').writelines(final_lines)
				else:
					lines = []
					lines.append('DEVICE="'+device+'"\n')
					lines.append('ONBOOT="'+onboot+'"\n')
					lines.append('NM_CONTROLLED=no\n')
					open('/etc/sysconfig/network-scripts/ifcfg-'+device, 'w').writelines(lines)
				
				os.chmod('/etc/sysconfig/network-scripts/ifcfg-'+device, 0440)
				self.output.info(device+" set to "+state)
				
		except:
			err = str(sys.exc_info()[1])
			self.log.error("setting "+self.PluginName+" "+str(data)+": "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def check(self):
		''' The fucntion is overwriten because we only check agains Onboot setup 
			we also remove commas in the get function '''
		self.output.disable()
		self.get()
		tmpinfos = self.messages["info"]
		if tmpinfos:
			info = re.sub(',', '', tmpinfos[1])
		else:
			info = ''
		self.output.clear_messages()
		self.output.enable()
		self._check(info_get=info)
	
	def all(self, data=''):
		''' function associated with the option previously defined in getopts 
	        You must have one function for each option ''' 
		try: 
			if data in ["up", "down"]:
				netlib = ifconfig.Interface()
				netDevs = netlib.list_ifs()
				input = []
				for dev in sorted(netDevs):
					input.append(dev+':'+data)
				self.set(input)
							
			else:
				errmsg = str(data)+" is not a correct input! Aborting."
				self.log.error(errmsg)
				self.output.error(errmsg)
				return 1
		
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error("all "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def modify(self, data, state):
		try:
			list = []
			for adev in data:
				list.append(adev+':'+state)
			self.updateKeyListEntry(list)
		except:
			err = str(sys.exc_info()[1])
			self.log.error("all "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def up(self, data):
		self.modify(data, "up")
	
	def down(self, data):
		self.modify(data, "down")
	
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


