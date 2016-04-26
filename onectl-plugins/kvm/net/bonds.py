#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import ifconfig
from includes import bash
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
# self.log.error, self.log.warning, self.log.info, self.log.debug


	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		
		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'bondX:ethX,ethY'
		opt['action'] = 'store'
		opt['nargs'] = '+'
		opt['help'] = 'Set Bonding devices'
		dic.append(opt)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: add
		opt = {}
		opt['name'] = '--add'
		opt['metavar'] = 'bondX:ethX,ethY'
		opt['action'] = 'store'
		#opt['nargs'] = '+'
		opt['help'] = 'Add a Bond.'
		dic.append(opt)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: remove
		opt = {}
		opt['name'] = '--remove'
		opt['metavar'] = 'bondX'
		opt['action'] = 'store'
		#opt['nargs'] = '+'
		opt['help'] = 'Remove a Bond.'
		dic.append(opt)
		
		return dic
	
	def info(self):
		title = self.PluginName+" configuration"
		msg = "Activate or deactivate Bonding interfaces.\n"
		msg += "--set [bondX:ethX,ethY ...] : take the list of Bonding interfaces to create.\n"
		msg += "                              eg: --set bond0:eth0,eth1 bond1:eth2,eth3 \n"
		msg += '                              NB: "none" keyword can be used to remove all bonds.\n'
		msg += " \n"
		msg += "--add  bondX:ethX,ethY  : Add a bond \n"
		msg += "--remove  bondX         : Remove a bond \n"
		self.output.help(title, msg)
	
	def get(self):
		try:
			''' MANDATORY !
			    define how to retreive the running config '''
			bond_list = []
			ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
			for afile in ifcfg_list:
				if "ifcfg-" in afile:
					bond_if = ''
					for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
						if 'BOND_IFACES=' in line:
							bond_if = re.sub('.*ifcfg-', '', afile)
							args = line.split('=')
							slaves = re.sub(' ', ',', re.sub('"', '', args[1])).strip()
							bond_list.append(bond_if+":"+slaves)
				
			bond_list.sort()
			if len(bond_list) == 0:
				self.output.title("No bonds")
				self.output.info("none")
			else:
				self.output.title("Setup:")
				self.output.info(' '.join(bond_list))
			
		except:
			err = str(sys.exc_info()[1])
			self.log.error(self.PluginName+" --get: "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def inputValidation(self, data):
		try:
			self.output.debug('Configuring bonds: '+str(data))
			# Check first for 'none' keyword
			# if present then return an empty list
			if data[0] == "none":
				return data
			
			## Check that data input is correct
			for info in data:
				err = False
				if not re.search('\:', info) and not re.search(',', info):
					err = True
					errmsg = "Data input is incorrect! Aborting."
				if not err:
					bond_info = info.split(':')
					slaves = bond_info[1].split(',')
					bond_name = bond_info[0]
					if not re.search('bond', bond_name):
						err = True
						errmsg = bond_name+" is not an authorized name! Aborting."
					else:
						str_pos = re.sub('bond', '', bond_name)
						try:
							int_pos = int(str_pos)
						except:
							err = True
							errmsg = bond_name+" is not an authorized name! Aborting."
				
				if err:
					#self.log.error(errmsg)
					self.output.error(errmsg)
					return None
		except:
			err = str(sys.exc_info()[1])
			self.log.error("setting "+self.PluginName+" "+str(data)+": "+err)
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
			
			self.netlib = ifconfig.Interface()
			onboot= 'yes'
			bond_data = {}
			if self.live_update:
				netDevs = self.netlib.list_ifs()
			for info in data:
				bond_info = info.split(':')
				slaves = bond_info[1].split(',')
				bond_data[bond_info[0]] = slaves
				if self.live_update:
					for dev in slaves:
						if dev not in netDevs:
							self.output.error("Device "+dev+" does not exist! Aborting.")
							return 1
			
			# Remove uneeded ifcfg-bondx files
			self.remove_uneeded_cfg(bond_data)
			self.output.debug("Removed uneeded ifcfg files")
			
			file = inspect.getfile(self.__class__)
			base = re.sub('/plugins.*', '', file)
			plg_path = os.path.join(base, "plugins/kvm/net/conf/bonds")
			## remove bonds plugins
			# Get the current config and remove plugins
			conf_list = self.get_current_config(self.PluginFqn)
			
			# For each entry in current config remove the MODE plugin
			for entry in conf_list:
				if entry == 'none':
					continue
				rm_bond = entry.split(':')[0]
				self.removePlugin("net.conf.bonds."+rm_bond+".mode")
			
			# Delete all plugin in plugins/net/conf/bonds has they will be recreated
			os.system('rm -rf '+plg_path)
			
			# proceed with bond creation
			for bond in bond_data.keys():
				slaves = bond_data[bond]
				# Create Bond associated plugin
				self.output.debug("Creating Bond "+bond+" plugin")
				dest_path = os.path.join(plg_path, bond)
				os.makedirs(dest_path)
				self.createPlugin("kvm/template_ovsbr.py", "net.conf.bonds."+bond+".mode")
				self.output.debug("Bond "+bond+" plugin created")
				# Create ifcfg
				MODE = ""
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+bond):
					final_lines = []
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+bond, 'r').readlines()
					for line in tmp_lines:
						if "ONBOOT=" in line:
							line = 'ONBOOT="'+onboot+'"\n'
						elif "BOND_IFACES=" in line:
							line = 'BOND_IFACES="'+' '.join(slaves)+'"\n'
						elif "USERCTL=" in line:
							line = ''
						elif "NM_CONTROLLED=" in line:
							line = ''
						elif "bond_mode=" in line:
							tmpstr1 = re.sub('.*bond_mode=', '', line)
							tmpargs = tmpstr1.split(' ')
							MODE = re.sub('".*', '', tmpargs[0])
						if line:
							final_lines.append(line)
					open('/etc/sysconfig/network-scripts/ifcfg-'+bond, 'w').writelines(final_lines)
				
				else:
					lines = []
					lines.append('DEVICE="'+bond+'"\n')
					# We set ONBOOT at no for the moment
					# set to on nnly when adding it to a bridge
					lines.append('ONBOOT=no\n')
					lines.append('BOOTPROTO=none\n')
					lines.append('DEVICETYPE=ovs\n')
					lines.append('TYPE=OVSBond\n')
					lines.append('OVS_BRIDGE=\n')
					lines.append('BOND_IFACES="'+' '.join(slaves)+'"\n')
					lines.append('OVS_OPTIONS="bond_mode=active-backup"\n')
					lines.append('HOTPLUG=no\n')
					open('/etc/sysconfig/network-scripts/ifcfg-'+bond, 'w').writelines(lines)
				
				if not MODE:
					self.executePluginLater('net.conf.bonds.'+bond+'.mode', 'set', 'active-backup')
				os.chmod('/etc/sysconfig/network-scripts/ifcfg-'+bond, 0440)
				self.output.debug("Bond "+bond+" ifcfg created")
				
				for if_slave in bond_data[bond]:
					# We can create ifcfg file
					lines = []
					lines.append('DEVICE="'+if_slave+'"\n')
					lines.append('ONBOOT="yes"\n')
					lines.append('HOTPLUG=no\n')
					open('/etc/sysconfig/network-scripts/ifcfg-'+if_slave, 'w').writelines(lines)
					
				self.output.info("added bond "+bond+" with slaves: "+str(bond_data[bond]))
			
		except:
			err = str(sys.exc_info()[1])
			#self.log.error("setting "+self.PluginName+" "+str(data)+": "+err)
			self.output.error(err)
			return 1
		return 0
	
	def add(self, data=''):
		''' Add a bond '''
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
					self.output.info("added bond "+infos[0])
		
		except:
			err = str(sys.exc_info()[1])
			self.log.error(self.PluginName+" --add "+data+": "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def remove(self, data=''):
		''' Delete a bond '''
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
					bond_name = aconf.split(':')[0]
					if entry == bond_name:
						nothing_todo = False
						conf_list.remove(aconf)
			
			if nothing_todo:
				self.output.warning('there is no bond to remove !')
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
					self.output.info("removed bond "+adev)
			
		except:
			err = str(sys.exc_info()[1])
			self.log.error(self.PluginName+" --del "+data+": "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def ListToString(self, list):
		return ','.join(list)
	
	def remove_uneeded_cfg(self, bond_data):
		ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
		bond_list = {}
		for afile in sorted(ifcfg_list):
			if "ifcfg-" in afile:
				is_bond_if = ''
				for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
					if 'BOND_IFACES=' in line:
						is_bond_if = re.sub('.*ifcfg-', '', afile)
						if not bond_list.has_key(is_bond_if):
							bond_list[is_bond_if] = []
				# if the device is a bond and is NOT part of the bonds to create then remove it
				if is_bond_if and not bond_data.has_key(is_bond_if):
					os.remove("/etc/sysconfig/network-scripts/"+afile)
	
