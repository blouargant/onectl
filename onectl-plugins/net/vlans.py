#!/usr/bin/python -u
# Name: fqn.plugin.name

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
		''' Create additional argument parser options
			specific to the plugin '''
	
		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'DEV:STATE'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Set VLAN devices'
		dic.append(opt)
	
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: add
		opt = {}
		opt['name'] = '--add'
		opt['metavar'] = 'VLAN_ID'
		opt['action'] = 'store'
		#opt['nargs'] = '+'
		opt['help'] = 'Add a vlan VLAN_ID.'
		dic.append(opt)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: remove
		opt = {}
		opt['name'] = '--remove'
		opt['metavar'] = 'VLAN_ID'
		opt['action'] = 'store'
		#opt['nargs'] = '+'
		opt['help'] = 'Remove vlan VLAN_ID.'
		dic.append(opt)
		
		return dic
	
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" configuration"
		msg = "Activate or deactivate VLAN interfaces.\n"
		msg += "--set ETHX.VID1 ETHX.VID2 ... \n"
		msg += "                   : take the list of VLAN interfaces to create.\n"
		msg += "                     eg: --set eth0.100 eth1.200 \n"
		msg += '                     NB: "none" keyword can be used to remove all vlans.\n'
		msg += " \n"
		msg += "--add  ETHX.VID    : Add a vlan \n"
		msg += "--remove  ETHX.VID : Remove a vlan \n"
		msg += " NB: It is mandatory to first activate a vlan before being able to proceed with its configuration.\n"
		self.output.help(title, msg)
	
	def get_active(self):
		try:
			''' get the active config in a list '''
			netlib = ifconfig.Interface()
			devlist = netlib.list_ifs(False)
			RunningVlans = ''
			vlan_list = []
			for adev in sorted(devlist):
				if netlib.is_vlan(adev):
					if netlib.is_up(adev) and adev not in vlan_list:
						vlan_list.append(adev)
			
			#RunningVlans = ' '.join(vlan_list)
		except:
			raise
		return vlan_list
	
	def get(self):
		try:
			''' MANDATORY ! 
			    define how to retreive the running config '''
			
			RunningVlans = self.get_active()
			netlib = ifconfig.Interface()
			devlist = netlib.list_ifs(False)
			onBootVlans = ''
			vlan_list = []
			for adev in sorted(devlist):
				if netlib.is_vlan(adev):
					onboot = False
					if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+adev):
						for line in open('/etc/sysconfig/network-scripts/ifcfg-'+adev).readlines():
							if "ONBOOT" in line:
								if not re.search("=", line):
									continue
								args = line.split("=")
								if "yes" in args[1]:
									onboot = True
					
					if onboot and adev not in vlan_list:
						vlan_list.append(adev)
			onBootVlans = ' '.join(vlan_list)
			
			if not RunningVlans:
				self.output.title("No running vlans")
				self.output.info("none")
			else:
				self.output.title("Running vlans:")
				self.output.info(' '.join(RunningVlans))
			
			if not onBootVlans:
				self.output.title("No onboot vlans")
				self.output.info("none")
			else:
				self.output.title("Onboot setup:")
				self.output.info(onBootVlans)
		
		
		except:
			err = str(sys.exc_info()[1])
			#self.log.error(self.PluginName+" --get: "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def inputValidation(self, data):
		try:
			data=self.validate_input_data(data)
			self.output.debug("Checking input :" + str(data))
			# Check first for 'none' keyword
			# if present then return an empty list
			if not data[0]:
				data[0] = "none"
			if data[0] == "none":
				return data
			
			
			netlib = ifconfig.Interface()
			netDevs = netlib.list_ifs(False)
			## Check that data input is correct
			for info in data:
				if info == 'none':
					continue
				dev = info.split('.')
				VID = dev[1]
				PHYSDEV = dev[0]
				err = False
				if not re.search('\.', info):
					err = True
					errmsg = "Data input is incorrect! Aborting."
				if not err:
					if int(VID) > 0 and int(VID) < 4095:
						err =False
					else:
						err = True
						errmsg = VID+" is not a valid VLAN id."
				if err:
					#self.log.error(errmsg)
					self.output.error(errmsg)
					return None
		except:
			err = str(sys.exc_info()[1])
			#self.log.error("setting "+self.PluginName+" "+str(data)+": "+err)
			self.output.error(err)
			return None
		
		
		self.output.debug("Data is OK")
		return data
		
	def set(self, data):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			data=self.validate_input_data(data)
			# Check for "none" keyword
			if data[0] == "none":
				data = []
			
			file = inspect.getfile(self.__class__)
			base = re.sub('/plugins.*', '', file)
			path = os.path.join(base, "plugins/net/conf/vlans")
			
			self.output.debug("setting vlans: "+str(data))
			netlib = ifconfig.Interface()
			existing_vlans = netlib.list_vlans()
			## remove all VLANs before anything
			#os.system('rm -rf '+path)
			
			# first check that everything is ok
			for info in data:
				if info == 'none':
					continue
				dev = info.split('.')
				VID = dev[1]
				PHYSDEV = dev[0]
				# Check if main device is a bond slave
				if netlib.is_bond_slave(PHYSDEV):
					self.output.error(PHYSDEV+' is part of a bond')
					self.output.error('You cannot create a vlan on a slaved interface.')
					return 1
				
				if self.live_update:
					# Check if main device is up
					if not netlib.is_up(PHYSDEV):
						self.output.debug("bring up "+str(PHYSDEV))
						if re.search('^bond', PHYSDEV):
							msg = self.executePlugin("net.bonds", "add", [PHYSDEV])
							if re.search('Error :', msg):
								self.output.error(msg)
								return 1
						else:
							msg = self.executePlugin("net.devices", "up", [PHYSDEV])
							if re.search('Error :', msg):
								self.output.error(msg)
								return 1
						#netlib.up(PHYSDEV)
				
				# Finaly check that main device is available	
					netDevs = netlib.list_ifs(False)
					if PHYSDEV not in netDevs:
						self.output.error("Device "+PHYSDEV+" does not exist! Aborting.")
						return 1
			
			if self.live_update:
				for avlan in existing_vlans:
					if avlan not in data:
						netlib.del_vlan(avlan)
			
			## remove vlans plugins
			self.show(verbose=False)
			msg = self.messages["info"]
			if len(msg) > 0:
				configured = msg[0].strip()
				if len(configured) > 0:
					conf_list = configured.split(' ')
				else:
					conf_list = []
				for entry in conf_list:
					self.removePlugin("net.conf.vlans."+entry+".ip")
					self.removePlugin("net.conf.vlans."+entry+".gateway")
			
			self.output.clear_messages()
			
			ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
			for afile in ifcfg_list:
				if "ifcfg-" in afile:
					for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
						if 'VLAN="yes"' in line:
							vlan_if = re.sub('.*ifcfg-', '', afile)
							if vlan_if not in data:
								self.output.debug("removing "+str(afile))
								os.remove("/etc/sysconfig/network-scripts/"+afile)
			
			for info in data:
				if info == 'none':
					continue
				self.output.debug("adding vlan "+str(info))
				dev = info.split('.')
				VID = dev[1]
				PHYSDEV = dev[0]
				onboot="yes"
				dest_path = os.path.join(path, PHYSDEV+"/"+VID)
				#os.makedirs(dest_path)
				self.createPlugin("network/plugin_ip.py", "net.conf.vlans."+PHYSDEV+"."+VID+".ip")
				self.createPlugin("network/iface_gateway.py", "net.conf.vlans."+PHYSDEV+"."+VID+".gateway")
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+PHYSDEV+"."+VID):
					final_lines = []
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+PHYSDEV+'.'+VID, 'r').readlines()
					for line in tmp_lines:
						if "ONBOOT=" in line:
							line = 'ONBOOT="'+onboot+'"\n'
						if "PHYSDEV=" in line:
							line = 'PHYSDEV="'+PHYSDEV+'"\n'
						final_lines.append(line)
					
					open('/etc/sysconfig/network-scripts/ifcfg-'+PHYSDEV+'.'+VID, 'w').writelines(final_lines)
				else:
					lines = []
					lines.append('VLAN="yes"\n')
					lines.append('DEVICE="'+PHYSDEV+'.'+VID+'"\n')
					lines.append('ONBOOT="'+onboot+'"\n')
					lines.append('PHYSDEV="'+PHYSDEV+'"\n')
					lines.append('TYPE=Ethernet\n')
					lines.append('NM_CONTROLLED=no\n')
					open('/etc/sysconfig/network-scripts/ifcfg-'+PHYSDEV+'.'+VID, 'w').writelines(lines)
				
				os.chmod('/etc/sysconfig/network-scripts/ifcfg-'+PHYSDEV+'.'+VID, 0440)
				
				if self.live_update:
					if not netlib.is_up(info):
						self.output.debug("adding vlan "+VID+" to device "+PHYSDEV)
						err = netlib.add_vlan(PHYSDEV, VID)
						if err:
							self.output.error("Enable to configure vlan "+str(info)+": "+err)
						else:
							netlib.up(info)
				
				#self.output.info("vlan set"+VID+" to "+PHYSDEV)
					
		except:
			err = str(sys.exc_info()[1])
			#self.log.error("setting "+self.PluginName+" "+str(data)+": "+err)
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
	
	def add(self, data=''):
		''' Add a vlan ''' 
		try:
			toadd=self.validate_input_data(data)
			conf_list = self.get_current_config(self.PluginFqn)
			
			for adev in toadd:
				if adev in conf_list:
					toadd.remove(adev)
			
			conf_list.extend(toadd)
			self.output.disable()
			res = self.set(sorted(conf_list))
			self.output.enable()
			if res > 0:
				return 1
			else:
				for adev in toadd:
					infos = adev.split('.')
					self.output.info("vlan added "+infos[1]+" to "+infos[0])
		
		except:
			err = str(sys.exc_info()[1])
			#self.log.error(self.PluginName+" --add "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def remove(self, data=''):
		''' Delete a vlan ''' 
		try:
			todel=self.validate_input_data(data)
			conf_list = self.get_current_config(self.PluginFqn)
			
			for entry in todel:
				if entry in conf_list:
					conf_list.remove(entry)
			
			if len(conf_list) == 0:
				conf_list = ['none']
			
			self.output.disable()
			self.set(sorted(conf_list))
			self.output.enable()
			if len(self.messages['error']) > 0:
				return 1
			else:
				for adev in todel:
					infos = adev.split('.')
					self.output.info("removed vlan "+infos[1]+" on "+infos[0])
		
		except:
			err = str(sys.exc_info()[1])
			#self.log.error(self.PluginName+" --del "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0




