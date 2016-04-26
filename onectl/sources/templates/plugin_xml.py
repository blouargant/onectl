#!/usr/bin/python -u
# Name: plugin_general

from includes import pluginClass
from includes import *

import re, os

from includes import xmlparser, fileparser

class PluginControl(pluginClass.Base):

	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''

		plugin = self.PluginFqn
		nargs = '+'

		input_format = 'VALUE '

		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = input_format
		opt['nargs'] = nargs
		opt['action'] = 'store'
		opt['help'] = 'Configure ' + plugin
		dic.append(opt)


		return dic
	
	def info(self):
		''' Information for the plugin shown in info command '''
		title = "Information for " + self.PluginName + ":"
		msg = 'Logging configuration'
		self.output.help(title, msg)

	def inputValidation(self, data):
		''' Validate input data before proceed with the configuration
		'''
		try:
			# Get the file type
			file_type = self.get_xml_field(xmlparser.XML_PLUGIN_FILE_TYPE)
			if not file_type:
				raise ValueError('Field <file_type> in xml is not pressent for plugin '+ plugin)
		
				# remove duplicate values
			input_list = self.validate_input_data(data)

		except:
			self.printError("Validation failure for "+self.PluginName+" : ")
			return None
		return input_list



	def get_active(self):
		try:
			''' Get the current config '''
			
			plugin = self.PluginFqn
			value_list = []
			xml_file = self.get_xml_field(xmlparser.XML_PLUGIN_FILE)
			if not xml_file:
				raise ValueError('Field <file> in xml is not pressent for plugin '+ plugin)
			
			xml_file_type = self.get_xml_field(xmlparser.XML_PLUGIN_FILE_TYPE)
			if not xml_file:
				raise ValueError('Field <file_type> in xml is not pressent for plugin '+ plugin)
			

			#log4j specific
			plugin_start = self.get_xml_field(xmlparser.XML_PLUGIN_DESTINATION)
			tmp = re.sub(plugin_start+'.','',plugin)
			appender, param = tmp.split('.')
			path = xmlparser.LOG4j_XML_PATH.format(appender,param)
			attrib='value'
			
			value = xmlparser.get_xml_elem_value(xml_file, path, attrib)
			#value = xmlparser.get_xml_field_from_xmlfile(xml_file, path)
			if value:
				#value_str = value['@value']
				value_list=[value]
		except:
			self.printError("Getting "+self.PluginName+" : ")
			return None

		return value_list



	def get(self):
		try:
			''' Get the current config '''
			value_list = self.get_active()
			if value_list:
				curr_config_str =  ' '.join(value_list)

			self.output.title("Current " + self.PluginName + " configured:")
			self.output.info(curr_config_str)

		except:
			self.printError("Getting "+self.PluginName+" : ")
			return 1

		return 0


	def set(self, data):
		''' Set new value '''

		try:
			new_value = data[0]
			plugin = self.PluginFqn
			xml_file = self.get_xml_field(xmlparser.XML_PLUGIN_FILE)
			if not xml_file:
				raise ValueError('Field <file> in xml is not pressent for plugin '+ plugin)
			

			# log4j specific
			plugin_start = self.get_xml_field(xmlparser.XML_PLUGIN_DESTINATION)
			tmp = re.sub(plugin_start+'.','',plugin)
			appender, param = tmp.split('.')
			path = xmlparser.LOG4j_XML_PATH.format(appender,param)
			attrib='value'
			
			xmlparser.set_xml_elem_value(xml_file, path, attrib,new_value)

			self.output.title('Configured ' + self.PluginName + '(s):')
			self.output.info(new_value)

		except:
			self.printError("Setting "+self.PluginName+" " + ' '.join(data)+": ")
			return 1
		return 0

	def check(self):
		''' Overwrite the check function.Needed for view diff.Check agains Onboot setup
		\n are removed from result from get function '''
		data_list = self.get_active()
		view_output = ' '.join(data_list)
		self._check(info_get=view_output)


