#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import bash
from includes import *
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
# self.log.error, self.log.warning, self.log.info, self.log.debug


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
	
		dic = []
		return dic
	
	
	
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" configuration"
		msg = "Configure access "+self.PluginName+".\n"
		if self.PluginName == "mode":
			msg += "--set [direct/nat]\n"
			msg += "                   : Set access mode to either bridge or nat\n"
			msg += "                    In nat mode the access bridge must have a static IP\n"
		else:
			msg += "--set OVS_BRIDGE   : Set access bridge for OpenKVI VM.\n"
		msg += " \n"
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		if self.PluginName == "mode":
			if data not in ["direct", "nat"]:
				self.output.error('Access mode must be either "direct" or "nat".')
				return None
		else:
			strBrList = self.executePlugin('net.bridges', 'get')
			brList = strBrList.split(' ')
			if data not in brList:
				self.output.error('Access bridge has not been found, please create it first.')
				return None
		return data
	
	def get(self):
		self.show()
		return 0
	
	def set(self, data):
		''' MANDATORY !
		    define how to set the plugin with "data" '''
		try:
			if self.PluginName == "mode":
				
				BR_MGNT = self.executePlugin('openkvi.access.bridge', 'get')
				if data == "nat":
					if not BR_MGNT or re.search('Error', BR_MGNT):
						self.output.error('Please set OpenKVI access bridge first.')
						return 1
					MGNT = BR_MGNT+"-mgnt"
					
					if os.path.exists('/etc/comverse/openkvi_nat'):
						bash.run('sh /etc/comverse/openkvi_nat stop')
					
					openkvi_nat = []
					openkvi_nat.append('#/bin/sh\n')
					openkvi_nat.append('OPT=$1\n')
					openkvi_nat.append('function start {\n')
					openkvi_nat.append('  iptables -t nat -A POSTROUTING -o '+MGNT+' -j MASQUERADE\n')
					openkvi_nat.append('  iptables -I FORWARD -p tcp -i '+MGNT+' -d 192.168.122.2 --dport 80 -j ACCEPT\n')
					openkvi_nat.append('  iptables -I FORWARD -p tcp -i '+MGNT+' -d 192.168.122.2 --dport 443 -j ACCEPT\n')
					openkvi_nat.append('  iptables -I FORWARD -p tcp -i '+MGNT+' -d 192.168.122.2 --dport 8700:9700 -j ACCEPT\n')
					openkvi_nat.append('  iptables -I FORWARD -i '+MGNT+' -o openkvibr0 -j ACCEPT\n')
					openkvi_nat.append('  iptables -I FORWARD -i openkvibr0 -o '+MGNT+' -j ACCEPT\n')
					openkvi_nat.append('  iptables -t nat -A PREROUTING -p tcp -i '+MGNT+' --dport 80 -j DNAT --to-destination 192.168.122.2:80\n')
					openkvi_nat.append('  iptables -t nat -A PREROUTING -p tcp -i '+MGNT+' --dport 443 -j DNAT --to-destination 192.168.122.2:443\n')
					openkvi_nat.append('  iptables -t nat -A PREROUTING -p tcp -i '+MGNT+' --dport 8700:9700 -j DNAT --to-destination 192.168.122.2\n')
					openkvi_nat.append('}\n')
					openkvi_nat.append('function stop {\n')
					openkvi_nat.append('  iptables -t nat -D POSTROUTING -o '+MGNT+' -j MASQUERADE\n')
					openkvi_nat.append('  iptables -D FORWARD -p tcp -i '+MGNT+' -d 192.168.122.2 --dport 80 -j ACCEPT\n')
					openkvi_nat.append('  iptables -D FORWARD -p tcp -i '+MGNT+' -d 192.168.122.2 --dport 443 -j ACCEPT\n')
					openkvi_nat.append('  iptables -D FORWARD -p tcp -i '+MGNT+' -d 192.168.122.2 --dport 8700:9700 -j ACCEPT\n')
					openkvi_nat.append('  iptables -D FORWARD -i '+MGNT+' -o openkvibr0 -j ACCEPT\n')
					openkvi_nat.append('  iptables -D FORWARD -i openkvibr0 -o '+MGNT+' -j ACCEPT\n')
					openkvi_nat.append('  iptables -t nat -D PREROUTING -p tcp -i '+MGNT+' --dport 80 -j DNAT --to-destination 192.168.122.2:80\n')
					openkvi_nat.append('  iptables -t nat -D PREROUTING -p tcp -i '+MGNT+' --dport 443 -j DNAT --to-destination 192.168.122.2:443\n')
					openkvi_nat.append('  iptables -t nat -D PREROUTING -p tcp -i '+MGNT+' --dport 8700:9700 -j DNAT --to-destination 192.168.122.2\n')
					openkvi_nat.append('}\n')
					openkvi_nat.append('if [ "$OPT" == "start" ]; then\n')
					openkvi_nat.append('  start\n')
					openkvi_nat.append('  rm -f /etc/sysconfig/iptables\n')
					openkvi_nat.append('  service iptables save\n')
					openkvi_nat.append('elif [ "$OPT" == "stop" ]; then\n')
					openkvi_nat.append('  stop\n')
					openkvi_nat.append('  rm -f /etc/sysconfig/iptables\n')
					openkvi_nat.append('  service iptables save\n')
					openkvi_nat.append('elif [ "$OPT" == "restart" ]; then\n')
					openkvi_nat.append('  stop\n')
					openkvi_nat.append('  start\n')
					openkvi_nat.append('fi\n')
					open("/etc/comverse/openkvi_nat", "w").writelines(openkvi_nat)
					
					bash.run('sh /etc/comverse/openkvi_nat start')
					rc_local = open("/etc/rc.d/rc.local").readlines()
					final_rc_local = []
					for line in rc_local:
						append = True
						if re.match('^iptables .* '+MGNT+' .*', line):
							append = False
						if re.match('# OpenKVI Nating.*', line):
							append = False
						if re.match('sh /etc/comverse/openkvi_nat restart', line):
							append = False
						
						if append:
							final_rc_local.append(line)
						
					final_rc_local.append("# OpenKVI Nating:\n")
					final_rc_local.append("sh /etc/comverse/openkvi_nat restart\n")
					open("/etc/rc.d/rc.local", "w").writelines(final_rc_local)
					self.output.info("OpenKVI access mode set to nat")
				else:
					# We do nothing in bridged mode
					self.output.info("OpenKVI access mode set to bridge")
					
			else:
				MGNT_MODE = self.executePlugin('openkvi.access.mode', 'get')
				if MGNT_MODE == "nat":
					self.executePluginLater('openkvi.access.mode', 'set', 'nat')
				self.output.info("OpenKVI access bridge set to "+data)
				
		except:
			err = str(sys.exc_info()[1])
			self.output.error(err)
			return 1
		
		return 0
