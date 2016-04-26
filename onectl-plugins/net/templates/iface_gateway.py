#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import ipvalidation
from includes import ipaddr
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
		return dic
	
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" configuration"
		msg = "Set a gateway per interface.\n"
		msg += "--set GATEWAY  : Set default route for this interface\n"
		msg += "                 eg: --set 192.168.1.254\n"
		msg += '                 Use "none" to disable a gateway setting.\n'
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
		
	def get(self):
		try:
			gateway = "none"
			iface = self._get_device_name()
			if os.path.exists("/etc/sysconfig/network-scripts/route-"+iface):
				tmp_lines = open('/etc/sysconfig/network-scripts/route-'+iface, 'r').readlines()
				for line in tmp_lines:
					if re.search("to default via", line):
						gateway = re.sub(" dev.*", '', re.sub(".*to default via ", '', line)).strip()
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
			netmask = ""
			prefix = ""
			ip = ""
			
			iface = self._get_device_name()
			## Add table entry in /etc/iproute2/rt_tables if needed ##
			if data == "none":
				if os.path.exists("/etc/sysconfig/network-scripts/route-"+iface):
					os.remove('/etc/sysconfig/network-scripts/route-'+iface)
				if os.path.exists("/etc/sysconfig/network-scripts/rule-"+iface):
					os.remove('/etc/sysconfig/network-scripts/rule-'+iface)
				if self.live_update:
					if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+iface):
						tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+iface, 'r').readlines()
						for line in tmp_lines:
							if re.match('^NETMASK *=', line):
								args = line.split('=')
								netmask = re.sub('"', '', args[1]).strip()
							if re.match('^IPADDR *=', line):
								args = line.split('=')
								ip = re.sub('"', '', args[1]).strip()
					
					if netmask and ip:
						ipv4 = ipaddr.IPv4Network(ip+'/'+netmask)
						prefix = str(ipv4.prefixlen)
						bash.run('ip route del default via '+data+' table rtable.'+iface)
						bash.run('ip rule del from '+ip+"/"+prefix+' table rtable.'+iface)
			else:
				rt_toadd = True
				rt_lines = []
				index = 1
				tmp_lines = open('/etc/iproute2/rt_tables', 'r').readlines()
				for line in tmp_lines:
					if re.match("^"+str(index)+" ", line):
						index += 1
					elif re.search("^"+str(index)+"\t", line):
						index += 1
					if re.search(" rtable."+iface+"$", line):
						rt_toadd = False
					elif re.search("\trtable."+iface+"$", line):
						rt_toadd = False
					rt_lines.append(line)
				if rt_toadd:
					if index > 252 :
						self.output.error("No more free routes, please cleanup /etc/iproute2/rt_tables.")
						return 1
					rt_lines.append(str(index)+"\trtable."+iface+"\n")
					open('/etc/iproute2/rt_tables', 'w').writelines(rt_lines)
				
				## Get netmask in ifcfg-iface ##
				if os.path.exists("/etc/sysconfig/network-scripts/ifcfg-"+iface):
					tmp_lines = open('/etc/sysconfig/network-scripts/ifcfg-'+iface, 'r').readlines()
					for line in tmp_lines:
						if re.match('^NETMASK *=', line):
							args = line.split('=')
							netmask = re.sub('"', '', args[1]).strip()
						if re.match('^IPADDR *=', line):
							args = line.split('=')
							ip = re.sub('"', '', args[1]).strip()
				
				if not netmask or not ip:
					self.output.error("Cannot find "+iface+" netmask, please set its IP configuration first.")
					return 1
				
				ipv4 = ipaddr.IPv4Network(ip+'/'+netmask)
				prefix = str(ipv4.prefixlen)
				
				# Write rule-iface file
				lines = []
				lines.append("from "+ip+"/"+prefix+" table rtable."+iface+"\n")
				open('/etc/sysconfig/network-scripts/rule-'+iface, 'w').writelines(lines)
				
				# Write route-iface file
				lines = []
				lines.append("table rtable."+iface+" to "+ip+"/"+prefix+" dev "+iface+"\n")
				lines.append("table rtable."+iface+" to default via "+data+" dev "+iface+"\n")
				open('/etc/sysconfig/network-scripts/route-'+iface, 'w').writelines(lines)
				
				if self.live_update:
					bash.run('ip route add default via '+data+' table rtable.'+iface)
					bash.run('ip rule add from '+ip+"/"+prefix+' table rtable.'+iface)
			
		except:
			err = str(sys.exc_info()[1])
			self.output.error(err)
			return 1
		
		self.output.title(iface+" gateway set to:")
		self.output.info(data)
		return 0
	
	def _get_device_name(self):
		dev = re.sub('.*conf.', '', re.sub('.gateway$', '', self.PluginFqn))
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
	
	def hook(self, *args):
		''' hooking function '''
		try:
			print args
		
		except:
			err = str(sys.exc_info()[1])
			self.output.error(err)
			return 1
		
		return 0


