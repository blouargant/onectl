#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import ifconfig
from includes import ipaddr
from includes import ipvalidation
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
		
	def get_active(self):
		'''  returns active config in a list  '''
		try:
			self.netlib = ifconfig.Interface()
			devlist = self.netlib.list_bonds()
			RunningBonds = []
			for adev in sorted(devlist):
				if self.netlib.is_up(adev):
					bond_slaves = self.ListToString(self.netlib.get_bond_slaves(adev))
					bond_info = adev+':'+bond_slaves
					RunningBonds.append(bond_info)
		except:
			raise
		return RunningBonds
		
	def get(self):
		try:
			''' MANDATORY !
			    define how to retreive the running config '''
			RunningBonds = self.get_active()
			
			onbootBonds = {}
			ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
			for afile in ifcfg_list:
				if "ifcfg-" in afile:
					is_bond_if = ''
					is_slave_if = False
					master_if = ''
					for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
						if 'BONDING_OPTS=' in line:
							is_bond_if = re.sub('.*ifcfg-', '', afile)
						elif re.search('^SLAVE=',line) and re.search('yes',line):
							is_slave_if = True
						elif 'MASTER=' in line:
							tmpstr = re.sub('MASTER=', '', line)
							master_if = re.sub('"', '', tmpstr).strip()

					if is_slave_if and master_if:
						ifname = re.sub('ifcfg-', '', afile)
						if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+master_if):
							if not onbootBonds.has_key(master_if):
								onbootBonds[master_if] = []
							onbootBonds[master_if].append(ifname)

					if is_bond_if:
						if not onbootBonds.has_key(is_bond_if):
							onbootBonds[is_bond_if] = []


			if not RunningBonds:
				self.output.title("No running bonds")
				self.output.info("none")
			else:
				self.output.title("Running bonds:")
				self.output.info(','.join(RunningBonds))

			bond_list = ''
			for abond in onbootBonds.keys():
				if not bond_list:
					bond_list = abond+":"+self.ListToString(onbootBonds[abond])
				else:
					bond_list += " "+abond+":"+self.ListToString(onbootBonds[abond])

			if not bond_list:
				self.output.title("No onboot bonds")
				self.output.info("none")
			else:
				self.output.title("Onboot setup:")
				self.output.info(bond_list)


		except:
			err = str(sys.exc_info()[1])
			self.log.error(self.PluginName+" --get: "+err)
			self.output.error(err)
			return 1

		return 0

	def inputValidation(self, data):
		try:
			if not data[0]:
				data[0] = "none"
			self.output.debug('Configuring bonds: '+str(data))
			# Check first for 'none' keyword
			# if present then return an empty list
			if data[0] == "none":
				return data

			self.netlib = ifconfig.Interface()
			netDevs = self.netlib.list_ifs()
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
			for info in data:
				bond_info = info.split(':')
				slaves = bond_info[1].split(',')
				bond_data[bond_info[0]] = slaves
				netDevs = self.netlib.list_ifs()
				for dev in slaves:
					if dev not in netDevs:
						self.output.error("Device "+dev+" does not exist! Aborting.")
						return 1
			if self.live_update:
				# remove running bonds that are NOT part of the bonds to create
				self.remove_uneeded_running(bond_data)
				self.output.debug("Removed uneeded running bonds")
			# Remove uneeded ifcfg-bondx files
			self.remove_uneeded_cfg(bond_data)
			self.output.debug("Removed uneeded ifcfg files")

			file = inspect.getfile(self.__class__)
			base = re.sub('/plugins.*', '', file)
			plg_path = os.path.join(base, "plugins/net/conf/bonds")
			## remove bonds plugins
			# Get the current config and remove plugins
			conf_list = self.get_current_config(self.PluginFqn)

			# For each entry in current config remove the IP plugin
			for entry in conf_list:
				if entry == 'none':
					continue
				rm_bond = entry.split(':')[0]
				self.removePlugin("net.conf.bonds."+rm_bond+".ip")


			boot_aliases = self.netlib.get_boot_aliases()
			active_aliases = self.netlib.get_active_aliases()
			aliases= list(set(boot_aliases)|set(active_aliases))
			aliases_remove=[]
			if aliases:
				for alias in aliases:
					if not re.search('bond', alias):
						continue
				
					main_device = re.sub('\:.*', '', alias)
					if main_device not in bond_data.keys():
						aliases_remove.append(alias)
				if aliases_remove:
					msg = self.executePlugin("net.aliases", "remove", aliases_remove)
					if re.search('Error :', msg):
						self.output.error("Remove of net.aliases %s failed" %('\n'.join(aliases_remove)))
					else:
						self.output.debug(str(alias)+": has been removed")


			# Delete all plugin in plugins/net/conf/bonds has they will be rectreated
			os.system('rm -rf '+plg_path)

			# proceed with bond creation
			for bond in bond_data.keys():
				# Create Bond associated plugin
				self.output.debug("Creating Bond "+bond+" plugin")
				dest_path = os.path.join(plg_path, bond)
				os.makedirs(dest_path)
				self.createPlugin("network/plugin_ip.py", "net.conf.bonds."+bond+".ip")
				self.createPlugin("network/iface_gateway.py", "net.conf.bonds."+bond+".gateway")
				self.output.debug("Bond "+bond+" plugin created")
				# Create ifcfg
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+bond):
					final_lines = []
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+bond, 'r').readlines()
					for line in tmp_lines:
						if "ONBOOT=" in line:
							line = 'ONBOOT="'+onboot+'"\n'
						if "USERCTL=" in line:
							line = ''
						if "NM_CONTROLLED=" in line:
							line = ''
						if line:
							final_lines.append(line)
					final_lines.append('USERCTL=no\n')
					final_lines.append('NM_CONTROLLED=no\n')

					open('/etc/sysconfig/network-scripts/ifcfg-'+bond, 'w').writelines(final_lines)
				else:
					lines = []
					lines.append('DEVICE="'+bond+'"\n')
					lines.append('ONBOOT="'+onboot+'"\n')
					lines.append('BONDING_OPTS="mode=1 miimon=100"\n')
					lines.append('USERCTL=no\n')
					lines.append('NM_CONTROLLED=no\n')
					open('/etc/sysconfig/network-scripts/ifcfg-'+bond, 'w').writelines(lines)

				os.chmod('/etc/sysconfig/network-scripts/ifcfg-'+bond, 0440)
				self.output.debug("Bond "+bond+" ifcfg created")

				# Add entries in /etc/modprobe.d/bonding.conf
				bond_entry = False
				if os.path.exists('/etc/modprobe.d/bonding.conf'):
					modprobe_bondings = open("/etc/modprobe.d/bonding.conf").readlines()
					for line in modprobe_bondings:
						if re.search('alias '+bond+' bonding', line):
							bond_entry = True
				else:
					os.system('mkdir -p /etc/modprobe.d/')
					os.system('touch /etc/modprobe.d/bonding.conf')

				if not bond_entry:
					mpf = open('/etc/modprobe.d/bonding.conf', 'a+')
					mpf.write('alias %s bonding\n' % bond)
					mpf.close()
					os.chmod('/etc/modprobe.d/bonding.conf', 0440)

				if self.live_update:
					self.output.debug("Creating live bonds")
					# if it does not exist then create bond interface
					existing_bonds = self.netlib.list_bonds()
					if not bond in existing_bonds:
						self.output.debug("create bond "+bond)
						error = self.netlib.create_bond(bond)
						self.output.debug("create bond result:"+error)
						if error:
							self.output.error("Cannot create bond "+bond+" :"+error)
							return 1

					else:
						existing_slaves = self.netlib.get_bond_slaves(bond)
						self.output.debug("existing slaves: "+str(existing_slaves))
						# release interfaces that are not part of the bond to create
						for a_slave in existing_slaves:
							if a_slave not in bond_data[bond] and a_slave:
								self.output.debug("releasing "+a_slave+" from "+bond)
								self.netlib.release_slave_iface(bond, a_slave)

					if not self.netlib.is_up(bond):
							self.output.debug("set "+bond+" up")
							self.netlib.up(bond)

				# For each interface to enslave check what we have to do
				bond_ip_active = ''
				bond_ip_boot = ''
				slave_ip_active = ''
				slave_ip_boot = ''
				vlans_to_move = {}
				
				for if_slave in bond_data[bond]:
					if self.live_update:
						# Is it already a slave ?
						self.output.debug(if_slave+" checking if device is part of a bond")
						if self.netlib.is_bond_slave(if_slave):
							bond_slaves = self.netlib.get_bond_slaves(bond)
							if not if_slave in bond_slaves:
								if self.live_update:
									# if not part of the right bond then release it and enslave it to the correct bond
									self.output.debug(if_slave+" is not part of the right bond")
									other_bond = self.netlib.get_bond_master(if_slave)
									self.netlib.release_slave_iface(other_bond, if_slave)
									self.netlib.enslave_iface(bond, if_slave)
									self.output.debug("Free "+if_slave+" from "+other_bond+" and enslave it to "+bond)
						else:
							self.output.debug(if_slave+" is not part of a bond")
					
					# Get the slave IP
					slave_ip_active,slave_ip_boot = self.get_dev_ip(if_slave, False, False)
					
					self.output.debug(str(if_slave)+": active IP = "+str(slave_ip_active))
					self.output.debug(str(if_slave)+": boot IP = "+str(slave_ip_boot))
					if not bond_ip_active or not bond_ip_boot:
						bond_ip_active = slave_ip_active
						bond_ip_boot = slave_ip_boot

					# Return back the IP of the active slave taken from the bond
					# If the slave has an IP remove it
					if slave_ip_active != "0.0.0.0/0" or slave_ip_boot != "0.0.0.0/0":
						# remove the IP
						self.output.debug("Removing "+if_slave+" IP")
						self.set_dev_ip(if_slave, False, False, "0.0.0.0/0", "0.0.0.0/0", False)

					# Check if if_slave has vlans
					self.output.debug(if_slave+": try to get attached vlans")

					boot_vlans = self.netlib.list_boot_vlans()
					active_vlans = self.netlib.list_vlans()
					vlans= list(set(boot_vlans)|set(active_vlans))
	
					for avlan in vlans:
						main_device = re.sub('\..*', '', avlan)
						vid = re.sub('.*\.', '', avlan)
						self.output.debug(if_slave+" ("+main_device+"): found vlan "+str(avlan))
						# Check if if_slave have an attached vlan
						if main_device == if_slave or main_device == bond:
							vlan_ip= '0.0.0.0/0'
							self.output.debug(if_slave+": "+str(avlan)+" is attached to the device")
							# get vlan IP configuration
							vlan_ip_active,vlan_ip_boot = self.get_dev_ip(avlan,False, True)
							self.output.debug(str(avlan)+": IP = "+str(vlan_ip_active))
							# If it was already added skip
							if vlans_to_move.has_key(avlan):
								continue
							vlans_to_move[avlan] = {}
							vlans_to_move[avlan]['ip_active'] = vlan_ip_active
							vlans_to_move[avlan]['ip_boot'] = vlan_ip_boot
							vlans_to_move[avlan]['vid'] = vid
							vlans_to_move[avlan]['device'] = main_device

					# We can finaly create ifcfg file
					lines = []
					lines.append('DEVICE="'+if_slave+'"\n')
					lines.append('ONBOOT="yes"\n')
					lines.append('BOOTPROTO=none\n')
					lines.append('MASTER="'+bond+'"\n')
					lines.append('SLAVE="yes"\n')
					lines.append('USERCTL=no\n')
					lines.append('NM_CONTROLLED=no\n')
					open('/etc/sysconfig/network-scripts/ifcfg-'+if_slave, 'w').writelines(lines)


				# Remove uneeded vlans
				vlan_list = sorted(vlans_to_move.keys())
				if len(vlan_list) > 0:
					msg = self.executePlugin("net.vlans", "remove", vlan_list)
					if re.search('Error :', msg):
						self.output.error("Remove of net.vlans %s failed" %s('\n'.join(vlan_list)))
						return 1
					self.output.debug(str(vlan_list)+": has been removed")

				if self.live_update:
					# Once all vlans are removed, then we can enslave if_slave
					bond_slaves = self.netlib.get_bond_slaves(bond)
					for if_slave in bond_data[bond]:
						if not if_slave in bond_slaves:
							err = self.netlib.enslave_iface(bond, if_slave)
							self.output.debug("Enslaving "+if_slave+" to "+bond+" : "+err)

				# Set the bond IP
				if bond_ip_active or bond_ip_boot:
					self.output.debug("Assigning ip "+bond_ip_active+" to "+bond)
					self.set_dev_ip(bond, True, False, bond_ip_active, bond_ip_boot,True)

				# Finaly recreate VLANs on bond
				new_vlan_list = []
				for avlan in vlan_list:
					vid = vlans_to_move[avlan]['vid']
					new_vlan = bond+'.'+vid
					if new_vlan not in new_vlan_list:
						new_vlan_list.append(new_vlan)

				if len(new_vlan_list) > 0:
					msg = self.executePluginLater("net.vlans", "add", new_vlan_list)
					if re.search('Error :', msg):
						self.output.error("Vlans %s were not added" %s(str(new_vlan_list)))
					else:
						self.output.debug(str(new_vlan_list)+": have been added")

				for avlan in vlan_list:
					vid = vlans_to_move[avlan]['vid']
					vlan_ip_active = vlans_to_move[avlan]['ip_active']
					vlan_ip_boot = vlans_to_move[avlan]['ip_boot']
					new_vlan = bond+'.'+vid
					self.set_dev_ip(new_vlan,False,True, vlan_ip_active, vlan_ip_boot,True)
					self.output.debug(str(new_vlan)+": set active IP %s boot ip %s " %(vlan_ip_active,vlan_ip_boot))

				self.output.info("added bond "+bond+" with slaves: "+str(bond_data[bond]))
		
		except:
			err = str(sys.exc_info()[1])
			#self.log.error("setting "+self.PluginName+" "+str(data)+": "+err)
			self.output.error(err)
			return 1
		return 0
	
	def check(self):
		''' The fucntion is overwriten because we only check agains Onboot setup
			we also replace ", " in the get function '''
		self.output.disable()
		self.get()
		tmpinfos = self.messages["info"]
		if tmpinfos:
			info = re.sub(', ', ' ', tmpinfos[1])
		else:
			info = ''
		self.output.clear_messages()
		self.output.enable()
		self._check(info_get=info)
		return 0

		self.show()
		info_show = self.listToString(self.messages["info"])
		
		self.output.enable()
		if not info_show:
			self.output.warning("Key has not been set!")
			self.output.info(self.PluginName+" active setup: "+info_get)
			return 0
		
		bonds_get = info_get.split(' ')
		bonds_show = info_show.split(' ')
		final_bonds = bonds_show
		
		for bond in bonds_get:
			bond_info = bond.split(':')
			bond_master = bond_info[0]
			bond_slaves = bond_info[1].split(',')
			found = False
			for sbond in bonds_show:
				if re.search('^'+bond_master+':', sbond):
					found = True
					sbond_info = bond.split(':')
					sbond_slaves = bond_info[1].split(',')
					for slave in bond_slaves:
						if slave in sbond_slaves:
							sbond_slaves.remove(slave)
						else:
							self.output.warning("Key configuration does not match active setup!")
							self.output.info(self.PluginFqn+" set to "+info_show+" while active setup is "+info_get)
							return 1
					if len(sbond_slaves) > 0:
						self.output.warning("Key configuration does not match active setup!")
						self.output.info(self.PluginFqn+" set to "+info_show+" while active setup is "+info_get)
						return 1
					
					final_bonds.remove(sbond)
			if not found:
				self.output.warning("Key configuration does not match active setup!")
				self.output.info(self.PluginFqn+" set to "+info_show+" while active setup is "+info_get)
				return 1
		
		if len(final_bonds) > 0:
			self.output.warning("Key configuration does not match active setup!")
			self.output.info(self.PluginFqn+" set to "+info_show+" while active setup is "+info_get)
			return 1
		else:
			self.output.title("Key's configuration is active.")
			self.output.info(self.PluginFqn+" = "+info_show)
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
			# get current configuration saved in onectl
			conf_list = self.get_current_config(self.PluginFqn)

			todel = []
			if type(data) is list:
				todel = data
			else:
				todel.append(data)


			for entry in todel:
				if re.search(':', entry):
					entry = entry.split(':')[0]
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
		str = ""
		for astr in sorted(list):
			if str:
				str += ","+astr
			else:
				str = astr
		return str

	def remove_uneeded_running(self, bond_data):
		self.output.debug("remove uneeded running bonds")
		existing_bonds = self.netlib.list_bonds()
		existing_vlans = self.netlib.list_vlans()
		bonded_vlans = {}
		for avlan in existing_vlans:
			vlan_device = avlan.split('.')[0]
			if self.netlib.is_bond_master(vlan_device):
				self.output.debug(str(vlan_device)+" has vlans")
				if not bonded_vlans.has_key(vlan_device):
					bonded_vlans[vlan_device] = []
				bonded_vlans[vlan_device].append(avlan)

		vlans_to_move = {}
		for ebond in existing_bonds:
			self.output.debug("Checking bond "+str(ebond))
			#if not bond_data.has_key(ebond):
			existing_slaves = self.netlib.get_bond_slaves(ebond)
			# get active slave to give it the Bond's IP later
			active_slave = self.netlib.get_active_slave(ebond)

			# first release the interfaces:
			for a_slave in existing_slaves:
				if a_slave:
					self.output.debug("release slave "+a_slave+" from "+ebond)
					self.netlib.release_slave_iface(ebond, a_slave)
					self.output.debug("set "+a_slave+" up")
					self.netlib.up(a_slave)
			
			# Get the active slave
			target_eth = ''
			if active_slave:
				target_eth = active_slave
			else:
				target_eth = existing_slaves[0]

			# move potential vlans to the active/first interface
			if bonded_vlans.has_key(ebond):
				self.output.debug(str(ebond)+" has vlans")
				for avlan in bonded_vlans[ebond]:
					infos = avlan.split('.')
					main_device = infos[0]
					vid = infos[1]
					vlan_ip_active,vlan_ip_boot = self.get_dev_ip(avlan,False, True)

					vlans_to_move[avlan] = {}
					vlans_to_move[avlan]['ip_active'] = vlan_ip_active
					vlans_to_move[avlan]['ip_boot'] = vlan_ip_boot
					vlans_to_move[avlan]['vid'] = vid
					vlans_to_move[avlan]['device'] = main_device
					vlans_to_move[avlan]['dest'] = target_eth
			
			# then set bond down
			self.output.debug("set "+ebond+" down")
			# Disable the bond
			self.netlib.down(ebond)
			
			# Copy ip address from bond to active slave
			if target_eth:
				# get bond ip to give it to the active interface
				bond_ip_active, bond_ip_boot = self.get_dev_ip(ebond,True,False)
				# Set IP back to the interface
				self.set_dev_ip(target_eth,False,False, bond_ip_active, bond_ip_boot,False)
		
		
		# Remove all vlans previously attached to bond
		vlans_to_remove = vlans_to_move.keys()
		if len(vlans_to_remove) > 0:
			msg = self.executePlugin("net.vlans", "remove", vlans_to_remove )
			if re.search('Error :', msg):
				self.output.error("Error removing vlans" %s(str(vlans_to_remove)))
			else:
				self.output.debug(str(vlans_to_remove)+": have been removed")


			vlans_to_add = []
			for avlan in vlans_to_remove:
				new_vlan = vlans_to_move[avlan]['dest']+"."+vlans_to_move[avlan]['vid']
				vlans_to_add.append(new_vlan)

			# If executed lated the eth will be inslaved and will fail
			msg  = self.executePlugin("net.vlans", "add", vlans_to_add)
			if re.search('Error :', msg):
				self.output.error("Error adding vlans" %s(str(vlans_to_add)))
			else:
				self.output.debug(str(vlans_to_add)+": have been added")


			for avlan in vlans_to_remove:
				new_vlan = vlans_to_move[avlan]['dest']+"."+vlans_to_move[avlan]['vid']
				vlan_ip_active = vlans_to_move[avlan]['ip_active']
				vlan_ip_boot = vlans_to_move[avlan]['ip_boot']
				self.set_dev_ip(new_vlan,False, True, vlan_ip_active, vlan_ip_boot,False)



	def remove_uneeded_cfg(self, bond_data):
		ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
		bond_list = {}
		bond_ip_list={}
		vlan_list = []
		for afile in sorted(ifcfg_list):
			if "ifcfg-" in afile:
				is_bond_if = ''
				bond_master = ''
				is_slave_if = False
				rewrite_lines = []
				is_vlan = False
				for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
					if 'BONDING_OPTS=' in line:
						is_bond_if = re.sub('.*ifcfg-', '', afile)
						if not bond_list.has_key(is_bond_if):
							bond_list[is_bond_if] = []
					elif 'SLAVE=' in line:
						is_slave_if = True
						line = ''
					elif 'MASTER=' in line:
						bond_master = re.sub('MASTER=', '', line).replace('"', '').strip()
						if not bond_list.has_key(bond_master):
							bond_list[bond_master] = []
						bond_list[bond_master].append(re.sub('ifcfg-', '', afile))
						line = ''
					elif re.search('^VLAN="*yes', line):
						vlan_list.append(afile)
					if len(line) > 0:
						rewrite_lines.append(line)
				# if the device was a slave then rewrite ifcfg file without bonding options
				if is_slave_if:
					open('/etc/sysconfig/network-scripts/'+afile, 'w').writelines(rewrite_lines)
				# if the device is a bond and is NOT part of the bonds to create then remove it
				if len(is_bond_if) > 0:
					# Get the IP of the bond before it is deleted
					bond_ip_active,bond_ip_boot  = self.get_dev_ip(is_bond_if, True,False)
					if not bond_ip_list.has_key(is_bond_if):
						bond_ip_list[is_bond_if]= []
					bond_ip_list[is_bond_if].append(bond_ip_boot)
	
					if not bond_data.has_key(is_bond_if):
						os.remove("/etc/sysconfig/network-scripts/"+afile)


		# check VLANs that may still be attached to a deleted bond
		# If it's the case then attach it to the active/first interface
		vlans_to_add = {}
		vlans_to_remove = []
		for afile in sorted(vlan_list):
			ifname = re.sub('ifcfg-', '', afile)
			vlan_infos = ifname.split('.')
			vlan_bond = vlan_infos[0]
			vlan_id = vlan_infos[1]
			if bond_list.has_key(vlan_bond):
				# this VLAN is based on a bond that will be removed
				target_eth = ''
				if self.netlib.is_up(vlan_bond):
					active_slave = self.netlib.get_active_slave(vlan_bond)
					if active_slave:
						target_eth = active_slave
				if not target_eth:
					# if no active slave then take the first interface
					target_eth = bond_list[vlan_bond][0]
				if target_eth:
					new_vlan = target_eth+'.'+vlan_id
					#vlans_to_add.append(new_vlan)
					vlans_to_remove.append(ifname)
					vlan_ip_active,vlan_ip_boot  = self.get_dev_ip(ifname, False,True)
					if not vlans_to_add.has_key(new_vlan):
						vlans_to_add[new_vlan]= []
						vlans_to_add[new_vlan].append(vlan_ip_boot)
					rewrite_lines = []
					for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
						rewrite_lines.append(re.sub(vlan_bond, target_eth, line))
					open('/etc/sysconfig/network-scripts/'+afile, 'w').writelines(rewrite_lines)

		if not self.live_update:
			if vlans_to_remove:
				msg = self.executePlugin("net.vlans", "remove", vlans_to_remove)
				if re.search('Error :', msg):
					self.output.error("Error removing vlans" %s(str(vlans_to_remove)))
				else:
					self.output.debug(str(vlans_to_remove)+": have been removed")


		
			if vlans_to_add:
				# If executed lated the eth will be inslaved and will fail
				add_vlans=vlans_to_add.keys()
				msg = self.executePlugin("net.vlans", "add", add_vlans)
				if re.search('Error :', msg):
					self.output.error("Error adding vlans" %s(str(add_vlans)))
				else:
					self.output.debug(str(add_vlans)+": have been added")


				for avlan in vlans_to_add:
					boot_ip = vlans_to_add[avlan][0]
					self.set_dev_ip(avlan,False, True, None, boot_ip,False)
		
		for ebond in bond_list:
			target_eth = ''
			if self.netlib.is_up(ebond):
				active_slave = self.netlib.get_active_slave(ebond)
				if active_slave:
					target_eth = active_slave
			if not target_eth:
				if bond_list[ebond]:
					target_eth = bond_list[ebond][0]
			
			# Copy ip address from bond to active slave
			if target_eth:
				# get the IP of the bond
				if bond_ip_list[ebond]:
					ipv4 = bond_ip_list[ebond][0]
				else:
					ipv4 = "0.0.0.0/0"
				boot_ip = ipv4
				
				# Set IP back to the slave  interface
				self.set_dev_ip(target_eth,False,False, None , boot_ip,False)

	def get_dev_ip(self,ebond,isBond=True,isVlan=False):
		''' Return active ip of a device and the boot ip  '''
		running_ip = "0.0.0.0/0"
		boot_ip = "0.0.0.0/0"
		if isBond:
			plugin="net.conf.bonds."+ebond+".ip"
		elif isVlan:
			plugin="net.conf.vlans."+ebond+".ip"
		else:
			plugin="net.conf."+ebond+".ip"
			
		if self.live_update:
			msg = self.executePlugin(plugin, "get")
			if re.search('Error', msg):
				bond_ip = str(self.netlib.get_ip(ebond))
				bond_mask = str(self.netlib.get_netmask(ebond))
				running_ip = bond_ip+'/'+bond_mask
			elif msg:
				running_ip =  msg
	
		msg = self.executePlugin(plugin, "get_boot")
		if re.search('Error', msg):
			boot_ip = None
		else:
			boot_ip = msg

		return running_ip, boot_ip

	def set_dev_ip(self,ebond,isBond,isVlan, running_ip, boot_ip, bExecuteLater=False):
		''' Get the active ip of a device or the boot ip  '''
		
		if isBond:
			plugin="net.conf.bonds."+ebond+".ip"
		elif isVlan:
			plugin="net.conf.vlans."+ebond+".ip"
		else:
			plugin="net.conf."+ebond+".ip"
		
		if bExecuteLater:
			if self.live_update:
				if running_ip != None:
					self.output.debug("Setting running"+ ebond +" IP")
					msg = self.executePluginLater(plugin, "set_active", [running_ip])
			
			if boot_ip != None:
				self.output.debug("Setting boot "+ ebond +" IP")
				msg = self.executePluginLater(plugin, "set_boot", [boot_ip])
		
		else:
			if self.live_update:
				if running_ip != None:
					self.output.debug("Setting running"+ ebond +" IP")
					msg = self.executePlugin(plugin, "set_active", [running_ip])
					if re.search('Error', msg):
						self.output.warning("Please create  plugin for %s by adding configuration by enabling the interface" %plugin)
						self.output.debug("Please create  plugin for %s" %(ebond)+msg)
						return 1
			
			
			if boot_ip != None:
				self.output.debug("Setting boot "+ ebond +" IP")
				msg = self.executePlugin(plugin, "set_boot", [boot_ip])
				if re.search('Error', msg):
					self.output.warning("Please create  plugin for %s by adding configuration by enabling the interface" %plugin)
					self.output.debug("Please create plugin for %s" %(ebond)+msg)
					return 1
		
		return 0

