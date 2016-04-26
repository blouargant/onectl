#!/usr/bin/python -u
# Name:  sys.time.ntp.service

from includes import pluginClass
from includes import *
import os
import sys
import subprocess

class PluginControl(pluginClass.Base):

	# This plugin handles npt service configuration
	def setOptions(self):
		""" Create additional argument parser options
			specific to the plugin
		"""

		# onectl sys.time.ntp.service --set on/off
		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = 'on|off'
		# opt['choices'] = ['on','off']
		opt['action'] = 'store'
		opt['help'] = 'Enable/disable NTP service'
		dic.append(opt)
		
		### OPTION: status
		opt1 = {}
		opt1['name'] = '--status'
		opt1['metavar'] = ''
		opt1['action'] = 'store_true'
		opt1['nargs'] = ''
		opt1['help'] = 'Show status of NTP service'
		dic.append(opt1)

		return dic

	def info(self):
		title = "System NTP "+self.PluginName+" configuration"
		msg = "This plugin helps to start/stop  NTP service\n"
		msg += "Current NTP service state can be retrieved by the following command:\n"
		msg += " > onectl "+self.PluginFqn+" --view [actual|saved|diff]\n"
		msg += "NTP service can be enabled/disabled with the following commands:\n"
		msg += " > onectl "+self.PluginFqn+" --set [on|off]\n"
		msg += "                             e.g.:onectl sys.time.ntp.servers --set on\n"
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
			Get if ntp is enabled/disabled
		"""
		try:
			proc = subprocess.Popen(["chkconfig --list ntpd"], stdout=subprocess.PIPE, shell=True)
			(output, err) = proc.communicate()
			# if not OK
			if err is not None:
				raise ValueError("Can not retrieve chkconfig --list ntpd output")

			if (output.find('3:on') >= 0) or (output.find('3:on') >= 0) or (output.find('3:on') >= 0):
				enabled = 'on'
			else:
				enabled = 'off'

		except:
			raise
		return enabled



	def get(self):
		"""
			Get if ntp is enabled/disabled
		"""
		try:

			enabled = self.get_active()

			self.output.title("NTP service is:")
			self.output.info(enabled)

		except:
			self.printError()
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

			if activate is True:
				res = os.system('service ntpd start')
				if res != 0:
					self.output.error("Service NTP did not start")
					return 1

				self.output.info("Service ntpd started")
				res = os.system('chkconfig --add ntpd')
				if res != 0:
					self.output.error("Service NTP:chkconfig --add ntpd failed")
					return 1

				res = os.system('chkconfig --level 345 ntpd on')
				if res != 0:
					self.output.error("Service NTP:chkconfig ntpd on failed")
					return 1

			else:
				res = os.system('service ntpd stop')
				if res != 0:
					self.output.error("Service NTP stop failed")
					return 1

				self.output.info("Service ntpd stopped")
				res = os.system('chkconfig --level 345 ntpd off')
				if res != 0:
					self.output.error("Service NTP:chkconfig ntpd off failed")
					return 1

		except:
			self.printError("setting " + self.PluginName + " " + str(data) +": ")
			return 1

		return 0
	
	def status(self):
		"""
			Get if ntp is enabled/disabled
		"""
		try:
			proc = subprocess.Popen(["chkconfig --list ntpd"], stdout=subprocess.PIPE, shell=True)
			(output, err) = proc.communicate()
			# if not OK
			if err is not None:
				self.output.error("Can not retrieve chkconfig --list ntpd output")
				return 1

			if (output.find('3:on') >= 0) or (output.find('3:on') >= 0) or (output.find('3:on') >= 0):
				enabled = 'enabled'
			else:
				enabled = 'disabled'

			self.output.info("NTP service is: "+ enabled)

			#if service is disabled do not show more information
			if enabled is 'disabled':
				return 0

			#ntpstat
			proc = subprocess.Popen(["ntpstat"], stdout=subprocess.PIPE, shell=True)
			(output, err) = proc.communicate()
			# if not OK
			if err is not None:
				self.output.error("Can not retrieve ntpstat")
				return 1

			self.output.info(output)
		except:
			self.printError()
			return 1

		return 0


