
#!/usr/bin/python -u
# Name: plugin_general

from includes import pluginClass
from includes import *
import os
import sys
import re
import subprocess
from includes import xmlparser, hash

class PluginControl(pluginClass.Base):
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		plugin = self.PluginFqn
		input_type = self.get_xml_field(xmlparser.XML_INI_KEYTYPE.format(plugin))
		key = self.PluginName
		
		dic = []
		### OPTION: start
		opt = {}
		opt['name'] = '--start'
		opt['metavar'] = ''
		opt['nargs'] = ''
		opt['action'] = 'store_true'
		opt['help'] = 'Start a service'
		dic.append(opt)
		
		### OPTION: stop
		opt = {}
		opt['name'] = '--stop'
		opt['metavar'] = ''
		opt['nargs'] = ''
		opt['action'] = 'store_true'
		opt['help'] = 'Stop a service '
		dic.append(opt)
		
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: restart
		opt = {}
		opt['name'] = '--restart'
		opt['metavar'] = ''
		opt['action'] = 'store_true'
		opt['nargs'] = ''
		opt['help'] = 'Restart a service'
		dic.append(opt)

		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'on|off'
		opt['action'] = 'store'
		#opt['nargs'] = '+'
		opt['help'] = 'Enable/disable the service '
		dic.append(opt)
	
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: rank
		opt = {}
		opt['name'] = '--rank'
		opt['metavar'] = 'START:KILL'
		opt['action'] = 'store'
		#opt['nargs'] = '+'
		opt['help'] = 'Set possition in which the service is started stopped'
		dic.append(opt)

		### OPTION: level
		opt = {}
		opt['name'] = '--level'
		opt['metavar'] = 'RUNLEVEL'
		opt['action'] = 'store'
		#opt['nargs'] = '+'
		opt['help'] = 'Change the level in which the service is started '
		dic.append(opt)

		### OPTION: status
		opt = {}
		opt['name'] = '--status'
		opt['metavar'] = ''
		opt['nargs'] = ''
		opt['action'] = 'store_true'
		opt['help'] = 'Show service status'
		dic.append(opt)


		return dic
	
	def info(self):
		''' Information for the plugin shown in info command '''
		title = "Information for " + self.PluginName + ":"
		plugin = self.PluginFqn
		msg = self.get_xml_field(xmlparser.XML_INFO.format(plugin))
		self.output.help(title, msg)


	def inputValidation(self, data):
		""" Check if the opions passed after the set command are valid
			Valid options are on and off only
		"""
		data = self.validate_input_data(data)
		activate_option = data[0]
		if activate_option != 'on' and activate_option != 'off':
			activate_option == 'off'
			self.output.error("Supported options are on/off")
			return None

		return activate_option

	def get_active(self):
		"""
			Get if service is enabled/disabled
		"""
		try:
			service_name = self.PluginName
			proc = subprocess.Popen(["chkconfig --list " + service_name], stdout=subprocess.PIPE, shell=True)
			(output, err) = proc.communicate()
			# if not OK
			if err is not None:
				raise ValueError("Can not retrieve output of chkconfig --list %s" %service_name)

			if (output.find('3:on') >= 0) or (output.find('3:on') >= 0) or (output.find('3:on') >= 0):
				enabled = 'on'
			else:
				enabled = 'off'


		except:
			raise
		return enabled



	def get(self):
		"""
			Get if service is enabled/disabled
		"""
		try:
			enabled = self.get_active()

			self.output.title(service_name + " service is:")
			self.output.info(enabled)

		except:
			err = str(sys.exc_info()[1])
			self.output.error("Error: %s" % err)
			return 1

		return 0

	def set(self, data):
		""" Enable disable ntp service
		    on for enable / off for disable
		"""
		try:
			data = self.validate_input_data(data)
			activate_option = data[0]
			if activate_option == 'on':
				activate = True
			elif activate_option == 'off':
				activate = False
			else:
				self.output.error("Supported options are on/off")
				return 1

			# service ntpd start/stop) and also activate/deactivate it at startup:
			# activate it: chkconfig --add ntpd then chkconfig --level 345 ntpd on
			# deactivate it: chkconfig --level 345 ntpd off
			service_name = self.PluginName
			if activate is True:
				res = os.system('chkconfig --del ' + service_name)
				if res != 0:
					self.output.error("Service NTP:chkconfig --del %s failed" %service_name)
					return 1

				res = os.system('chkconfig --add ' + service_name)
				if res != 0:
					self.output.error("Service NTP:chkconfig --add %s failed" %service_name)
					return 1
			else:
				res = os.system('chkconfig --del ' + service_name)
				if res != 0:
					self.output.error("Service NTP:chkconfig --del %s failed" %service_name)
					return 1


		except:
			err = str(sys.exc_info()[1])
			self.log.error("setting " + self.PluginName + " " + str(data) + ": " + err)
			self.output.error(err)
			return 1

		return 0
	


	def check(self):
		''' Overwrite the check function.Needed for view diff.Check agains Onboot setup
		\n are removed from result from get function '''
		self.output.disable()
		self.get()
		view_output = ''
		get_result = self.messages["info"]
		if get_result:
			# get command returns servers separated by \n.Replace \n with a space
			view_output = re.sub('\n', ' ', get_result[0])
			# remove the ending space
			view_output = re.sub(re.escape(' ') + '$', '', view_output)
		self.output.clear_messages()
		self.output.enable()
		self._check(info_get=view_output)


	def start(self):
		
		service_name = self.PluginName
		res = os.system('service %s start' %service_name)
		if res != 0:
			self.output.error("Service %s did not start" %service_name)
			return 1

		self.output.info("Service %s started" %service_name)

		return 0

	def stop(self):
		service_name = self.PluginName
		res = os.system('service %s stop' %service_name)
		if res != 0:
			self.output.error("Service %s stop failed" %service_name)
			return 1


	def restart(self):
		service_name = self.PluginName
		res = os.system('service %s restart' %service_name)
		if res != 0:
			self.output.error("Service %s restart failed" %service_name)
			return 1

	def change_chkconfig(self,  inLevel, inStartLevel, inKillLevel):
		try:
			service_name = self.PluginName
			file_name = os.path.join('/etc/init.d/', service_name)
			file_lines = open(file_name, 'r').readlines()
			output_file = []
			for line in file_lines:
				if re.search('chkconfig:', line):
					split_arr = line.split(':',1)
					if len(split_arr)>1:

						value_arr = (split_arr[1].strip()).split(' ')
						if len(value_arr) == 3:
							levels = value_arr[0]
							start = value_arr[1]
							stop = value_arr[2]
					if inLevel:
						levels = inLevel
					if inStartLevel:
						start = inStartLevel
					if inKillLevel:
						stop = inKillLevel
					line = '# chkconfig: %s %s %s \n' %(levels, start, stop)

				output_file.append(line)

			# write the new config
			open(file_name, 'w').writelines(output_file)
		except:
			pass
		

	def rank(self, data):
		try:
			values = self.validate_input_data(data)[0]
			service_name = self.PluginName
			file_name = os.path.join('/etc/init.d/', service_name)
		
			if not re.search(r"^\d+:\d+$", values):
				raise ValueError('Input rank should be in this format START:KILL. Entered %s' %values)
		
			entry = values.split(':', 1)
			inStartLevel = entry[0]
			inKillLevel  = entry[1]
			#inStartLevel = entry[entry.index('[')+1:entry.index(':')]
			#inKillLevel = entry[entry.index(':')+1:entry.index(']')]
			if not re.match("^-?\d*\.{0,1}\d+$", inStartLevel):
				raise ValueError('Input rank %s should be digits only' %entry)
		
			if not re.match("^-?\d*\.{0,1}\d+$", inStartLevel):
				 raise ValueError('Input rank %s should be digits only' %entry)

			self.change_chkconfig( None, inStartLevel, inKillLevel)

		except:
			self.printError("Setting rank "+self.PluginName+" : ")


		

	def level(self, data):
		try:
			values = self.validate_input_data(data)
			levels = values[0]
			service_name = self.PluginName
			self.change_chkconfig( levels, None, None)
			#res = os.system('chkconfig --level %s %s on' %(level, service_name))
			#if res != 0:
			#	self.output.error("Service %s:chkconfig %s on failed" %(service_name, service_name))
			#	return 1
		except:
			self.printError("Setting level "+self.PluginName+" : ")

	def status(self):
		service_name = self.PluginName

		proc = subprocess.Popen(["service %s status" %service_name], stdout=subprocess.PIPE, shell=True)
		(output, err) = proc.communicate()
		# if not OK
		if err is not None:
			self.output.error("Can not retrieve service %s status output" %service_name)
			return 1

		self.output.info(output)

		proc = subprocess.Popen(["chkconfig --list %s" %service_name], stdout=subprocess.PIPE, shell=True)
		(output, err) = proc.communicate()
		# if not OK
		if err is not None:
			self.output.error("Can not retrieve chkconfig --list %s output" %service_name)
			return 1

		self.output.info(output)

		return 0


