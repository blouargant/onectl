#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import regexp
from includes import bash
from includes import ipvalidation
from includes import ipaddr
import os
import sys
import re
import subprocess

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
		'''
		## The dictionnary created in this function will is used to create/modify options parsed in the command line.  
		##
		## create an entry for each additional option
		## opt = {}
		## opt["name"] = "option_name" ; eg --clear
		##
		## opt["help"] = "help message" ; the help message to display 
		##
		## opt["metavar"] = "A_VAR_NAME" ; Optional: the variable's name shown in the help message
		##
		## opt["action"] = store_action
		## where store_action can be one of the following:
		##  'store'                        ; just stores the argument's value.
		##  'store_const'                  ; stores the value specified by the const keyword argument.
		##  'store_true' and 'store_false' ; These are special cases of 'store_const' using for storing the values True and False respectively.
		##  'append'                       ; stores a list, and appends each argument value to the list.
		##  'append_const'                 ; stores a list, and appends the value specified by the const keyword argument to the list.
		##	''                             ; disable the key (for exemple use it to disable the --set options). 
		##
		## with 'store' and 'store_const' actions you can add an additional parameter:
		## opt['nargs'] = NUMBER_OF_ARGUMENTS ; where NUMBER_OF_ARGUMENTS can be:
		##  N (an integer)      ; N arguments from the command line will be gathered together into a list.
		##  '?'                 ; One argument will be consumed from the command line if possible, and produced as a single item.
		##  '*'                 ; All command-line arguments present are gathered into a list.
		##  '+'                 ; Just like '*', all command-line args present are gathered into a list. Additionally, an error message will be generated if there wasn't at least one command-line argument present.
		##  argparse.REMAINDER  ; All the remaining command-line arguments are gathered into a list. This is commonly useful for command line utilities that dispatch to other command line utilities
		##
		## NB: The argparse library is used to parse command line options.
		##     Checkout its documentation for more in depth understanding on how it works.
		'''
		dic = {}
		return dic
	
	
	
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" configuration"
		if self.PluginName == "ip":
			msg = "Set a management IP.\n"
			msg += "    --set IP/MASK\n"
			msg += "                  : Set the IP address of the management interface and its netmask.\n"
			msg += "                    eg: --set 192.168.1.1/24\n"
			msg += "                    Use --set dhcp to use dynamic IP assignement.\n"
			msg += "                    Use --set none to erase the configuration.\n"
			msg += "Other possible usage:\n"
			msg += "    --set IP NETMASK\n"
			msg += "                  : It is also possible to use the netmask directly\n"
			msg += "                    eg: --set 192.168.1.1 255.255.255.0\n"
			msg += " \n"
		
		if self.PluginName == "access":
			msg = "Set an access interface.\n"
			msg += "--set ETHX\n"
			msg += "                  : Set the external access device.\n"
			msg += "                    The device MUST exists and can be either a physical device or a bond.\n"
			msg += "                    eg: --set eth0 \n"
			msg += " \n"
		
		if self.PluginName == "vlan":
			msg = "Set a Vlan ID.\n"
			msg += "--set VLANID\n"
			msg += "                  : Set the external access VLAN ID.\n"
			msg += "                    eg: --set 210\n"
			msg += " \n"
		if self.PluginName == "mode":
			msg = "Set bonding mode.\n"
			msg += "--set [active-backup/balance-tcp/balance-slb]\n"
			msg += "                  : Set Bond mode.\n"
			msg += "                    The mode can either be active-backup, balance-tcp or balance-slb.\n"
			msg += "                    eg: --set active-backup\n"
			msg += "                    The default mode is active-backup.\n"
			msg += " \n"
		
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		''' TO OVERWRITE IN PLUGINS -- MANDATORY --
		In this function, plugin creator must implement a data input validator
		If input is valid then the function must return the data, or else it must return None.
		You can also use this to alter input data in order to support multiple input format.
		This function is automatically called, there is no need to call it within <set> function.
		'''
		data_res = None
		errmsg = ""
		err = False
		
		self.output.debug("Validating "+str(data))
		if self.PluginName == "ip":
			if isinstance(data, str) or len(data) == 1:
				if not isinstance(data, str):
					input = data[0]
				else:
					input = data
				
				if input == 'dhcp':
					self.output.debug(str(data)+" validated")
					return input
				elif input == '0.0.0.0/0' or input == 'none':
					self.output.debug(str(data)+" validated")
					return 'none'
				else:
					if re.search('/', input):
						tmp = input.split('/')
						ip = tmp[0]
						mask = tmp[1]
						if not ipvalidation.is_ipv4(ip):
							err = True
							errmsg = ip+" is not in a valid format! Aborting."
						
						try:
							if not int(mask) in range(0,33):
								err = True
								errmsg = "mask "+str(mask)+" is not in a valid format! Aborting."
							else:
								ipv4 = ipaddr.IPv4Network(ip+'/'+mask)
								data_res = ip+'/'+str(ipv4.netmask)
							
						except:
							if ipvalidation.is_ipv4(mask):
								ipv4 = ipaddr.IPv4Network(ip+'/'+mask)
								data_res = ip+'/'+str(ipv4.netmask)
							else:
								err = True
								errmsg = "mask "+str(mask)+" is not in a valid format! Aborting."
								
					else:
						errmsg = input+" is not in a valid format! Aborting."
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
			
		elif self.PluginName == "access":
			if not isinstance(data, str):
				input = data[0]
			else:
				input = data
				
			
			if input == 'none':
				data_res = input
			elif not re.match(regexp.IFNAME, input):
				err = "data input is incorrect! Aborting."
			elif not os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+input):
				err = input+" interface does not exist! Aborting."
			else:
				data_res = input
			
		elif self.PluginName == "vlan":
			if not isinstance(data, str):
				input = data[0]
			else:
				input = data
			
			if input == 'none':
				data_res = input
			elif not re.match(regexp.VLAN, input):
				err = "data input is incorrect! Aborting."
			else:
				data_res = input
		
		elif self.PluginName == "mode":
			if not isinstance(data, str):
				input = data[0]
			else:
				input = data
			
			if input in ['active-backup','balance-tcp','balance-slb']:
				data_res = input
			else:
				err = "data input is incorrect! Aborting."
			
		if err:
			#self.log.error(errmsg)
			self.output.error(errmsg)
		
		self.output.debug(str(data_res)+" validated")
		return data_res
	
	
	def get(self):
		try:
			''' MANDATORY ! 
			    define how to retreive the running config '''
			
			args = self.PluginFqn.split('.')
			if self.PluginName == "access":
				bridge = args[len(args)-2]
			else:
				bridge = args[len(args)-3]
			result = []
			
			if self.PluginName == "access":
				files = os.listdir("/etc/sysconfig/network-scripts/")
				for file in files:
					if "ifcfg-" in file and bridge+"_mgnt" not in file:
						res, err = bash.run('grep ^OVS_BRIDGE /etc/sysconfig/network-scripts/'+file)
						if res:
							args = res.split("=")
							if re.match('"*'+bridge+'"*', args[1].strip()):
								iface = re.sub('ifcfg-', '', file)
								if iface != bridge+"-mgnt" and iface not in result:
									result.append(iface)
				result.sort()
			
			if self.PluginName == "ip":
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+bridge+"-mgnt"):
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+bridge+"-mgnt", 'r').readlines()
					IP = ""
					NETMASK = ""
					for line in tmp_lines:
						if re.match('^BOOTPROTO *= *"*dhcp', line):
							result.append('dhcp')
						elif re.match('^IPADDR *=', line):
							infos = line.split('=')
							IP = re.sub('"', '', infos[1]).strip()
						elif re.match('^NETMASK *=', line):
							infos = line.split('=')
							NETMASK = re.sub('"', '', infos[1]).strip()
					if IP and NETMASK:
						result.append(IP+'/'+NETMASK)
					
					if len(result) == 0:
						result.append('none')
				else:
					result.append('none')
			
			if self.PluginName == "vlan":
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+bridge+"-mgnt"):
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+bridge+"-mgnt", 'r').readlines()
					for line in tmp_lines:
						if re.match('^OVS_OPTIONS *=', line):
							infos = line.split('=')
							OPTS= re.sub('"', '', infos[1]).split(' ')
							for opt in OPTS:
								if re.match("tag=", opt):
									result.append(opt.split('=')[1])
					
					if len(result) == 0:
						result.append('none')
				else:
					result.append('none')
			
			if self.PluginName == "mode":
				args = self.PluginFqn.split('.')
				bond = args[len(args)-2]
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+bond):
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+bond, 'r').readlines()
					for line in tmp_lines:
						if re.match('^OVS_OPTIONS *=', line):
							tmpstr1 = re.sub('.*bond_mode=', '', line)
							tmpargs = tmpstr1.split(' ')
							result.append(re.sub('".*', '', tmpargs[0]))
					
					if len(result) == 0:
						result.append('none')
				else:
					self.output.error("Cannot find "+bond+" configuration file !")
					result.append('none')
			
			self.output.info(' '.join(result))
		
		except:
			err = str(sys.exc_info()[1])
			#self.log.error("getting "+self.PluginName+" : "+err)
			self.output.error(err)
			return 1
		
		return 0
	
	def set(self, data):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			'''Implement set functionality '''
			args = self.PluginFqn.split('.')
			if self.PluginName == "access":
				bridge = args[len(args)-2]
			else:
				bridge = args[len(args)-3]
			if self.PluginName == "vlan" or self.PluginName == "ip":
				IP = ""
				NETMASK = ""
				VLAN = ""
				DHCP_IFACES = ""
				if self.PluginName == "ip":
					if data == "none":
						if self.live_update:
							bash.run('ifdown '+bridge+'-mgnt')
						if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+bridge+"-mgnt"):
							os.remove("/etc/sysconfig/network-scripts/ifcfg-"+bridge+"-mgnt")
							self.output.debug("removed /etc/sysconfig/network-scripts/ifcfg-"+bridge+"-mgnt")
						self.executePluginLater("net.conf.bridges."+bridge+".mgnt.vlan", "set", 'none')
						return 0
					
					if data != "dhcp":
						args = data.split('/')
						IP = args[0]
						NETMASK = args[1]
					else:
						msg = self.executePlugin("net.conf.bridges."+bridge+".access", "get")
						if msg and "Error" not in msg:
							if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+msg):
								tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+msg, 'r').readlines()
								for line in tmp_lines:
									if re.match('^BOND_IFACE *=', line):
										args = line.split('=')
										DHCP_IFACES = args[1].srtip('"').strip()
								
							if not DHCP_IFACES:
								DHCP_IFACES = msg
				
				if self.PluginName == "vlan":
					VLAN = data
				
				self.output.debug("setting "+self.PluginName+" for "+bridge+" to "+data)
				
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+bridge+"-mgnt"):
					final_lines = []
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+bridge+"-mgnt", 'r').readlines()
					has_ip = False
					has_netmask = False
					has_opts = False
					has_extra = False
					has_bridge = False
					for line in tmp_lines:
						if re.match('^DEVICE *=', line):
							line = 'DEVICE="'+bridge+'-mgnt"\n'
						elif re.match('^ONBOOT *=', line):
							line = 'ONBOOT=yes\n'
						elif re.match('^OVS_BRIDGE *=', line):
							line = 'OVS_BRIDGE='+bridge+'\n'
							has_bridge = True
						elif re.match('^TYPE *=', line):
							line = 'TYPE=OVSIntPort\n'
						elif re.match('^IPADDR', line):
							has_ip = True
							if self.PluginName == "ip":
								if data == "dhcp":
									line = ''
								else:
									line = 'IPADDR='+IP+'\n'
							
						elif re.match('^NETMASK', line):
							has_netmask = True
							if self.PluginName == "ip":
								if data == "dhcp":
									line = ''
								else:
									line = 'NETMASK='+NETMASK+'\n'
							
						elif re.match('^BOOTPROTO', line):
							if self.PluginName == "ip":
								if data == "dhcp":
									line = 'BOOTPROTO=dhcp\n'
									
								else:
									line = 'BOOTPROTO=static\n'
						
						elif re.match('^OVS_OPTIONS', line):
							has_opts = True
							if self.PluginName == "vlan":
								if data == "none":
									line = ""
								else:
									line = 'OVS_OPTIONS="tag='+VLAN+'"\n'
						elif re.match('^OVS_EXTRA', line):
							has_extra = True
							if self.PluginName == "vlan":
								if data == "none":
									line = ""
								else:
									line = 'OVS_EXTRA="set Interface $DEVICE external-ids:iface-id=$(hostname -s)-$DEVICE-vif"\n'
						
						if line :
							final_lines.append(line)
					
					# Looks for missing parameters
					if not has_bridge:
						final_lines.append('OVS_BRIDGE='+bridge+'\n')
					if self.PluginName == "ip" and data != "dhcp":
						if not has_ip:
							final_lines.append('IPADDR='+IP+'\n')
						if not has_netmask:
							final_lines.append('NETMASK='+NETMASK+'\n')
					if self.PluginName == "vlan" and data != "none":
						if not has_opts:
							final_lines.append('OVS_OPTIONS="tag='+VLAN+'"\n')
						if not has_extra:
							final_lines.append('OVS_EXTRA="set Interface $DEVICE external-ids:iface-id=$(hostname -s)-$DEVICE-vif"\n')
						
					open('/etc/sysconfig/network-scripts/ifcfg-'+bridge+'-mgnt', 'w').writelines(final_lines)
					
				elif self.PluginName == "vlan":
					if data != "none":
						self.output.error("You must set an IP on the interface before assigning a vlan")
						return 1
					else:
						self.output.debug("File does not exists, nothing to do")
						return 0
				else:
					lines = []
					lines.append('DEVICE='+bridge+'-mgnt\n')
					lines.append('ONBOOT=yes\n')
					if self.PluginName == "ip":
						if data == "dhcp":
							lines.append('BOOTPROTO=dhcp\n')
						else:
							lines.append('BOOTPROTO=static\n')
							lines.append('IPADDR='+IP+'\n')
							lines.append('NETMASK='+NETMASK+'\n')
					
					lines.append('DEVICETYPE=ovs\n')
					lines.append('TYPE=OVSIntPort\n')
					lines.append('OVS_BRIDGE='+bridge+'\n')
					lines.append('HOTPLUG=no\n')
					open('/etc/sysconfig/network-scripts/ifcfg-'+bridge+'-mgnt', 'w').writelines(lines)
				
				if self.live_update:
					bash.run('ifdown '+bridge+'-mgnt')
					bash.run('ifup '+bridge+'-mgnt')
			
			elif self.PluginName == "access":
				self.output.debug("setting "+self.PluginName+" for "+bridge+" to "+data)
				if data == "none":
					files = os.listdir("/etc/sysconfig/network-scripts/")
					for file in files:
						if "ifcfg-" in file:
							res, err = bash.run('grep ^OVS_BRIDGE /etc/sysconfig/network-scripts/'+file)
							if res:
								args = res.split("=")
								if re.match('"*'+bridge+'"*', args[1].strip()):
									res, err = bash.run('grep ^TYPE /etc/sysconfig/network-scripts/'+file)
									if res:
										iface = re.sub('ifcfg-', '',file)
										if "OVSPort" in res:
											self.output.debug("remove "+bridge+" reference in "+file)
											lines = []
											lines.append('DEVICE="'+iface+'"\n')
											lines.append('ONBOOT=yes\n')
											lines.append('BOOTPROTO=none\n')
											lines.append('HOTPLUG=no\n')
											open('/etc/sysconfig/network-scripts/ifcfg-'+iface, 'w').writelines(lines)
											os.chmod('/etc/sysconfig/network-scripts/ifcfg-'+iface, 0440)
											
										elif "OVSBond" in res:
											self.output.debug("remove bond "+iface)
											bash.run('rm -f /etc/sysconfig/network-scripts/'+file)
				
				else:
					# Check if bond
					bond_ifaces = ""
					not_set = True
					if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+data):
						res, err = bash.run('grep "^TYPE *=.*OVS" /etc/sysconfig/network-scripts/ifcfg-'+data)
						if res:
							not_set = False
							tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+data, 'r').readlines()
							final_lines = []
							for line in tmp_lines:
								if re.match('^OVS_BRIDGE', line):
									line = 'OVS_BRIDGE='+bridge+'\n'
								final_lines.append(line)
							open('/etc/sysconfig/network-scripts/ifcfg-'+data, 'w').writelines(final_lines)
					
					if not_set:
						lines = []
						lines.append('DEVICE='+data+'\n')
						lines.append('ONBOOT=yes\n')
						lines.append('DEVICETYPE=ovs\n')
						lines.append('TYPE=OVSPort\n')
						lines.append('OVS_BRIDGE='+bridge+'\n')
						lines.append('BOOTPROTO=none\n')
						lines.append('HOTPLUG=no\n')
						open('/etc/sysconfig/network-scripts/ifcfg-'+data, 'w').writelines(lines)
					
			elif self.PluginName == "mode":
				bond = args[len(args)-2]
				if os.path.exists('/etc/sysconfig/network-scripts/ifcfg-'+bond):
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+bond, 'r').readlines()
					final_lines = []
					for line in tmp_lines:
						if re.match('^OVS_OPTIONS', line):
							line='OVS_OPTIONS="bond_mode='+data+'"\n'
						final_lines.append(line)
					open('/etc/sysconfig/network-scripts/ifcfg-'+bond, 'w').writelines(final_lines)
				else:
					self.output.error("Cannot find "+bond+" configuration file!")
				
		except:
			err = str(sys.exc_info()[1])
			##self.log.error("setting "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
		
		return 0
	
