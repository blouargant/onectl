#!/usr/bin/python -u
""" 
Handle Node's network configuration 
"""

import sys
import subprocess
import os
import json
#require python-xmltodict
import xmltodict
import re
import time
#require libvirt-python
import libvirt
import bash

class NetworkControler:
	def __init__(self, debug=False):
		self.debug = debug
		self.connection = libvirt.open("qemu:///system")
		self.netconfig = {}
		self.netconfig["ovs"] = {}
		self.netconfig["lbr"] = {}
		self.netconfig["virtualnet"] = {}
		self.physicalInterfaces = []
	
	def sh_command(self, command):
		""" Send bash command """
		return bash.run(command)
	
	def sh_query(self, command):
		""" Send bash query, only return result """
		res, err = bash.run(command)
		return res
	
	def getConfig(self):
		"""Read Node's network settings"""
		ovs_cfg = {}
		self.netconfig["physicals"] = self.get_physicalInterfaces()
		self.netconfig["virtualnet"] = self.get_virtualNetworks()
		
		shres = self.sh_query('/bin/ls -l /var/run/openvswitch/db.sock')
		if shres:
			ovs_cfg = self.ovs_show()
		else:
			ovs_cfg["error"] = "No openvswitch process"
		self.netconfig["ovs"] = ovs_cfg
		
		self.netconfig["lbr"] = self.brctl_show()
		return self.netconfig
	
	def updateBridgesInfo(self):
		""" Update self.netconfig["ovs"] and self.netconfig["lbr"] information
		"""
		shres = self.sh_query('/bin/ls -l /var/run/openvswitch/db.sock')
		if shres:
			ovs_cfg = self.ovs_show()
		else:
			ovs_cfg["error"] = "No openvswitch process"
		self.netconfig["ovs"] = ovs_cfg
		
		self.netconfig["lbr"] = self.brctl_show()
	
	
	def get_physicalInterfaces(self):
		try:
			self.physicalInterfaces = []
			phy_cfg = {}
			phy_cfg["error"] = ""
			phy_cfg["ifaces"] = []
			cmd_list = []
			eth_list = []
			sriov_physical_functions = []
			sriov_virtual_functions = []
			
			# Search for SRIOV physical devices
			cmd = 'find /sys/devices -name sriov_numvfs | sed -e s|/sriov_numvfs|| | xargs -i -t ls {}/net'
			sriov_physical_functions = self.sh_query(cmd)
			# Search for SRIOV virtual functions
			cmd = 'find /sys/devices -name physfn | sed -e s|/physfn|| | xargs -i -t ls {}/net'
			sriov_virtual_functions = self.sh_query(cmd)
			# Search for Network Devices
			cmd = 'find /sys/devices -name net | grep -v virtual | xargs -i -t ls {}/'
			cmd_res = self.sh_query(cmd).split("\n")
			for eth in cmd_res:
				if eth not in sriov_virtual_functions:
					eth_list.append(eth)
				
			
			cmd_list = []
			for eth_name in eth_list:
				new_eth = {}
				new_eth['name'] = eth
				
				cmd = 'ls -l /sys/class/net/'+eth_name+'/device | sed -e s/.*->// | sed -e s/.*\///'
				new_eth['bus'] = self.sh_query(cmd).strip()
				
				cmd = 'ls -l /sys/class/net/'+eth_name+'/device/ | grep subsystem | grep -> | sed -e s/.*->// | sed -e s/.*\///'
				new_eth['subsystem'] = self.sh_query(cmd).strip()
				
				cmd = 'cat /sys/class/net/'+eth_name+'/operstate'
				new_eth['state'] = self.sh_query(cmd)
				
				cmd = 'cat /sys/class/net/'+eth_name+'/duplex'
				new_eth['duplex'] = self.sh_query(cmd)
				
				cmd = 'cat /sys/class/net/'+eth_name+'/speed'
				new_eth['speed'] = self.sh_query(cmd)
				
				if new_eth['bus'] != "usb":
					cmd_tmp = 'lspci -s '+new_eth['bus']+' | sed -e s/.*://'
					new_eth['info'] = self.sh_query(cmd).strip()
				
				if eth in sriov_physical_functions:
					cmd = 'find /sys/devices -name '+eth+' | sed -e s|/net/'+eth+'|| | xargs -i -t cat {}/sriov_totalvfs'
					shRes = self.sh_query(cmd).strip().split("\n")
					for aline in shRes:
						nb_vf = aline.strip()
					new_eth['sriov'] = nb_vf
				else:
					new_eth['sriov'] = '0'
				
				phy_cfg["ifaces"].append(new_eth)
				self.physicalInterfaces.append(eth)
		except:
			self.log_error("Failed to get physicals devices: %s" % str(sys.exc_info()[1]))
			print "Error: Failed to get physicals devices: %s" % str(sys.exc_info()[1])
		
		return phy_cfg
	
	def get_management_interface(self):
		result = ""
		regexp = re.compile('^management *= *\\"*yes', re.I)
		for file in os.listdir('/etc/sysconfig/network-scripts/'):
			if "ifcfg-" in file:
				for line in open('/etc/sysconfig/network-scripts/'+file).readlines():
					if regexp.search(line):
						result = file.strip("ifcfg-")
		return result
	
	def ovs_show(self):
		"""Get OVS configuration"""
		ovs_cfg = {}
		ovs_cfg["error"] = "None"
		ovs_cfg["bridges"] = []
		brlist = {}
		MNGT = self.get_management_interface()
		shRes = self.sh_query('/usr/bin/ovs-vsctl show').split("\n")
		brname = ""
		for aline in shRes:
			aline = aline.strip()
			if 'Bridge' in aline:
				tmpargs = aline.split(" ")
				brname = tmpargs[1].strip('"')
				brlist[brname] = {}
				brlist[brname]["ports"] = []
				res = self.sh_query('ip addr show ' +brname).split("\n")
				for resline in res:
					if "inet " in resline:
						tmpstr1 = resline.strip().split(" brd")
						tmpstr2 = tmpstr1[0].split("inet ")
						brlist[brname]["inet"] = tmpstr2[1].strip()
			elif 'Port' in aline:
				tmpargs = aline.split(" ")
				portname = tmpargs[1].strip('"')
				if portname != brname:
					brlist[brname]["ports"].append(portname)
					brlist[brname][portname] = {}
					brlist[brname][portname]["ifaces"] = []
					res = self.sh_query('ip addr show ' +portname).split("\n")
					for resline in res:
						if "inet " in resline:
							tmpstr1 = resline.strip().split(" brd")
							tmpstr2 = tmpstr1[0].split("inet ")
							brlist[brname][portname]["inet"] = tmpstr2[1].strip()
			elif 'Interface' in aline:
				if portname != brname:
					tmpargs = aline.split(" ")
					inetname = tmpargs[1].strip('"')
					brlist[brname][portname]["ifaces"].append(inetname)
			elif 'tag:' in aline:
				if portname != brname:
					tmpargs = aline.split(":")
					tagnum = tmpargs[1].strip()
					brlist[brname][portname]["tag"] = tagnum
		
		for a_br in brlist.keys():
			new_br = {}
			new_br['name'] = a_br
			if a_br == MNGT:
				new_br['mngt'] = "yes"
			else:
				new_br['mngt'] = "no"
			if brlist[a_br].has_key("inet"):
				new_br['inet'] = brlist[a_br]["inet"]
			else:
				new_br['inet'] = "none"
			new_br['type'] = 'private'
			new_br['ports'] = []
			access = []
			for a_port in brlist[a_br]["ports"]:
				new_port = {}
				new_port['name'] = a_port
				new_port['ifaces'] = brlist[a_br][a_port]['ifaces']
				for an_iface in new_port['ifaces']:
					if an_iface in self.physicalInterfaces:
						new_br['type'] = 'public'
						access.append(a_port)
						break
				if brlist[a_br][a_port].has_key('tag'):
					new_port['tag'] = brlist[a_br][a_port]['tag']
				else:
					new_port['tag'] = '-1'
				
				if new_br['type'] == 'private' and a_port == a_br+"-nic":
					new_br['type'] = 'virtual'
				new_br['ports'].append(new_port)
				new_br['access'] = ', '.join(access)
			
			ovs_cfg['bridges'].append(new_br)
			
			
		bond_res = self.sh_query('/usr/bin/ovs-appctl bond/list').split("\n")
		ovs_cfg["bonds"] = []
		bondlist = {}
		if len(bond_res) > 1:
			for aline in bond_res[1:]:
				aline = aline.strip()
				if aline:
					tmpargs = aline.split("\t")
					bondlist[tmpargs[0]] = {}
					bondlist[tmpargs[0]]["mode"] = tmpargs[1]
					bondlist[tmpargs[0]]["ifaces"] = []
					for inet in tmpargs[2].split(","):
						bondlist[tmpargs[0]]["ifaces"].append(inet.strip())
			
		for a_bond in bondlist.keys():
			new_bond = {}
			new_bond['name'] = a_bond
			new_bond['mode'] = bondlist[a_bond]['mode']
			new_bond['ifaces'] = bondlist[a_bond]['ifaces']
			ovs_cfg["bonds"].append(new_bond)
		
		return ovs_cfg
	
	def brctl_show(self):
		"""Get Linux bridges settings"""
		brctl_cfg = {}
		brctl_cfg["error"] = "None"
		brctl_cfg["bridges"] = []
		shRes = self.sh_query('/usr/sbin/brctl show').split("\n")
		shRes = filter(None, shRes)
		if len(shRes) > 1:
			brname = ""
			firstbr = True
			for aline in shRes[1:]:
				aline = aline.strip()
				if aline:
					tmpargs = aline.split("\t")
					brinfos = []
					for anarg in tmpargs:
						if len(anarg) > 0:
							brinfos.append(anarg)
					if len(brinfos) > 1:
						if not firstbr:
							brctl_cfg["bridges"].append(newbr)
						else:
							firstbr = False
						
						newbr = {}
						newbr["name"] = brinfos[0]
						newbr["ifaces"] = []
						if len(brinfos) > 3: 
							newbr["ifaces"].append(brinfos[3])
					elif len(brinfos) == 1:
						newbr["ifaces"].append(brinfos[0])
			if newbr:
				brctl_cfg["bridges"].append(newbr)
		return brctl_cfg
	
	def get_virtualNetworks(self):
		"""
		Get Network defined on node
		"""
		try:
			virtnet_cfg = {}
			virtnet_cfg["error"] = ""
			network_list = self.connection.listNetworks()
			network_list_inactive = self.connection.listDefinedNetworks()
			network_list.extend(network_list_inactive)
			networks = []
			for aNet in network_list:
				net_infos = {}
				net_infos['name'] = aNet
				net_infos['type'] = ""
				pgroup = False
				
				network = self.connection.networkLookupByName(aNet)
				XMLDesc = network.XMLDesc(0)
				infos = xmltodict.parse(XMLDesc)['network']
				if infos.has_key('@connections'):
					net_infos['connections'] = infos['@connections']
				else:
					net_infos['connections'] = "0"
				
				if infos.has_key('forward') and infos['forward'].has_key('@mode'):
					net_infos['mode'] = infos['forward']['@mode']
					## Hanble SR-IOV devices
					if net_infos['mode'] == "hostdev":
						if infos['forward'].has_key('pf') and infos['forward']['pf'].has_key('@dev'):
							net_infos['sriov_dev'] = infos['forward']['pf']['@dev']
							pgroup = True
							net_infos['type'] = 'sriov'
						else:
							net_infos['sriov_dev'] = ""
				else:
					net_infos['mode'] = "private"
				
				net_infos['portgroups'] = []
				if infos.has_key('portgroup'):
					if isinstance(infos['portgroup'], list):
						for aGroup in infos['portgroup']:
							group_infos = {}
							group_infos['name'] = aGroup['@name']
							if aGroup.has_key('@default'):
								group_infos['is_default'] = aGroup['@default']
							else:
								group_infos['is_default'] = "no"
							if aGroup.has_key('vlan'):
								group_infos['vlan_id'] = aGroup['vlan']['tag']['@id']
							else:
								group_infos['vlan_id'] = "-1"
							net_infos['portgroups'].append(group_infos)
					else:
						group_infos = {}
						group_infos['name'] = infos['portgroup']['@name']
						if infos['portgroup'].has_key('@default'):
							group_infos['is_default'] = infos['portgroup']['@default']
						else:
							group_infos['is_default'] = "no"
						if infos['portgroup'].has_key('vlan'):
							group_infos['vlan_id'] = infos['portgroup']['vlan']['tag']['@id']
						else:
							group_infos['vlan_id'] = "-1"
						net_infos['portgroups'].append(group_infos)
				
				else:
					group_infos = {}
					group_infos['name'] = ""
					group_infos['is_default'] = "yes"
					if infos.has_key('vlan'):
						group_infos['vlan_id'] = infos['vlan']['tag']['@id']
					else:
						group_infos['vlan_id'] = "-1"
					net_infos['portgroups'].append(group_infos)
				
				if infos.has_key('bridge') and infos['bridge'].has_key('@name'):
					net_infos['bridge'] = infos['bridge']['@name']
					if net_infos['bridge'] == "private_"+net_infos['name']:
						net_infos['mode'] = "private"
				else:
					net_infos['bridge'] = ""
				
				if infos.has_key('virtualport') and infos['virtualport'].has_key('@type'):
					net_infos['type'] = infos['virtualport']['@type']
				
				net_infos['active'] = network.isActive()
				net_infos['persistent'] = network.isPersistent()
				net_infos['autostart'] = network.autostart()
				networks.append(net_infos)
			
			virtnet_cfg["networks"] = networks
			
		except:
			self.log_error("Failed to get networks: %s" % str(sys.exc_info()[1]))
			virtnet_cfg["error"] = "Error: cannot get networks: %s" % str(sys.exc_info()[1])
		return virtnet_cfg
	
	def generate_network_xml(self, network):
		"""
		Create a Libvirt network
		INPUT:
		    network['name']       : Virtual Network's name
		    network['type']       : private/openvswitch/sriov
		    network['bridge']     : Either a bridge or a PF (if type = sriov)
		    network['portgroups'] : List of portgroups with :
		        portgroup['is_default']  : yes/no 
		        portgroup['name']        : Portgroup's name
				portgroup['vlan_id']     : VLAN tag
		"""
		result = ""
		try:
			self.log_debug("creating virtual network %s" % network['name'])
			desc = '<network>'
			desc += '<name>'+network['name']+'</name>'
			if network['type'] == "private":
				desc += '<bridge name="private_'+network['name']+'" />'
				desc += '<forward mode="bridge" />'
				desc += '<virtualport type="openvswitch"/>'
				
			elif network['type'] == "openvswitch":
				src = network['bridge']
				desc += '<bridge name="'+src+'" />'
				desc += '<forward mode="bridge" />'
				desc += '<virtualport type="openvswitch"/>'
				
			elif network['type'] == "sriov":
				if network.has_key('sriov_dev'):
					src = network['sriov_dev']
				else:
					src = network['bridge']
				
				desc += '<forward mode="hostdev" managed="yes">'
				desc += '<pf dev="'+src+'"/>'
				desc += '</forward>'
				
			if network.has_key("portgroups"):
				for portgroup in network["portgroups"]:
					if portgroup['is_default'] == "yes":
						pdefault = 'default="yes" '
						if portgroup['name'] == "":
							pname = 'Default'
						else:
							pname = portgroup['name']
					else:
						pdefault = ''
						pname = portgroup['name']
					desc += '<portgroup name="'+pname+'" '+pdefault+'>'
					if portgroup['vlan_id'] != "-1":
						desc += '<vlan>'
						desc += '<tag id="'+portgroup['vlan_id']+'"/>'
						desc += '</vlan>'
					desc += '</portgroup>'
			desc += '</network>'
			result = desc
		
		except:
			self.log_error("Failed to create network s: %s" % str(sys.exc_info()[1]))
			result = "Error: cannot generate network XML: %s" % str(sys.exc_info()[1])
			
		return result
	
	def create_virtualNetwork(self, data):
		"""
		Create a Libvirt network
		"""
		result = self._create_virtualNetwork(data)
		self.netconfig["virtualnet"] = self.get_virtualNetworks()
		return result
	
	def _create_virtualNetwork(self, data):
		result = "Success"
		try:
			network = json.loads(data)
			net_xml = self.generate_network_xml(network)
			if "Error: " in net_xml:
				return net_xml
			
			if network['type'] == "private":
				self.ovs_create_bridge("private_"+network['name'])
			
			for aVnet in self.netconfig["virtualnet"]['networks']:
				if aVnet['name'] == network['name']:
					self._remove_virtualNetwork(json.dumps(aVnet))
					break
			libvirt_network = self.connection.networkDefineXML(net_xml)
			libvirt_network.create()
			libvirt_network.setAutostart(1)
			
		except:
			self.log_error("Failed to create network: %s" % str(sys.exc_info()[1]))
			result = "Error: cannot create network: %s" % str(sys.exc_info()[1])
		return result
	
	def update_virtualNetwork(self, data):
		"""
		Update a Libvirt network
		"""
		result = "Success"
		try:
			result = self._remove_virtualNetwork(data)
			result = self._create_virtualNetwork(data)
			self.netconfig["virtualnet"] = self.get_virtualNetworks()
			
		except:
			self.log_error("Failed to create network s: %s" % str(sys.exc_info()[1]))
			result = "Error: cannot update network: %s" % str(sys.exc_info()[1])
		return result
	
	def remove_virtualNetwork(self, data):
		"""
		Remove a Libvirt network
		"""
		result = self._remove_virtualNetwork(data)
		self.netconfig["virtualnet"] = self.get_virtualNetworks()
		return result
	
	def _remove_virtualNetwork(self, data):
		try:
			
			network = json.loads(data)
			if network.has_key('old_name'):
				vswitch = network['old_name']
			else:
				vswitch = network['name']
			try:
				libvirt_network = self.connection.networkLookupByName(vswitch)
			except:
				return "Virtual Network %s not found !" % vswitch
			
			if network['type'] == "openvswitch" and network['mode'] == "private":
				self.ovs_remove_bridge("private_"+network['name'])
			
			if libvirt_network.isActive():
				libvirt_network.destroy()
			libvirt_network.undefine()
			del libvirt_network
			return "Success"
			
		except:
			self.log_warning("Failed to remove network: %s" % str(sys.exc_info()[1]))
			return "Error: cannot remove: %s" % str(sys.exc_info()[1])
	
	def start_vswitch(self, vswitch):
		try:
			libvirt_network = self.connection.networkLookupByName(vswitch)
			libvirt_network.create()
		except:
			self.log_warning("Failed to stop vswitch: %s" % str(sys.exc_info()[1]))
			return "Error: stop vswitch: %s" % str(sys.exc_info()[1])
	
	def stop_vswitch(self, vswitch):
		try:
			libvirt_network = self.connection.networkLookupByName(vswitch)
			libvirt_network.destroy()
		except:
			self.log_warning("Failed to stop vswitch: %s" % str(sys.exc_info()[1]))
			return "Error: stop vswitch: %s" % str(sys.exc_info()[1])
	
	def restart_virtualNetworks(self):
		try:
			self.getConfig()
			vswitches = self.netconfig['virtualnet']['networks']
			vmList = self.list_all_vmnets();
			for vswitch in vswitches:
				print "Restarting virtual network "+vswitch['name']+" ..."
				if vswitch['active']:
					self.stop_vswitch(vswitch['name'])
				if vswitch['autostart'] and vswitch['persistent']:
					self.start_vswitch(vswitch['name'])
			
			print "Re-attaching vnets ..."
			for vm in vmList:
				for vnic in vm['vnics']:
					if vnic['target']:
						res = self.attach_virtual_interface(vnic['target'], vnic['source'], vnic['vlan_id'])
		
		except:
			self.log_warning("Failed to restart virtual networks: %s" % str(sys.exc_info()[1]))
			return "Error: cannot restart networks: %s" % str(sys.exc_info()[1])
		return "Virtual Networks restarted."
	
	def start_virtualNetworks(self):
		try:
			self.getConfig()
			vswitches = self.netconfig['virtualnet']['networks']
			vmList = self.list_all_vmnets();
			for vswitch in vswitches:
				print "Starting virtual network "+vswitch['name']+" ..."
				if vswitch['autostart'] and vswitch['persistent']:
					self.start_vswitch(vswitch['name'])
			
			print "Attaching vnets ..."
			for vm in vmList:
				for vnic in vm['vnics']:
					if vnic['target']:
						res = self.attach_virtual_interface(vnic['target'], vnic['source'], vnic['vlan_id'])
		
		except:
			self.log_warning("Failed to start virtual networks: %s" % str(sys.exc_info()[1]))
			return "Error: cannot start networks: %s" % str(sys.exc_info()[1])
		return "Virtual Networks started."
	
	def stop_virtualNetworks(self):
		try:
			self.getConfig()
			vswitches = self.netconfig['virtualnet']['networks']
			for vswitch in vswitches:
				print "Stopping virtual network "+vswitch['name']+" ..."
				if vswitch['active']:
					self.stop_vswitch(vswitch['name'])
		except:
			self.log_warning("Failed to stop virtual networks: %s" % str(sys.exc_info()[1]))
			return "Error: cannot stop networks: %s" % str(sys.exc_info()[1])
		return "Virtual Networks stopped."
	
	def list_all_vmnets(self):
		"""
		List all virtual networks for all VMs define in database for KVM node <node>
		OUTPUT: list of dictionaries containing the following:
			info['name']  : Virtual machine's name
			info['vnics'] : List of vnic links for a given VM
			                see get_active_domain_extended_vnics(node, domain) for
			                the description of the 'vnics' list
		"""
		result = []
		try:
			idList = self.connection.listDomainsID()
			for id in idList:
				vm = self.connection.lookupByID(id).name()
				vmInfo = {}
				vmInfo = self.extend_vnet_infos(self.get_domain_vnets(vm))
				vmInfo['name'] = vm
				result.append(vmInfo)
		except:
			self.log_warning("Failed to list VMs networks: %s" % str(sys.exc_info()[1]))
			return "Error: cannot list all VMs networks: %s" % str(sys.exc_info()[1])
		
		return result
	
	def get_domain_vnets(self, vm):
		""" Get the list of vnets from a running domain
		INPUT: a VM name
		OUPUT: a list of VM virtual networks dictionaries containing:
		info['mac']       : Mac Address
		info['type']      : connection type, either "network" or "bridge"
		info['vswitch']   : Libvirt Vswitch name
		info['portgroup'] : Libvirt portgroup (default if empty)
		info['target']    : vnet target if it exists (none otherwise)
		info['state']     : vnic state = up/down
		"""
		result = []
		try:
			domain = self.connection.lookupByName(vm)
			dom_xml = domain.XMLDesc(0)
			dom_dict = xmltodict.parse(dom_xml)
			dom_interface_list = dom_dict['domain']['devices']['interface']
			if isinstance(dom_interface_list, list):
				interface_list = dom_interface_list
			else:
				interface_list = []
				interface_list.append(dom_interface_list)
				
			for dom_interface in interface_list:
				#print dom_interface
				info = {}
				info['mac'] = dom_interface['mac']['@address']
				info['type'] = dom_interface['@type']
				if info['type'] == "network":
					info['vswitch'] = dom_interface['source']['@network']
				elif info['type'] == "bridge":
					info['vswitch'] = dom_interface['source']['@bridge']
				if dom_interface['source'].has_key('@portgroup'):
					info['portgroup'] = dom_interface['source']['@portgroup']
				else:
					info['portgroup'] = ""
				
				if dom_interface.has_key('target') and dom_interface['target'].has_key('@dev'):
					info['target'] = dom_interface['target']['@dev']
				else:
					info['target'] = None
				
				if dom_interface.has_key('link') and dom_interface['link'].has_key('@state'):
					info['state'] = dom_interface['link']['@state']
				else:
					info['state'] = "down"
				
				
				result.append(info)
				
		except:
			self.logger.log_warning("Failed to get domain vnets: %s" % str(sys.exc_info()[1]))
			return [] # return an empty list if a failure occured
			
		return result
	
	
	def extend_vnet_infos(self, vnetList):
		"""
		Try to get on which interface each vnics are plugged
		INPUT: take a list of vnic info as input, each vnic is a dictionary containing:
			info['mac']        : Mac Address
			info['type']       : connexion type (network or bridge)
			info['vswitch']    : if type = network, then it is the name of the network else it's the bridge name
			info['portgroup']  : name of the portgroup (if empty then it's the default one)
			info['target']     : vnic name on the KVM server (eg vnet1, vnet2 ...) attched to the bridge
			info['state']      : state of the connection, either "up" or "down"
		
		OUTPUT: return the list of dictionary given in INPUT with, for each vnic, the additional below information:
			info['source']     : the name of the OVS or Linux bridge
			info['vlan_id']    : the vlan tag
			info['device_type] : "lbr" for a Linux Bridge, "ovs" for an OpenVswtich bridge
		
		"""
		try:
			if not self.netconfig['virtualnet']:
				self.netconfig["virtualnet"] = self.get_virtualNetworks()
			
			result = {}
			result['error'] = ""
			result['vnics'] = []
			for vnet in vnetList:
				info = vnet
				brName = ""
				device_type = ""
				vlan_id = "-1"
				if info['type'] == "network":
					for aNetwork in self.netconfig['virtualnet']['networks']:
						if aNetwork['name'] == info['vswitch']:
							brName = aNetwork['bridge']
							device_type = aNetwork['type']
							for portgroup in aNetwork['portgroups']:
								if info['portgroup'] == "" and portgroup['is_default'] == "yes":
									vlan_id = portgroup['vlan_id']
									break
								elif info['portgroup'] == portgroup['name']:
									vlan_id = portgroup['vlan_id']
									break
									
							break
				elif info['type'] == "bridge":
					brName = info['vswitch']
					device_type = "lbr"
				
				info['source'] = brName
				info['vlan_id'] = vlan_id
				info['device_type'] = device_type
				result['vnics'].append(info)
			
		except:
			self.log_warning("Failed to extend virtual interfaces infos: %s" % str(sys.exc_info()[1]))
			result['error'] = "Error: cannot extend virtual interfaces infos: %s" % str(sys.exc_info()[1])
		
		return result
	
	def update_target_connexion(self, src, dest):
		""" live update of a virtual network interface 
		PARAMS:
			src              : src Dictionary 
			  src['target']     : target name on KVM server
			  src['source']     : Bridge name on KVM server
			  src['state']      : target initial state (up/down)
			dest             : Destination Dictionary
			  dest['type']      : Destination type : network or bridge
			  dest['vswitch']   : Libvirt Virtual Network
			  dest['portgroup'] : Libvirt portgroup in Virtual Network
			  dest['state']     : target final state (used to simulate plug/unplug of network cables)
		return "Success" / "Error: "
		"""
		result = "Success"
		try:
			brDestName = ""
			brSrcName = src['bridge']
			portgroup = dest['portgroup']
			vlan_id = "-1"
			vnet_type = ""
			if dest['type'] == "network":
				for aNetwork in self.netconfig['virtualnet']['networks']:
					if aNetwork['name'] == dest['vswitch']:
						vnet_type = aNetwork['type']
						brDestName = aNetwork['bridge']
						for aGroup in aNetwork['portgroups']:
							if portgroup == "":
								if aGroup['is_default'] == "yes":
									vlan_id = aGroup['vlan_id']
									break
							else:
								if aGroup['name'] == portgroup:
									vlan_id = aGroup['vlan_id']
									break
								
						break
			
			elif dest['type'] == "bridge":
				brDestName = dest['vswitch']
				vlan = '-1'
			
			if vnet_type != "sriov":
				if src['state'] != dest['state']:
					if dest['state'] == "down":
						res = self.detach_virtual_interface(src['target'], brSrcName)
					else:
						res = self.attach_virtual_interface(src['target'], brDestName, vlan_id)
				else:
					res = self.migrate_virtual_interface(src['target'], brSrcName, brDestName, vlan_id)
				self.updateBridgesInfo()
				result = res
			
			else :
				result = "Cannot do a live update of a SR-IOV device !"
			
		
		except:
			self.log_warning("Failed to update virtual interface: %s" % str(sys.exc_info()[1]))
			result = "Error: cannot update virtual interface: %s" % str(sys.exc_info()[1])
		
		return result
	
	def attach_virtual_interface(self, vnet, bridge, vlan):
		""" Attach a virtual network interface to a bridge"""
		result = "Success"
		try:
			done = False
			for aBridge in self.netconfig['ovs']['bridges']:
				if aBridge['name'] == bridge:
					done = True
					if vlan == "-1":
						regexp = ".*--may-exist add-port "+bridge+" "+vnet+"."
						shRes, err = self.sh_command('/usr/bin/ovs-vsctl --may-exist add-port '+bridge+' '+vnet)
					else:
						regexp = ".*--may-exist add-port "+bridge+" "+vnet+" tag="+vlan+"."
						shRes, err = self.sh_command('/usr/bin/ovs-vsctl --may-exist add-port '+bridge+' '+vnet+' tag='+vlan)
					
					if err != "":
						str1 = re.sub(regexp, '', err)
						str2 = re.sub('^ but ', '' ,str1)
						result = "Failed to add port %s to OVS bridge %s: %s" % (vnet, bridge, str2)
						self.log_warning(result)
					
					break
				
			if not done:
				for aBridge in self.netconfig['lbr']['bridges']:
					if aBridge['name'] == bridge:
						shRes, err = self.sh_command('/usr/sbin/brctl addif '+bridge+' '+vnet)
						if err != "":
							self.log_warning("Failed to add port %s to LBR birdge %s: %s" % (vnet, bridge, err))
							result = "Error: "+err
						break
		
		except:
			self.log_warning("Failed to attach virtual interface: %s" % str(sys.exc_info()[1]))
			result = "Error: cannot attach virtual interface: %s" % str(sys.exc_info()[1])
		
		return result
	
	def detach_virtual_interface(self, vnet, bridge):
		""" Attach a virtual network interface to a bridge"""
		result = "Success"
		try:
			done = False
			for aBridge in self.netconfig['ovs']['bridges']:
				if aBridge['name'] == bridge:
					done = True
					shRes, err = self.sh_command('/usr/bin/ovs-vsctl --if-exists del-port '+bridge+' '+vnet)
					if err:
						result = err
					break
			
			if not done:
				for aBridge in self.netconfig['lbr']['bridges']:
					if aBridge['name'] == bridge:
						shRes, err = self.sh_command('/usr/sbin/brctl delif '+bridge+' '+vnet)
						if err :
							result = err
						break
		
		except:
			self.log_warning("Failed to detach virtual interface: %s" % str(sys.exc_info()[1]))
			result = "Error: cannot detach virtual interface: %s" % str(sys.exc_info()[1])
		return result
	
	def migrate_virtual_interface(self, vnet, src_bridge, dst_bridge, vlan):
		""" Attach a virtual network interface to a bridge"""
		result = ""
		try:
			self.detach_virtual_interface(vnet, src_bridge)
			result = self.attach_virtual_interface(vnet, dst_bridge, vlan)
		except:
			self.log_warning("Failed to migrate virtual interface: %s" % str(sys.exc_info()[1]))
			result = "Error: cannot migrate virtual interface: %s" % str(sys.exc_info()[1])
		
		return result
	
	def ovs_create_bridge(self, bridge, interface=None):
		"""
		Create an OpenVswitch bridge
		INPUT:
			bridge     : OVS bridge name
			interface  : OVS egress interface, left empty for a private bridge
		"""
		result = "Success"
		try:
			br_conf = 'DEVICE='+bridge+'\n'
			br_conf += 'NM_CONTROLLED=no\n'
			br_conf += 'DEVICETYPE=ovs\n'
			br_conf += 'ONBOOT=yes\n' 
			br_conf += 'TYPE=OVSBridge\n'
			br_file = open('/etc/sysconfig/network-scripts/ifcfg-'+bridge, 'w')
			br_file.write(br_conf)
			br_file.close()
			
			res, err = self.sh_command('ovs-vsctl --if-exists del-br '+bridge)
			res, err = self.sh_command('ovs-vsctl add-br '+bridge)
			
			if interface:
				self.ovs_add_exit_interface(bridge, interface)
			
			return result
		except:
			self.log_error("Failed to create bridge: %s" % str(sys.exc_info()[1]))
			return "Error: cannot create bridge: %s" % str(sys.exc_info()[1])
	
	def ovs_remove_bridge(self, bridge):
		"""
		Remove an OVS network bridge
		"""
		try:
			res, err = self.sh_command('rm -f /etc/sysconfig/network-scripts/ifcfg-'+bridge)
			res, err = self.sh_command('ovs-vsctl --if-exists del-br '+bridge)
			return err
			
		except:
			self.log_warning("Failed to remove bridge: %s" % str(sys.exc_info()[1]))
			return "Error: cannot remove bridge: %s" % str(sys.exc_info()[1])
	
	def ovs_add_exit_interface(self, bridge, interface):
		""" Add an exit (eth0, eth1, bond0 ...) NIC to an ovs bridge """
		try:
			print "ovs_add_exit_interface"
		except:
			self.log_warning("Failed to add an exit interface to ovs bridge: %s" % str(sys.exc_info()[1]))
			return "Error: cannot add an exit interface to ovs bridge: %s" % str(sys.exc_info()[1])
	
	
	def find_vnet_ip(self, vnet, mac, ip_range):
		"""
		Find with arping2 a vnet's IP address
		"""
		try:
			list_ip = []
			arping_list = []
			range_info = ip_range.split(',')
			start_args = range_info[0].split('.')
			end_args = range_info[1].split('.')
			
			istart = int(start_args[3])
			iend = int(end_args[3])
			for i in range (istart,iend):
				if i == istart:
					ip_source = start_args[0]+"."+start_args[1]+"."+start_args[2]+"."+str(iend)
					ip_dest = start_args[0]+"."+start_args[1]+"."+start_args[2]+"."+str(i)
				else :
					ip_source = start_args[0]+"."+start_args[1]+"."+start_args[2]+"."+str(istart)
					ip_dest = start_args[0]+"."+start_args[1]+"."+start_args[2]+"."+str(i)
				arping_list.append('arping2 -c1 -p -S '+ip_source+' -i '+vnet+' '+mac+' -T '+ip_dest)
			
			cmd = ['tcpdump', '-Klanes0', '-i', vnet, 'ether host', mac]
			proc_tcpdump = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			res = bash.run_parallel(arping_list)
			#time.sleep(2)
			proc_tcpdump.terminate()
			proc_tcpdump.wait()
			for line in proc_tcpdump.stdout:
				if "Request who-has" in line:
					str1 = re.sub('.* tell ', '' , line)
					res_ip = re.sub(',.*', '' , str1).strip()
					if res_ip not in list_ip:
						list_ip.append(res_ip)
			
			result = ', '.join(list_ip)
		except:
			self.log_warning("Failed to find vnet IP address: %s" % str(sys.exc_info()[1]))
			return "Error: cannot find vnet IP address: %s" % str(sys.exc_info()[1])
		return result
	
	def log_error(self, msg):
		self.log(msg, "ERROR")
	
	def log_warning(self, msg):
		self.log(msg, "WARNING")
		
	def log_info(self, msg):
		self.log(msg, "INFO")
		
	def log_event(self, msg):
		self.log(msg, "EVENT")
		
	def log_debug(self, msg):
		self.log(msg, "DEBUG")
	
	def log(self, msg, level):
		if self.debug == True :
			print "["+level+"]::"+msg


if __name__ == '__main__':
	network = NetworkControler()
	#network.getConfig()
	print  network.get_virtualNetworks()

	
