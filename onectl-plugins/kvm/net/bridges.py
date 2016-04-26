#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import ifconfig
from includes import bash
from includes import regexp
import os
import sys
import re
import subprocess
import inspect

class PluginControl(pluginClass.Base):

# self.output => screen output
# Available outputs:
# self.output.title, self.output.info, self.output.error, self.output.warning, self.output.debug
# Output messages are stored in self.messages dictionnary that contains the
# following List entries: self.messages["info"], self.messages["error"],
# self.messages["warning"], self.messages["error"]
#
# self.log => logger
# Available logs :
# #self.log.error, self.log.warning, self.log.info, self.log.debug


	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		
		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'bridgeX:ethX,ethY'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Set bridgeing devices'
		dic.append(opt)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: add
		opt = {}
		opt['name'] = '--add'
		opt['metavar'] = 'bridgeX:ethX,ethY'
		opt['action'] = 'store'
		#opt['nargs'] = '+'
		opt['help'] = 'Add a bridge.'
		dic.append(opt)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: remove
		opt = {}
		opt['name'] = '--remove'
		opt['metavar'] = 'bridgeX'
		opt['action'] = 'store'
		#opt['nargs'] = '+'
		opt['help'] = 'Remove a bridge.'
		dic.append(opt)
		
		return dic
	
	def info(self):
		title = self.PluginName+" configuration"
		msg = "Activate or deactivate bridgeing interfaces.\n"
		msg += "--set [bridgeX bridgeY ...] : take the list of bridgeing interfaces to create.\n"
		msg += "                              eg: --set ovsbr0 ovsbr1\n"
		msg += '                              NB: "none" keyword can be used to remove all bridges.\n'
		msg += " \n"
		msg += "--add  bridgeX              : Add a bridge \n"
		msg += "--remove  bridgeX           : Remove a bridge \n"
		self.output.help(title, msg)
	
	def get(self):
		try:
			''' MANDATORY !
			    define how to retreive the running config '''
			br_list = self.get_existing_bridges()
			
			if len(br_list) == 0:
				self.output.title("No bridge")
				self.output.info("none")
			else:
				self.output.title("Setup:")
				self.output.info(' '.join(br_list))
			
		except:
			err = str(sys.exc_info()[1])
			#self.log.error(self.PluginName+" --get: "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def get_existing_bridges(self):
		try:
			br_list = []
			ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
			for afile in ifcfg_list:
				if "ifcfg-" in afile:
					br_if = ''
					for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
						if re.search('TYPE *= *?OVSBridge', line):
							br_if = re.sub('.*ifcfg-', '', afile)
							br_list.append(br_if)
			
			br_list.sort()
			
		except:
			err = str(sys.exc_info()[1])
			self.output.error(err)
		
		return br_list
	
	def inputValidation(self, data):
		try:
			self.output.debug('Configuring bridges: '+str(data))
			# Check first for 'none' keyword
			# if present then return an empty list
			if data[0] == "none":
				return data
			
			## Check that data input is correct
			for info in data:
				err = False
				if not re.match(regexp.IFNAME, info):
					errmsg = "Data input is incorrect! Aborting."
					self.output.error(errmsg)
					return None
		except:
			err = str(sys.exc_info()[1])
			##self.log.error("setting "+self.PluginName+" "+str(data)+": "+err)
			self.output.error(err)
			return None
		
		return data
	
	def set(self, data):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			# Check for "none" keyword
			if data[0] == "none":
				data = []
			
			# Remove uneeded ifcfg-bridgex files
			self.remove_uneeded_cfg(data)
			self.output.debug("Removed uneeded ifcfg files")
			
			file = inspect.getfile(self.__class__)
			base = re.sub('/plugins.*', '', file)
			plg_path = os.path.join(base, "plugins/net/conf/bridges")
			## remove bridges plugins
			# Get the current config and remove plugins
			conf_list = self.get_current_config(self.PluginFqn)
			
			# For each entry in current config remove associated plugins
			for entry in conf_list:
				if entry == 'none':
					continue
				rm_bridge = entry.split(':')[0]
				self.removePlugin("net.conf.bridges."+rm_bridge+".mgnt.ip")
				self.removePlugin("net.conf.bridges."+rm_bridge+".access")
				self.removePlugin("net.conf.bridges."+rm_bridge+".mgnt.vlan")
			
			# Delete all plugin in plugins/net/conf/bridges has they will be recreated
			os.system('rm -rf '+plg_path)
			# if live: Remove existing bridges that are not in use anymore
			if self.live_update:
				br_list = self.get_existing_bridges()
				for bridge in br_list:
					if bridge not in data:
						res, err = self.sh_command('ovs-vsctl --if-exists del-br '+bridge)
			
			# proceed with bridge creation
			for bridge in data:
				ip_set = False
				vlan_set = False
				
				# Create bridge associated plugin
				self.output.debug("Creating bridge "+bridge+" plugin")
				dest_path = os.path.join(plg_path, bridge)
				os.makedirs(dest_path)
				self.createPlugin("kvm/template_ovsbr.py", "net.conf.bridges."+bridge+".access")
				self.createPlugin("kvm/template_ovsbr.py", "net.conf.bridges."+bridge+".mgnt.vlan")
				self.createPlugin("kvm/template_ovsbr.py", "net.conf.bridges."+bridge+".mgnt.ip")
				self.output.debug("bridge "+bridge+" plugin created")
				# Create ifcfg
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+bridge):
					final_lines = []
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+bridge, 'r').readlines()
					ip = ""
					netmask = ""
					for line in tmp_lines:
						if re.match('^IPADDR', line):
							args = line.split('=')
							ip = re.sub('"','',args[1]).strip()
						elif re.match('^NETMASK', line):
							args = line.split('=')
							netmask = re.sub('"','',args[1]).strip()
						elif re.match('OVSBOOTPROTO.*dhcp', line):
							self.executePluginLater("net.conf.bridges."+bridge+".mgnt.ip", "set", 'dhcp')
							ip_set = True
						elif re.match('^OVSDHCPINTERFACES', line):
							args = line.split('=')
							iface = re.sub('"','',args[1]).strip()
							self.executePluginLater("net.conf.bridges."+bridge+".access", "set", iface)
					if ip and netmask:
						self.executePluginLater("net.conf.bridges."+bridge+".mgnt.ip", "set", ip+"/"+netmask)
						ip_set = True
				
				lines = []
				lines.append('DEVICE="'+bridge+'"\n')
				lines.append('ONBOOT=yes\n')
				lines.append('BOOTPROTO=none\n')
				lines.append('DEVICETYPE=ovs\n')
				lines.append('TYPE=OVSBridge\n')
				lines.append('HOTPLUG=no\n')
				open('/etc/sysconfig/network-scripts/ifcfg-'+bridge, 'w').writelines(lines)
				os.chmod('/etc/sysconfig/network-scripts/ifcfg-'+bridge, 0440)
				self.output.info("added bridge "+bridge)
				if not ip_set:
					self.executePluginLater("net.conf.bridges."+bridge+".mgnt.ip", "set", "none")
				if not vlan_set:
					self.executePluginLater("net.conf.bridges."+bridge+".mgnt.vlan", "set", "none")
			
			# Search for OVSPorts already attached to the listed OVS Bridges
			ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
			for afile in ifcfg_list:
				if "ifcfg-" in afile:
					iface = re.sub('ifcfg-', '',afile)
					if iface not in data:
						ovsport = False
						ovsbr = ""
						for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
							if re.search('^TYPE *= *?OVSPort', line):
								ovsport = True
							elif re.search('^OVS_BRIDGE *= ', line):
								args = line.split('=')
								ovsbr = re.sub('"','',args[1]).strip()
						if ovsport :
							if ovsbr in data:
								self.executePluginLater("net.conf.bridges."+ovsbr+".access", "set", iface)
							else:
								# Remove OVS ref on an used interface
								lines = []
								lines.append('DEVICE="'+iface+'"\n')
								lines.append('ONBOOT=yes\n')
								lines.append('BOOTPROTO=none\n')
								lines.append('HOTPLUG=no\n')
								open('/etc/sysconfig/network-scripts/ifcfg-'+iface, 'w').writelines(lines)
								os.chmod('/etc/sysconfig/network-scripts/ifcfg-'+iface, 0440)
			
			
		except:
			err = str(sys.exc_info()[1])
			##self.log.error("setting "+self.PluginName+" "+str(data)+": "+err)
			self.output.error(err)
			return 1
		return 0
	
	def add(self, data=''):
		''' Add a bridge '''
		try:
			conf_list = self.get_current_config(self.PluginFqn)
			if 'none' in conf_list:
				conf_list.pop(0)
			
			toadd = []
			if type(data) is list:
				toadd = data
			else:
				toadd.append(data)
			for adev in list(toadd):
				if adev in conf_list:
					toadd.remove(adev)
			
			conf_list.extend(toadd)
			self.output.disable()
			res = self.set(sorted(conf_list))
			self.output.enable()
			if res > 0:
				errors = self.messages['error']
				self.clear_messages()
				for err in errors:
					self.output.error(err)
				return 1
			else:
				for adev in toadd:
					infos = adev.split(':')
					self.output.info("added bridge "+infos[0])
		
		except:
			err = str(sys.exc_info()[1])
			#self.log.error(self.PluginName+" --add "+data+": "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def remove(self, data=''):
		''' Delete a bridge '''
		try:
			# get current configuration saved in ncxctl
			conf_list = self.get_current_config(self.PluginFqn)
			
			todel = []
			if type(data) is list:
				todel = data
			else:
				todel.append(data)
			
			
			for entry in todel:
				nothing_todo = True
				for aconf in list(conf_list):
					bridge_name = aconf.split(':')[0]
					if entry == bridge_name:
						nothing_todo = False
						conf_list.remove(aconf)
			
			if nothing_todo:
				self.output.warning('there is no bridge to remove !')
				return 0
			
			if len(conf_list) == 0:
				conf_list = ['none']
			
			self.output.disable()
			self.set(sorted(conf_list))
			self.output.enable()
			if len(self.messages['error']) > 0:
				errors = self.messages['error']
				self.clear_messages()
				for err in errors:
					self.output.error(err)
				return 1
			else:
				for adev in todel:
					self.output.info("removed bridge "+adev)
			
		except:
			err = str(sys.exc_info()[1])
			#self.log.error(self.PluginName+" --del "+data+": "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def ListToString(self, list):
		return ','.join(list)
	
	def remove_uneeded_cfg(self, data):
		ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
		bridge_list = {}
		for afile in sorted(ifcfg_list):
			if "ifcfg-" in afile:
				is_bridge = ''
				target_br = ''
				for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
					if re.search('^TYPE *= *"*OVSBridge', line):
						is_bridge = re.sub('.*ifcfg-', '', afile)
					if re.search("^OVS_BRIDGE *=", line):
						target_br = line.split('=')[1].strip('"').strip()
				
				# if the device is attached to bridge that is NOT part of the bridges to create then remove it
				if target_br and target_br not in data:
					bash.run('perl -p -i -e s/^OVS_BRIDGE./OVS_BRIDGE=/ /etc/sysconfig/network-scripts/'+afile)
				# if the device is a bridge and is NOT part of the bridges to create then remove it
				if is_bridge and is_bridge not in data:
					self.output.debug("Removing "+afile)
					os.remove("/etc/sysconfig/network-scripts/"+afile)
	
