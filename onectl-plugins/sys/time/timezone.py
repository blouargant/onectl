#!/usr/bin/python -u
# Name: sys.time.timezone

from includes import pluginClass
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
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: zones
		opt1 = {}
		opt1['name'] = '--zones'
		opt1['metavar'] = 'ZONE'
		opt1['action'] = 'store'
		#opt1['nargs'] = '?'
		opt1['help'] = 'List possible timezones. Use "all" keyword to list all available timezones.'
		dic.append(opt1)


		### OPTION: set
		opt1 = {}
		opt1['name'] = '--set'
		opt1['metavar'] = ''
		opt1['action'] = 'store'
		opt1['nargs'] = '+'
		opt1['help'] = 'Set time zone'
		dic.append(opt1)

		return dic

	def info(self):
		title = "System "+self.PluginName+" configuration"
		msg = "This plugin will help you configure the system's timezone\n"
		msg += "You can list all possible timezones with the following command:\n"
		msg += " > onectl "+self.PluginFqn+" --zones all\n"
		msg += "or search possible timezones in an area:\n"
		msg += " > onectl "+self.PluginFqn+" --zones Europe"
		self.output.help(title, msg)

	def zones(self, area='all'):
		proc = subprocess.Popen(['find','/usr/share/zoneinfo/right'], stdout=subprocess.PIPE)
		retcode = proc.wait()
		lines = []
		if area == "all":
			area = ''

		for aline in proc.stdout:
			if not os.path.isdir(aline):
				#print aline+" is not a directory"
				if area:
					area_reg = re.compile(area, re.IGNORECASE)
					if area_reg.search(aline):
						lines.append(re.sub('.*right/', '', aline).strip())
				else:
					lines.append(re.sub('.*right/', '', aline).strip())

		lines.sort()
		self.output.title("Available timezones:")
		for res in lines:
			self.output.info(res)

	def inputValidation(self, data):
		if len(data) > 1:
			self.output.error('"'+str(data)+'" is not a valid timezone, aborting.')
			return None
		
		if os.path.isfile('/usr/share/zoneinfo/right/'+data[0]) :
				return data
		else:
			self.output.error('"'+data[0]+'" is not a valid timezone, aborting.')
			return None


	def get_active(self):
		zone = ""
		try:
			if os.path.exists("/etc/sysconfig/clock"):
				fzone = open("/etc/sysconfig/clock", 'r')
				zone_lines = fzone.readlines()
				fzone.close()
				for aline in zone_lines:
					if not re.search("^ *#", aline) :
						config_args = aline.split('=')
						if "ZONE" in config_args[0]:
							zone = re.sub('"', '', config_args[1].strip())
							break
			else:
				raise ValueError("Error: Cannot find ZONE definition !")

		except:
			raise

		return zone



	def get(self):
		zone = ""
		try:
			zone = self.get_active()
			self.output.title("Current Timezone:")
			self.output.info(zone)

		except:
			self.printError()
			return 1

		return 0


	def set(self, data):
		try:
			timezone = data[0]
			if os.path.isfile('/usr/share/zoneinfo/right/'+timezone) :
				fzone = open("/etc/sysconfig/clock", 'w')
				zone_lines = fzone.write('ZONE=\"'+timezone+'\"')
				fzone.close()
				if os.path.exists('/etc/localtime'):
					os.remove('/etc/localtime')
				os.symlink('/usr/share/zoneinfo/'+timezone, '/etc/localtime')
				self.output.title('Timezone set to ')
				self.output.info(timezone)
			else:
				self.output.error('"'+timezone+'" is not a valid timezone, aborting.')
				return 1
		except:
			self.printError()
			return 1

		return 0

