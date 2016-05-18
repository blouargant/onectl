#!/usr/bin/python -u
# Name: fqn.plugin.name

from includes import pluginClass
from includes import bash
from includes import *
import os
import sys
import re
import subprocess
import json
import time
import shutil
#require python-xmltodict
import xmltodict

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
		
		# you will find below an example for a command plugin implementation
		# change the start,stop,restart and status command by whatever commands you
		# need to support.
		
		dic = []
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: start
		opt1 = {}
		opt1['name'] = '--start'
		opt1['metavar'] = ''
		opt1['action'] = 'store_true'
		opt1['nargs'] = ''
		opt1['help'] = 'Start OpenKVI VM.'
		dic.append(opt1)
		### OPTION: stop
		opt2 = {}
		opt2['name'] = '--stop'
		opt2['metavar'] = ''
		opt2['action'] = 'store_true'
		opt2['nargs'] = ''
		opt2['help'] = 'Stop OpenKVI VM'
		dic.append(opt2)
		### OPTION: restart
		opt3 = {}
		opt3['name'] = '--restart'
		opt3['metavar'] = ''
		opt3['action'] = 'store_true'
		opt3['nargs'] = ''
		opt3['help'] = 'Restart OpenKVI VM.'
		dic.append(opt3)
		### OPTION: status
		opt4 = {}
		opt4['name'] = '--status'
		opt4['metavar'] = ''
		opt4['action'] = 'store_true'
		opt4['nargs'] = ''
		opt4['help'] = 'Display OpenKVI VM status.'
		dic.append(opt4)
		
		### OPTION: create [PATH]
		opt5 = {}
		opt5['name'] = '--create'
		opt5['metavar'] = 'ISO_FILE'
		opt5['action'] = 'store'
		opt5['nargs'] = ''
		opt5['help'] = 'Create an OpenKVI Virtual Machine.'
		dic.append(opt5)
		
		### OPTION: kill
		opt6 = {}
		opt6['name'] = '--kill'
		opt6['metavar'] = ''
		opt6['action'] = 'store_true'
		opt6['nargs'] = ''
		opt6['help'] = 'Kill OpenKVI VM.'
		dic.append(opt6)
		
		### OPTION: destroy
		opt6 = {}
		opt6['name'] = '--destroy'
		opt6['metavar'] = ''
		opt6['action'] = 'store_true'
		opt6['nargs'] = ''
		opt6['help'] = 'Removed OpenKVI VM.'
		dic.append(opt6)
		
		
		## To disable the --set options - for a command plugin
		### NO OPTION: set
		opt10 = {}
		opt10['name'] = '--set'
		opt10['metavar'] = ''
		opt10['action'] = ''
		opt10['nargs'] = ''
		opt10['help'] = ''
		dic.append(opt10)
		## To disable the --view options - for a command plugin
		### NO OPTION: view
		opt11 = {}
		opt11['name'] = '--view'
		opt11['metavar'] = ''
		opt11['action'] = ''
		opt11['nargs'] = ''
		opt11['help'] = ''
		dic.append(opt11)
	
		return dic
	
	def info(self):
		''' MANDATORY !'''
		title = self.PluginName+" commands"
		msg = "Manage OpenKVI.\n"
		msg += "--create          : Create OpenKVI\n"
		msg += "The following commands can only bu used if OpenKVI has been created:\n"
		msg += "    --start           : Start OpenKVI\n"
		msg += "    --stop            : Stop OpenKVI\n"
		msg += "    --restart         : Restart OpenKVI\n"
		msg += "    --status          : Display OpenKVI status\n"
		msg += "    --resmove         : Remove OpenKVI\n"
		self.output.help(title, msg)
	
	def inputValidation(self, data):
		''' TO OVERWRITE IN PLUGINS -- MANDATORY --
		In this function, plugin creator must implement a data input validator
		If input is valid then the function must return the data, or else it must return None.
		You can also use this to alter input data in order to support multiple input format.
		This function is automatically called, there is no need to call it within <set> function.
		'''
		data_path = os.path.normpath(os.path.join(self.pwd, data))
		
		res, err = bash.run('file '+data_path)
		if not res:
			self.output.error(data_path+' not found')
			return None
		
		if ': directory' in res:
			if not os.path.exists(data_path+'/ks_openkvi.cfg'):
				self.output.error(data_path+' is not valid: OpenKVI Kickstart cannot be found.')
				return None
		elif "ISO 9660" not in res:
			self.output.error(data_path+' is not a valid ISO file')
			if res:
				self.output.error(res)
			if err:
				self.output.error(err)
			return None
			
		return data_path
	
	
	def get(self):
		self.show()
		return 0
	
	def view(self, *args, **kwds):
		''' override the view function as no data is saved with this plugin '''
		res = self.get()
		return res
	
	def set(self, data):
		return 0
	
	def exists(self):
		created = False
		if os.path.exists("/opt/virtualization/vmdisks/OpenKVI-01.img"):
			created = True
		else:
			res, err = bash.run('virsh list --all')
			if res:
				for line in res:
					if re.search(' OpenKVI ', line):
						created = True
		return created
	
	def start(self, data=''):
		if not self.exists():
			self.output.error("OpenKVI not found, please create it first")
			return 1
		
		try:
			res, err = bash.run('virsh start OpenKVI')
			if err:
				self.output.error(re.sub('error: ', '', err))
			else:
				self.output.info(res)
		except:
			err = str(sys.exc_info()[1])
			self.log.error("dothat "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def stop(self, data=''):
		if not self.exists():
			self.output.error("OpenKVI not found, please create it first")
			return 1
		
		try:
			res, err = bash.run('virsh shutdown OpenKVI')
			if err:
				self.output.error(re.sub('error: ', '', err))
			else:
				self.output.info(res)
		except:
			err = str(sys.exc_info()[1])
			self.log.error("dothat "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def restart(self, data=''):
		if not self.exists():
			self.output.error("OpenKVI not found, please create it first")
			return 1
		
		try:
			self.output.title('Stopping OpenKVI ...')
			res, err = bash.run('virsh shutdown OpenKVI')
			sleep_counter = 0
			sleep_max = 6
			still_running = True
			while sleep_counter != sleep_max:
				if sleep_counter == 2:
					self.output.info('Waiting for OpenKVI to cleanly shutdown ...')
				time.sleep(10)
				sleep_counter += 1
				res, err = bash.run('virsh list')
				if err:
					self.output.error(re.sub('error: ', '', err))
					still_running = True
				else:
					still_running = False
					for line in res.split('\n'):
						if re.search(' OpenKVI ', line):
							still_running = True
				if not still_running:
					self.output.info('OpenKVI has stopped.')
					sleep_counter = sleep_max
			
			if still_running:
				self.output.warning('Forcing OpenKVI to stop ...')
				res, err = bash.run('virsh destroy OpenKVI')
				time.sleep(5)
			
			self.output.title('Restarting OpenKVI ...')
			self.start()
		except:
			err = str(sys.exc_info()[1])
			self.log.error("dothat "+self.PluginName+" "+data+": "+err)
			self.output.error(err)
			return 1
			
		return 0
	
	def status(self, data=''):
		if not self.exists():
			self.output.error("OpenKVI not found, please create it first")
			return 1
		
		res, err = bash.run('virsh list')
		result = "Not Created"
		if err:
			self.output.error(re.sub('error: ', '', err))
		else:
			for line in res.split('\n'):
				if re.search(' OpenKVI ', line):
					result = re.sub('.*OpenKVI *', '', line).strip()
			
			if result == "Not Created":
				res, err = bash.run('virsh list --all')
				if err:
					self.output.error(re.sub('error: ', '', err))
				else:
					for line in res.split('\n'):
						if re.search(' OpenKVI ', line):
							result = re.sub('.*OpenKVI *', '', line).strip()
		
		self.output.info(result)
		return 0
	
	def kill(self, data=''):
		if not self.exists():
			self.output.error("OpenKVI not found, please create it first")
			return 1
		
		self.output.info("Killing OpenKVI process ...")
		res, err = bash.run('virsh destroy OpenKVI')
		if err:
			self.output.error(re.sub('error: ', '', err))
			return 1
		else:
			self.output.info(res)
		return 0
	
	def destroy(self, data=''):
		if not self.exists():
			self.output.warning("OpenKVI VM not found.")
			return 0
		
		MODE = self.executePlugin('openkvi.access.mode', 'get')
		if MODE == 'nat':
			## remove nat in rc.local
			rclocal = open('/etc/rc.d/rc.local', 'r').readlines()
			rclocalmod = []
			for line in rclocal:
				if not re.search('# OpenKVI Nating :', line) and not re.search('sh /etc/openkvi/openkvi_nat', line):
					rclocalmod.append(line)
			open('/etc/rc.d/rc.local', 'w').writelines(rclocalmod)
			res, err = bash.run('sh /etc/openkvi/openkvi_nat stop')
		
		self.output.info('Trying to stop OpenKVI ...')
		res, err = bash.run('virsh destroy OpenKVI')
		res, err_dump = bash.run('virsh dumpxml OpenKVI >/tmp/OpenKVI.xml')
		self.output.info('Removing OpenKVI definition ...')
		res, err = bash.run('virsh undefine OpenKVI')
		if err:
			self.output.error(re.sub('error: ', '', err))
		if not err_dump:
			self.output.info('Deleting disk images ...')
			XMLDesc = open('/tmp/OpenKVI.xml', 'r').readlines()
			infos = xmltodict.parse(XMLDesc)
			disc_dic = infos['domain']['devices']['disk']
			disc_list = []
			if not isinstance(disc_dic, list):
				disc_list.append(disc_dic)
			else:
				disc_list = disc_dic
			for adisc in disc_list:
				if adisc['@device'] == 'disk':
					todel = adisc['source']['@file']
					if os.path.exists(todel):
						res, err = bash.run('rm -f '+todel)
						if err:
							self.output.error(err)
			
		return 0
	
	def create(self, data):
		try:
			BR_MGNT = self.executePlugin('openkvi.access.bridge', 'get')
			VSWITCH = ""
			if not BR_MGNT or re.search('Error', BR_MGNT):
				self.output.error('Please set OpenKVI access bridge first.')
				return 1
			MODE = self.executePlugin('openkvi.access.mode', 'get')
			if not MODE or MODE not in ['direct', 'nat']:
				self.output.error('Please set OpenKVI access mode to either bridge or nat first.')
				return 1
			MGNT = re.sub('ovsbr_', 'mgnt-', BR_MGNT)
			
			if MODE == 'nat':
				# Create openkvi nat
				default_net = []
				default_net.append('<network>\n')
				default_net.append('<name>default</name>\n')
				default_net.append('<bridge name="openkvibr0" />\n')
				default_net.append('<forward/>\n')
				default_net.append('<ip address="192.168.122.1" netmask="255.255.255.0">\n')
				default_net.append('<dhcp>\n')
				default_net.append('<range start="192.168.122.2" end="192.168.122.2" />\n')
				default_net.append('</dhcp>\n')
				default_net.append('</ip>\n')
				default_net.append('</network>\n')
				open('/tmp/default_network.xml', 'w').writelines(default_net)
			else:
				res, err = bash.run('virsh net-list | tail -n +3')
				for line in res.split('\n'):
					infos = line.split(' ')
					if infos[0]:
						res, err = bash.run('virsh net-info '+infos[0]+' | grep ": *'+BR_MGNT+'$"')
						if re.search('Bridge:', res):
							VSWITCH = infos[0]
				if not VSWITCH:
					self.output.error('You first need to create a Virtual Network that support '+BR_MGNT)
					return 1
			self.output.title('Proceeding with OpenKVI creation, this may take some time ...')
			
			if not re.search("/opt/virtualization/isos/openkvi-iso-build", data):
				data_path = self.inputValidation(data)
				if not data_path:
					return 1
				# mount ISO
				res, err = bash.run('file '+data_path)
				bash.run('mkdir -p /tmp/kvm_cdrom')
				bash.run('umount /tmp/kvm_cdrom')
				
				if ': directory' in res:
					res, err = bash.run('mount --bind '+data_path+' /tmp/kvm_cdrom')
					if err:
						self.output.error('An error occured when binding '+data_path+' to /tmp/kvm_cdrom directory:')
						self.output.error(err)
						return 1
				elif "ISO 9660" in res:
					res, err = bash.run('mount -o loop,ro '+data_path+' /tmp/kvm_cdrom')
					if err:
						self.output.error('An error occured when mounting '+data_path+' to /tmp/kvm_cdrom directory:')
						self.output.error(err)
						return 1
				
				self.output.info(data_path+' mounted.')
				bash.run('rm -rf /opt/virtualization/isos/openkvi-iso-build')
				self.output.info('Copying Install Disc content ...')
				shutil.copytree('/tmp/kvm_cdrom','/opt/virtualization/isos/openkvi-iso-build',symlinks=True)
				shutil.copy2('/tmp/kvm_cdrom/.discinfo', '/opt/virtualization/isos/openkvi-iso-build/')
				shutil.copy2('/tmp/kvm_cdrom/.treeinfo', '/opt/virtualization/isos/openkvi-iso-build/')
				bash.run('umount /tmp/kvm_cdrom')
				
			# Generate MAC address
			res, err = bash.run('openssl rand -hex 6')
			NUM = res[6:]
			MAC = "52:54:00:"+NUM[0:2]+":"+NUM[2:4]+":"+NUM[4:6]
			if os.path.exists('/usr/local/firstboot'):
				os.remove('/usr/local/firstboot/system.startup')
				shutil.copy2('/usr/local/firstboot/system.startup.kvm_openkvi','/usr/local/firstboot/system.startup')
			else:
				os.remove('/usr/local/firstboot/system.startup')
				shutil.copy2('/usr/local/firstboot/system.startup.kvm_openkvi','/usr/local/firstboot/system.startup')
			bash.run('mkdir -p /opt/virtualization/vmdisks/')
			bash.run('rm -f /opt/virtualization/vmdisks/OpenKVI-01.img')
			bash.run('qemu-img create -f qcow2 -o preallocation=metadata /opt/virtualization/vmdisks/OpenKVI-01.img 10G')
			self.output.info('OpenKVI VM disk created.')
			
			self.output.info('Gathering KVM host information ...')
			kickstart = open('/root/anaconda-ks.cfg', 'r').readlines()
			for line in kickstart:
				if re.search('^VERSION=', line):
					VERSION = line.split('=')[1].strip()
				if re.search('^keyboard ', line):
					KEYBOARD = line
					KS_LAYOUT = re.sub('^keyboard', '', line).strip()
				if re.search('^rootpw', line):
					ROOTPWD = line
			
			network_lines = open('/etc/sysconfig/network', 'r').readlines()
			
			KVMNAME = ""
			for line in network_lines:
				if re.search('^HOSTNAME', line):
					KVMNAME = line.split('=')[1].strip()
				
			if not KVMNAME:
				tmpstr, err = bash.run('hostname')
				KVMNAME = tmpstr.strip()
			
			LAYOUT = 'en-us'
			keymaps = os.listdir('/usr/share/qemu-kvm/keymaps/')
			if KS_LAYOUT in keymaps:
				LAYOUT = KS_LAYOUT
			else:
				shorter = KS_LAYOUT.split('-')[0]
				if shorter in keymaps:
					LAYOUT = shorter
			
			ks_openkvi_lines = open("/opt/virtualization/isos/openkvi-iso-build/tools/profiles/openkvi/ks_openkvi.cfg", 'r').readlines()
			final_ks = []
			final_ks.append(ROOTPWD)
			for aline in ks_openkvi_lines:
				str0 = re.sub("##KEYBOARD##", KEYBOARD, aline)
				str1 = re.sub("#AVAHI HOSTS#", "", str0)
				str2 = re.sub("##KVM_HOST##", KVMNAME, str1)
				str3 = re.sub("##NETWORK: ", "", str2)
				final_ks.append(str3)
			
			open("/opt/virtualization/isos/openkvi-iso-build/tools/profiles/openkvi/ks_openkvi.cfg", 'w').writelines(final_ks)
			# <reate SSH keys>
			## Note the double space after -N option for empty passphrase
			root_dsa = '/opt/virtualization/isos/openkvi-iso-build/root-id_dsa'
			tomcat_dsa = '/opt/virtualization/isos/openkvi-iso-build/tomcat-id_dsa'
			bash.run('rm -f '+root_dsa)
			bash.run('rm -f '+tomcat_dsa)
			bash.run('ssh-keygen -q -t dsa -N  -C root@'+KVMNAME+'-OpenKVI -f '+root_dsa)
			shutil.copy2(root_dsa, tomcat_dsa)
			shutil.copy2(root_dsa+".pub", tomcat_dsa+".pub")
			bash.run('mkdir -p /root/.ssh')
			keylines = open(root_dsa+'.pub', 'r').readlines()
			auth_lines = []
			if os.path.exists('/root/.ssh/authorized_keys'):
				for line in open('/root/.ssh/authorized_keys', 'r').readlines():
					if not re.search(' root@'+KVMNAME+'-OpenKVI$', line):
						auth_lines.append(line)
			auth_lines.extend(keylines)
			open('/root/.ssh/authorized_keys', 'w').writelines(auth_lines)
			
			if os.path.exists('/usr/local/firstboot/openkvi.xml'):
				xml_lines = open('/usr/local/firstboot/openkvi.xml', 'r').readlines()
			else:
				xml_lines = open('/usr/local/firstboot/openkvi.xml', 'r').readlines()
			final_xml = []
			for line in xml_lines:
				line = line.replace('##OPENKVI##', 'OpenKVI')
				line = line.replace('##MAC##', MAC)
				line = line.replace('##DOMAIN_TYPE##', 'kvm')
				line = line.replace('##LAYOUT##', LAYOUT)
				line = line.replace('##HOSTNAME##', KVMNAME)
				line = line.replace('##PRIVATE_IP##', '192.168.122.2')
				line = line.replace('##NAT_IP##', '192.168.122.1')
				if MODE == 'direct':
					if re.search('<interface type=.bridge.>', line):
						line = '    <interface type="network">\n'
					elif re.search('<source bridge=.openkvibr0./>', line):
						line = '      <source network="'+VSWITCH+'"/>\n'
				if line:
					final_xml.append(line)
			open('/opt/virtualization/openkvi.xml', 'w').writelines(final_xml)
			
			res, err = bash.run('lscpu | grep "^Virtualization:" | egrep "(VT-x|AMD-V|VIA-VT)"')
			if res:
				TYPE = "kvm"
			else:
				TYPE = "qemu"
			
			self.output.info('Creating VM: check libvirtd status')
			res, err = bash.run('virsh list')
			if err:
				self.output.error(err)
				time.sleep(30)
				self.output.info('Creating VM: check libvirtd status again')
				res, err = bash.run('virsh list')
				if err:
					self.output.error(err)
					return err
				
			if MODE == "nat":
				lines = open("/etc/rc.d/rc.local", "r").readlines()
				to_add = True
				for line in lines:
					if re.search('^sh /etc/openkvi/openkvi_nat', line):
						to_add = False
				if to_add:
					lines.append('# OpenKVI Nating :\n')
					lines.append('sh /etc/openkvi/openkvi_nat restart\n')
				open("/etc/rc.d/rc.local", "w").writelines(lines)
				
				hosts_file = open("/etc/hosts", "r").readlines()
				etchosts = []
				for line in hosts_file:
					if not re.search(' OpenKVI openkvi', line):
						etchosts.append(line)
				etchosts.append("192.168.122.2    OpenKVI openkvi\n")
				open("/etc/hosts", "w").writelines(etchosts)
			
			
			# Start installation	
			create_openkvi = []
			create_openkvi.append('#/bin/sh\n')
			create_openkvi.append('DOMAINTYPE='+TYPE+'\n')
			create_openkvi.append('LAYOUT='+LAYOUT+'\n')
			create_openkvi.append('MGNT='+MGNT+'\n')
			#create_openkvi.append('IP=$(ifconfig | grep -A1 "^'+MGNT+' " | grep inet | sed "s/.*addr://" | sed "s/ .*//")\n')
			create_openkvi.append('IP=$(ip addr show dev '+MGNT+' | grep "inet " | sed -e "s/.*inet //" | sed -e "s/\/.*//")\n')
			create_openkvi.append('HOSTNAME='+KVMNAME+'\n')
			create_openkvi.append('echo "$HOSTNAME=$IP" > /opt/virtualization/isos/openkvi-iso-build/kvm-host\n')
			## <create OpenKVI ISO>
			create_openkvi.append('cd /opt/virtualization/isos/openkvi-iso-build/tools/\n')
			create_openkvi.append('mkdir -p /opt/virtualization/isos/x86_64\n')
			create_openkvi.append('sh iso-tool.sh -f -r -p openkvi -a x86_64 -o CENTOS7 -d ../../x86_64/ 2>&1\n')
			create_openkvi.append('ISONAME=$(ls /opt/virtualization/isos/x86_64/ | grep "CENTOS7.*-KVM" | grep "\.iso$")\n')
			create_openkvi.append('echo $ISONAME\n')
			create_openkvi.append('perl -p -i -e "s/##ISOCENTOS##/$ISONAME/" /opt/virtualization/openkvi.xml\n')
			create_openkvi.append('cd -\n')
			## </create OpenKVI ISO>
			create_openkvi.append('perl -p -i -e "s/.*enable-reflector=.*/enable-reflector=yes/" /etc/avahi/avahi-daemon.conf; service avahi-daemon restart\n')
			if MODE == 'nat':
				create_openkvi.append('virsh net-destroy default 1>/dev/null 2>&1\n')
				create_openkvi.append('virsh net-undefine default 1>/dev/null 2>&1\n')
				create_openkvi.append('virsh net-define /tmp/default_network.xml\n')
				create_openkvi.append('virsh net-autostart default\n')
				create_openkvi.append('virsh net-start default\n')
			
			create_openkvi.append('sh /usr/local/firstboot/system.startup\n')
			create_openkvi.append('virsh destroy OpenKVI 2>&1\n')
			create_openkvi.append('virsh undefine 2>&1\n')
			create_openkvi.append('virsh define /opt/virtualization/openkvi.xml 1>/root/virsh_cmd 2>&1\n')
			create_openkvi.append('virsh autostart OpenKVI\n')
			create_openkvi.append('echo "Proceding with OpenKVI installation ..."\n')
			create_openkvi.append('virsh start OpenKVI\n')
			create_openkvi.append('echo "Started OpenKVI Virtual Machine"\n')
			create_openkvi.append('sh /etc/openkvi/openkvi_nat stop\n')
			create_openkvi.append('sleep 60\n')
			create_openkvi.append('sh /etc/openkvi/openkvi_nat start\n')
			create_openkvi.append('echo "-> You can follow OpenKVI installation with a vnc client at $IP:0" > /etc/issue \n')
			create_openkvi.append('TEST=""\n')
			create_openkvi.append('COUNT=0\n')
			create_openkvi.append('while [ -z $TEST ]; do\n')
			create_openkvi.append('    sleep 30\n')
			create_openkvi.append('    wget 192.168.122.2:8080 2>/tmp/test; rm -f index.html\n')
			create_openkvi.append('    TEST=$(cat /tmp/test | grep "index.html" | grep "saved")\n')
			create_openkvi.append('    COUNT=$((COUNT+1))\n')
			create_openkvi.append('    if [ $COUNT == 60 ]; then\n')
			create_openkvi.append('        TEST="EXIT"\n')
			create_openkvi.append('    fi\n')		
			create_openkvi.append('done\n')
			create_openkvi.append('echo "OpenKVI installation completed." >> /etc/issue \n')
			create_openkvi.append('sleep 60\n')
			create_openkvi.append('sh /usr/local/firstboot/system.startup \n')
			create_openkvi.append('sh /etc/comverse/openkvi_nat restart\n')
			
			open('/root/create_openkvi.sh', 'w').writelines(create_openkvi)
			
			#cmd = 'ifconfig | grep -A1 "^'+MGNT+' " | grep inet | sed "s/.*addr://" | sed "s/ .*//"'
			cmd = 'ip addr show dev '+MGNT+' | grep "inet " | sed -e "s/.*inet //" | sed -e "s/\/.*//"'
			res, err = bash.run(cmd)
			IP = res.strip()
			self.output.info('Creating OpenKVI Virtual Machine ...')
			bash.run('rm -f /root/openkvi.log; touch /root/openkvi.log')
			bash.run('rm -f /root/openkvi-error.log; touch /root/openkvi-error.log')
			bash.background('sh /root/create_openkvi.sh 1>/root/openkvi.log 2>/root/openkvi-error.log')
			time.sleep(10)
			res, err = bash.run('virsh domdisplay OpenKVI')
			screen = '0'
			if res:
				display = res.split(':')
				screen = display[2].strip()
			self.output.title('-> You can follow OpenKVI installation with a vnc client at '+IP+':'+screen)
			time.sleep(20)
			err = open('/root/openkvi-error.log').readlines()
			if len(err) > 0:
				self.output.error('Failed create OpenKVI VM: ')
				self.output.error("\n".join(filter(None, errors)))
				cmd = "ps fax | grep create_openkvi.sh | grep -v grep"
				res, err = bash.run(cmd)
				PID = res.split(' ')[0]
				bash.run('kill -9 '+PID)
				return 1
			
			bash.run('sh /etc/comverse/openkvi_nat restart')
			
			
		except:
			err = str(sys.exc_info()[1])
			self.output.error("Cannot create OpenKVI: "+err)
		return res
	
	def _check(self, *args, **kwargs):
		''' Overwrite _check function, because this is a command plugin
		and should not display anything with _check'''
		return 0
	
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


