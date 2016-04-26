#!/usr/bin/python -u

from includes import pluginClass
from includes import regexp
from includes import host
import os, errno
import sys
import re
import time
import socket
import paramiko

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		dic = []
		
		### OPTION: exchange
		opt0 = {}
		#opt0['name'] = '--exchange'
		#opt0['action'] = 'store_true'
		#opt0['help'] = 'Exchange ssh keys'
		#dic.append(opt0)
		
		opt0['name'] = '--exchange'
		opt0['metavar'] = 'PASS'
		opt0['action'] = 'store'
		opt0['nargs'] = '?'
		opt0['help'] = 'Exchange ssh keys'
		dic.append(opt0)
		

		### OPTION: download
		opt1 = {}
		opt1['name'] = '--download'
		opt1['metavar'] = 'PASS'
		opt1['action'] = 'store'
		opt1['nargs'] = '?'
		opt1['help'] = 'Exchange ssh keys'
		dic.append(opt1)
		
		### OPTION: upload
		opt2 = {}
		opt2['name'] = '--upload'
		opt2['metavar'] = 'PASS'
		opt2['action'] = 'store'
		opt2['nargs'] = '?'
		opt2['help'] = 'Exchange ssh keys'
		dic.append(opt2)
		
		### OPTION: disable
		opt3 = {}
		opt3['name'] = '--disable'
		opt3['metavar'] = 'PASS'
		opt3['action'] = 'store'
		opt3['nargs'] = '?'
		opt3['help'] = 'Disable the ssh key.'
		dic.append(opt3)
		
		### NO OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = ''
		opt['action'] = ''
		opt['nargs'] = ''
		opt['help'] = ''
		dic.append(opt)
	
		### NO OPTION: view
		opt = {}
		opt['name'] = '--view'
		opt['metavar'] = ''
		opt['action'] = ''
		opt['nargs'] = ''
		opt['help'] = ''
		dic.append(opt)
	
		return dic
	
	def info(self):
		''' MANDATORY !'''
		title = "SSH configuration.\n"
		msg =  "--exchange [PASWORD] : Exchange DSA keys between the host and local machine. \n"
		msg += "--download [PASWORD] : Get DSA key from the host. \n"
		msg += "--upload  [PASWORD]  : Send DSA key to the host. \n"
		msg += "--disable [PASWORD]  : Remove the ssh keys exchanged from both machines\n"
		msg += "As an optional argument password can be specified in the form PASWORD.\n"
		self.output.help(title, msg)
	
	def inputValidation(self, data=None):
		try:
			if not data:
				return data
			input_list = list(set(data))
			input_list = sorted(input_list)
			plugin = self.PluginFqn
			
			password = host._get_password(data)
			pattern=re.compile(regexp.PASSWORD, re.VERBOSE | re.IGNORECASE)
			if  pattern.match(password) is None:
				raise ValueError('Invalid password %s' %password)
		except:
			self.printError("Validation failure for "+self.PluginName+" : ")
			return None
		
		self.output.debug("Plugin: %s Data is OK" %plugin)
		return data
	

	def get_active(self):
		try:
			''' Get configured configuration  '''
			hostkeys = paramiko.HostKeys()
			hostkeys.load(os.path.expanduser('~/.ssh/known_hosts'))
			hostname = self._get_hostname(self.PluginFqn)
			lowhostname = hostname.lower()
			if hostname in hostkeys or lowhostname in hostkeys:
				return True
			else:
				return False
		except:
			raise
		return None
	
	def get(self):
		try:
			''' Get info '''
			bTrusted = self.get_active()
			hostname = self._get_hostname(self.PluginFqn)
			if hostname != "all":
				if bTrusted:
					self.output.info("%s is known host" %hostname)
				else:
					self.output.info("%s is unknown host" %hostname)
		
		except:
			self.printError("Get "+self.PluginName+" : ")
			return 1
		
		return 0
	
	def check(self):
		return 0
	
	def _get_hostname(self, plugin):
		''' get the hostname from the plugin '''
		# neighbors.conf.hosta.ssh
		hostname = re.sub('.*conf.', '', re.sub('.ssh$', '', plugin))
		return hostname
		
	def remote_file_exists(self, sftp, path):
		"""os.path.exists for paramiko's SCP object """
		try:
			sftp.stat(path)
		except IOError, e:
			if e.errno == errno.ENOENT:
				return False
			raise
		else:
			return True
		
	def download_key(self, host, username, ssh_client):
		try:
			# Check/Generate nodemanger DSA key
			dsa_path = os.path.expanduser('~/.ssh/id_dsa')
			dsa_pub_key_path = os.path.expanduser('~/.ssh/id_dsa.pub')
			authorized_keys_path = os.path.expanduser('~/.ssh/authorized_keys')
		
			# generate DSA key on remote host if it does not exist
			sftp_client = ssh_client.open_sftp()
			if not self.remote_file_exists(sftp_client, dsa_pub_key_path):
				stdin, stdout, stderr = ssh_client.exec_command('ssh-keygen -q -t dsa -N "" -f %s' %dsa_path)
				time.sleep(1)
			sftp_client.close()
			# get the key
			stdin, stdout, stderr = ssh_client.exec_command('cat %s' %dsa_pub_key_path)
			key = stdout.read()
				
			if key:
				# remove previous entries in authories_keys
				if os.path.exists(authorized_keys_path):
					#remotehostsname = ssh_client.get_transport().sock.getpeername()
					_, stdout, _ = ssh_client.exec_command('hostname')
					remotehostsname = stdout.read()
					remotehostsname = remotehostsname.strip()
					if not remotehostsname:
						remotehostsname = host
					cmd = 'perl -p -i -e "s/.* %s\@%s\\n$//" %s' %(username, remotehostsname, authorized_keys_path)
					os.system(cmd)
				if not os.path.exists('~/.ssh/'):
					os.system('mkdir -p ~/.ssh/')
				# copy the key
				os.system('echo "%s" >> %s' % (key, authorized_keys_path))
				os.system('chmod 700 ~/.ssh/')
				os.system('chmod 640 %s' %authorized_keys_path)

			#Automaticaly add remote host to known_hosts: 
			localhostname = socket.gethostname()
			ip = ssh_client.get_transport().sock.getsockname()
			ip = ip[0]
			cmd = 'ssh -o StrictHostKeyChecking=no %s@%s "exit" ' %(username, ip)
			stdin, stdout, stderr = ssh_client.exec_command(cmd)
			stdin, stdout, stderr = ssh_client.exec_command("onectl --show neighbors.names")
			remote_defined_hosts = stdout.read().split(' ')
			if localhostname not in remote_defined_hosts:
				sock = ssh_client.get_transport().sock
				local_ip = sock.getsockname()[0]
				stdin, stdout, stderr = ssh_client.exec_command("onectl neighbors.names --add %s" % localhostname)
				err = stderr.read()
				if not err:
					cmd = 'onectl neighbors.conf.'+localhostname+'.ip --set '+local_ip
					stdin, stdout, stderr = ssh_client.exec_command(cmd)
					self.output.title('Remotely added %s to neighbors names' % localhostname)
		except:
			raise
		
	def upload_key(self, host, username, ssh_client):
		try:
			# Check/Generate nodemanger DSA key
			dsa_path = os.path.expanduser('~/.ssh/id_dsa')
			dsa_pub_key_path = os.path.expanduser('~/.ssh/id_dsa.pub')
			authorized_keys_path = os.path.expanduser('~/.ssh/authorized_keys')
			localhostname = socket.gethostname()
			
			# Clien DSA key if it does not exist
			if not os.path.exists(dsa_path) or not os.path.exists(dsa_pub_key_path):
				os.system('ssh-keygen -q -t dsa -N "" -f %s' %dsa_path)
			
			# get the key
			key = open(dsa_pub_key_path).read()
			
			stdin, stdout, stderr = ssh_client.exec_command('mkdir -p ~/.ssh/')
			# remove previous keys on remote host
			cmd = 'perl -p -i -e "s/.* %s\@%s\\n$//" %s' %(username, localhostname, authorized_keys_path)
			stdin, stdout, stderr = ssh_client.exec_command(cmd)
			stdin, stdout, stderr = ssh_client.exec_command('echo "%s" >> %s' % (key, authorized_keys_path))
			stdin, stdout, stderr = ssh_client.exec_command('chmod 700 ~/.ssh/')
			stdin, stdout, stderr = ssh_client.exec_command('chmod 640 %s' % authorized_keys_path)
			#client.close()
			#Automaticaly add remote host to root's known_hosts:
			cmd = 'ssh -o StrictHostKeyChecking=no %s@%s "exit" ' %(username, host)
			os.system(cmd)
		except:
			raise
			
	def remove_key_remote(self, host, username, ssh_client):
		try:
			authorized_keys_path = os.path.expanduser('~/.ssh/authorized_keys')
			known_hosts_path = os.path.expanduser('~/.ssh/known_hosts')
			localhostname = socket.gethostname()
			privatekeyfile = os.path.expanduser('~/.ssh/id_dsa.pub')
			
			cmd = 'perl -p -i -e "s/.* %s\@%s\\n$//" %s' %(username, localhostname, authorized_keys_path)
			stdin, stdout, stderr = ssh_client.exec_command(cmd)
			
			if os.path.exists(known_hosts_path):
				ip = None
				ip_plugin = "neighbors.conf." + host + ".ip"
				msg = self.executePlugin(ip_plugin, "get")
				if not re.search('Error', msg):
					ip = msg
				cmd = 'perl -p -i -e "s/%s,.* ssh-rsa .*\\n$//" %s' %(host, known_hosts_path)
				os.system(cmd)
				cmd = 'perl -p -i -e "s/%s ssh-rsa .*\\n$//" %s' %(host, known_hosts_path)
				os.system(cmd)
				if ip:
					cmd = 'perl -p -i -e "s/.*,%s ssh-rsa .*\\n$//" %s' %(ip, known_hosts_path)
					os.system(cmd)
					cmd = 'perl -p -i -e "s/%s ssh-rsa .*\\n$//" %s'  %(ip, known_hosts_path)
					os.system(cmd)
		except:
			raise
		
	def remove_key_local(self, host, username, ssh_client):
		try:
			authorized_keys_path = os.path.expanduser('~/.ssh/authorized_keys')
			known_hosts_path = os.path.expanduser('~/.ssh/known_hosts')
			localhostname = socket.gethostname()
			privatekeyfile = os.path.expanduser('~/.ssh/id_dsa.pub')
		
			if os.path.exists(authorized_keys_path):
				cmd = 'perl -p -i -e "s/.* %s\@%s\\n$//" %s' %(username, host, authorized_keys_path)
				os.system(cmd)
			
			#localhostname = localhostname.lower()
			cmd = 'perl -p -i -e "s/%s,.* ssh-rsa .*\\n$//" %s' %(localhostname, known_hosts_path)
			stdin, stdout, stderr = ssh_client.exec_command(cmd)
			cmd = 'perl -p -i -e "s/%s ssh-rsa .*\\n$//" %s' %(localhostname, known_hosts_path)
			stdin, stdout, stderr = ssh_client.exec_command(cmd)
			ip = ssh_client.get_transport().sock.getsockname()
			ip = ip[0]
			if ip:
				cmd = 'perl -p -i -e "s/.*,%s ssh-rsa .*\\n$//" %s' %(ip, known_hosts_path)
				stdin, stdout, stderr = ssh_client.exec_command(cmd)
				cmd = 'perl -p -i -e "s/%s ssh-rsa .*\\n$//" %s'  %(ip, known_hosts_path)
				stdin, stdout, stderr = ssh_client.exec_command(cmd)
		except:
			raise
		
	def exchange(self, data=None):
		''' exchange key with host '''
		try:
			password = host._get_password(data)
			hostname = self._get_hostname(self.PluginFqn)
			username = host.getlogin()
			hosts = []
			if hostname == "all":
				names = self.executePlugin('neighbors.names', 'get')
				hosts = names.split(' ')
				if 'all' in hosts:
					hosts.remove('all')
			else:
				hosts.append(hostname)
				
			for hostname in hosts:
				ssh_client = host.remote_host_connect(hostname, username, password)
				self.upload_key(hostname, username, ssh_client)
				self.download_key(hostname, username, ssh_client)
				ssh_client.close()
		except:
			self.printError("Exchanging "+self.PluginName+" : ")
			return 1
		
		if len(hosts) == 1:
			self.output.title('SSH keys exchanged correctly with %s' % hostname)
		else:
			self.output.title('SSH keys exchanged correctly with %s' % hosts)
		return 0
	
	def download(self, data=None):
		''' exchange key with host '''
		try:
			password = host._get_password(data)
			hostname = self._get_hostname(self.PluginFqn)
			username = host.getlogin()
			hosts = []
			if hostname == "all":
				names = self.executePlugin('neighbors.names', 'get')
				hosts = names.split(' ')
				if 'all' in hosts:
					hosts.remove('all')
			else:
				hosts.append(hostname)
				
			for hostname in hosts:
				ssh_client = host.remote_host_connect(hostname, username, password)
				self.download_key(hostname, username, ssh_client)
				ssh_client.close()
		except:
			self.printError("Exchanging "+self.PluginName+" : ")
			return 1
		
		if len(hosts) == 1:
			self.output.title('SSH keys downloaded correctly from %s' % hostname)
		else:
			self.output.title('SSH keys downloaded correctly from %s' % hosts)
		return 0
	
	def upload(self, data=None):
		''' exchange key with local host '''
		try:
			password = host._get_password(data)
			hostname = self._get_hostname(self.PluginFqn)
			username = host.getlogin()
			hosts = []
			if hostname == "all":
				names = self.executePlugin('neighbors.names', 'get')
				hosts = names.split(' ')
				if 'all' in hosts:
					hosts.remove('all')
			else:
				hosts.append(hostname)
				
			for hostname in hosts:
				ssh_client = host.remote_host_connect(hostname, username, password)
				self.upload_key(hostname, username, ssh_client)
				ssh_client.close()
		except:
			self.printError("Exchanging "+self.PluginName+" : ")
			return 1

		if len(hosts) == 1:
			self.output.title('SSH keys uploaded correctly to %s' % hostname)
		else:
			self.output.title('SSH keys uploaded correctly to %s' % hosts)
		return 0
		
	def disable(self, data = None):
		''' remove exchanges keys '''
		try:
			password = host._get_password(data)
			hostname = self._get_hostname(self.PluginFqn)
			username = host.getlogin()
			ssh_client = host.remote_host_connect(hostname, username, password)
				
			self.remove_key_remote(hostname, username, ssh_client)
			self.remove_key_local(hostname, username, ssh_client)
			ssh_client.close()
		except:
			self.printError("Disabling "+self.PluginName+" : ")
			return 1
		
		self.output.title('SSH settings for neighbour removed.')
		return 0
		
	def set(self, data):
		''' Nothing to do when --set [ARGS] is called '''
		return 0
		
	

