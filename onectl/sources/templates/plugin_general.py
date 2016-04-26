#!/usr/bin/python -u
# Name: plugin_general

from includes import pluginClass
import re, os

from includes import xmlparser, fileparser

class PluginControl(pluginClass.Base):

	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''

		plugin = self.PluginFqn
		input_type = self.get_xml_field((xmlparser.XML_INI_KEYTYPE).format(plugin))
		input_separator = self.get_xml_field((xmlparser.XML_INI_KEY_SEPARATOR).format(plugin))
		input_format = self.get_xml_field((xmlparser.XML_INI_KEY_FORMAT).format(plugin))
		key = self.PluginName
		if input_type:
			input_type = input_type.lower()
		else:
			input_type = 'list'

		nargs = ''
		bIsList = False
		if (input_type.lower() == 'list') or (input_type.lower() == 'integer-list'):
			bIsList = True
			nargs = '+'

		action = 'store'
		if not input_format:
			if not bIsList:
				input_format = 'VALUE VALUE ..'
			else:
				input_format = 'VALUE '

		dic = []
		### OPTION: set
		opt = {}
		opt['name'] = '--set'
		opt['metavar'] = input_format
		opt['nargs'] = nargs
		opt['action'] = 'store'
		opt['help'] = 'Configure ' + key
		dic.append(opt)

		### OPTION: disable
		opt = {}
		opt['name'] = '--disable'
		opt['metavar'] = ''
		opt['nargs'] = ''
		opt['action'] = 'store_true'
		opt['help'] = 'Disable ' + key
		dic.append(opt)


		if bIsList:
			### Additional options, the line below is mandatory for bash autocompletion
			### OPTION: add
			opt = {}
			opt['name'] = '--add'
			opt['metavar'] = input_format
			opt['action'] = action
			opt['nargs'] = nargs
			opt['help'] = 'Add '+ key + ' list of ' + key + 's to the startup config.'
			dic.append(opt)

			### Additional options, the line below is mandatory for bash autocompletion
			### OPTION: remove
			opt = {}
			opt['name'] = '--remove'
			opt['metavar'] = input_format
			opt['action'] = action
			opt['nargs'] = nargs
			opt['help'] = 'Remove ' + key
			dic.append(opt)

		return dic
	
	def info(self):
		''' Information for the plugin shown in info command '''
		title = "Information for " + self.PluginName + ":"
		plugin = self.PluginFqn
		msg = self.get_xml_field(xmlparser.XML_INFO.format(plugin))
		if msg:
			self.output.help(title, msg)

	def inputValidation(self, data):
		''' Validate input data before proceed with the configuration
		'''

		if data == pluginClass.DISABLE_PLUGIN:
			return data

		# Get the file type
		file_type = self.get_xml_field(xmlparser.XML_PLUGIN_FILE_TYPE)
		if not file_type:
			raise ValueError('Field <file_type> in xml is not pressent for plugin '+ plugin)
		
		if file_type == 'ini':
			# remove duplicate values
			input_list = self.validate_input_data(data)
		else:
			input_list = self.validate_bulk_data(data)

		regex = None
		min_check = None
		max_check = None
		plugin = self.PluginFqn

		try:
			input_type = self.get_xml_field(xmlparser.XML_INI_KEYTYPE.format(plugin))
			if not input_type:
				input_type = 'list'
			# In case the input type is not a list input value should be only one
			if (input_type.lower() != 'list') and (input_type.lower() != 'integer-list'):
				if len(input_list)>1:
					raise ValueError('Only one value should be configured' )

			bIsInteger = False
			if (input_type.lower() == 'integer') or (input_type.lower() == 'integer-list'):
				bIsInteger = True
				min_check = self.get_xml_field(xmlparser.XML_INI_VAL_MIN.format(plugin))
				if min_check is not None:
					if not re.match("^-?\d*\.{0,1}\d+$", min_check):
						 raise ValueError('Please enter a digit for validation/min in xml')
					else:
						min_check = long(min_check)
				max_check = self.get_xml_field(xmlparser.XML_INI_VAL_MAX.format(plugin))
				if max_check is not None:
					if not re.match("^-?\d*\.{0,1}\d+$", max_check):
						raise ValueError('Please enter a digit for validation/min in xml')
					else:
						max_check = long(max_check)
			else:
				regex = self.get_xml_field(xmlparser.XML_INI_REGEXP.format(plugin))
		
			for entry in input_list:
				if regex:
					pattern=re.compile(regex, re.VERBOSE)
					if pattern.match(entry) is None:
						raise ValueError('Value %s is not valid input.Please check --info command for more information' %entry )

				if bIsInteger:
					# if input is from type [min-max] range
					if re.search(r"^\[\d+-\d+\]$", entry):
						min_range = entry[entry.index('[')+1:entry.index('-')]
						max_range = entry[entry.index('-')+1:entry.index(']')]
						if not re.match("^-?\d*\.{0,1}\d+$", min_range):
							raise ValueError('Input data range %s should be digits only' %entry)
						else:
							min_range = long(min_range)
						if not re.match("^-?\d*\.{0,1}\d+$", max_range):
							raise ValueError('Input data range %s should be digits only' %entry)
						else:
							max_range = long(max_range)
						if min_check is not None:
							if min_range < min_check:
								raise ValueError('Input min value in range should be bigger than or equal to %d: entered %s ' %(min_check, entry) )

						if max_check is not None:
							if max_range > max_check:
								raise ValueError('Input max value in range should be less than or equal to %d: entered %s ' %(max_check, entry) )
					else:
						# if not a digit print error
						if not re.match("^-?\d*\.{0,1}\d+$", entry):
							raise ValueError('Input data %s should be digits only' %entry)
						else:
							digit = long(entry)
						if min_check is not None:
							if digit < min_check:
								raise ValueError('Input value should be bigger than or equal to %d: entered %d ' %(min_check, digit) )
						if max_check is not None:
							if digit > max_check:
								raise ValueError('Input value should be less than or equal to %d: entered %d ' %(max_check,digit) )
		except:
			self.printError("Validation failure for "+self.PluginName+" : ")
			return None
		return input_list



	def get_active(self):
		try:
			''' Get the current config '''
			
			plugin = self.PluginFqn
			
			config_file = self.get_xml_field(xmlparser.XML_PLUGIN_FILE)
			if not config_file:
				raise ValueError('Field <file> in xml is not pressent for plugin '+ plugin)
			
			section = self.get_xml_field(xmlparser.XML_INI_SECTION.format(plugin))
			key = None
			file_type = self.get_xml_field(xmlparser.XML_PLUGIN_FILE_TYPE)
			if not file_type:
				raise ValueError('Field <file_type> in xml is not pressent for plugin '+ plugin)

			data_separator = self.get_xml_field(xmlparser.XML_INI_KEY_SEPARATOR.format(plugin))
			if not data_separator:
				data_separator = ' ' 

			if file_type == 'ini':
				key_separator = '='
				key = self.get_xml_field(xmlparser.XML_INI_KEY.format(plugin))
				if not key:
					raise ValueError('Field <key> in xml is not pressent for plugin '+ plugin)
		

			elif file_type == 'cache':
				key_separator = ' '
			else:
				raise ValueError("Not supported file format.Only inii and cache file format are supported")

			value_list = fileparser.get_key(config_file, section, key, key_separator, data_separator)
		

		except:
			self.printError("Getting "+self.PluginName+" : ")
			return None

		return value_list



	def get(self):
		try:
			''' Get the current config '''
			curr_config_str = ''
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
		
		plugin = self.PluginFqn

		try:
			# Get the file
			config_file = self.get_xml_field(xmlparser.XML_PLUGIN_FILE)
			if not config_file:
				raise ValueError('Field <file> in xml is not pressent for plugin '+ plugin)
			
			# Get the file type
			file_type = self.get_xml_field(xmlparser.XML_PLUGIN_FILE_TYPE)
			if not file_type:
				raise ValueError('Field <file_type> in xml is not pressent for plugin '+ plugin)

			# Get the section
			section = self.get_xml_field(xmlparser.XML_INI_SECTION.format(plugin))
			key = None
			data_separator = self.get_xml_field(xmlparser.XML_INI_KEY_SEPARATOR.format(plugin))


			if file_type == 'cache':
				data_list = self.validate_bulk_data(data)
			else:
				data_list = self.validate_input_data(data)

			if file_type=='cache':
				key_separator = ' '
				new_val_conf = fileparser.set_bulk(config_file, section,  key_separator, data_list, data_separator)
			elif file_type=='ini':
				key = self.get_xml_field(xmlparser.XML_INI_KEY.format(plugin))
				if not key:
					raise ValueError('Field <key> in xml is not pressent for plugin '+ plugin)
				key_separator = '='
				new_val_conf = fileparser.set_key(config_file, section, key, key_separator, data_list, data_separator)
				if self.live_update:
					live_command = self.get_xml_field(xmlparser.XML_INI_LIVE.format(plugin))
					if live_command:
						for new_value in data_list:
							os.system(live_command + ' %s' % new_value)

			else:
				raise ValueError("Not supported file format.Only ini file format is supported")


			self.output.title('Configured ' + self.PluginName + '(s):')
			self.output.info(new_val_conf)

		except:
			self.printError("Setting "+self.PluginName+" " + ' '.join(data_list)+": ")
			return 1
		return 0

	def check(self):
		''' Overwrite the check function.Needed for view diff.Check agains Onboot setup
		\n are removed from result from get function '''
		data_list = self.get_active()
		view_output = ' '.join(data_list)
		self._check(info_get=view_output)

	def add(self, data=''):
		''' Add new values 
			Return 0 for OK and 1 for error
		'''

		try:
			file_type = self.get_xml_field(xmlparser.XML_PLUGIN_FILE_TYPE)
			if not file_type:
				raise ValueError('Field <file_type> in xml is not pressent for plugin '+ plugin)
			
			if file_type == 'cache':
				input_data = self.validate_bulk_data(data)
			else:
				input_data = self.validate_input_data(data)

			toadd = input_data
			plugin = self.PluginFqn

			# Get the current config
			curr_config = self.get_current_config(self.PluginFqn)
			#if the plugin is called for the first time no info saves load the current config
			is_db_config = True
			if not curr_config:
				is_db_config = False
				# gets the corrent config as a string
				curr_config = self.get_active()

			if file_type == 'ini':
				# input is values only
				for item in list(toadd):
					# if item is already in the current config remove it from list for adding
					if item in curr_config:
						toadd = list(filter(lambda curr: curr!= item, toadd))
			else:
				# input is key=value
				for value in list(curr_config):
					for item in toadd:
						if not re.search('=', item):
							continue
						keys = item.split('=',1)
						key = keys[0]
						if value.startswith(key+'=') and value in curr_config:
							curr_config.remove(value)


			# if list for elements to be added is empty and the db is  exit
			#if db is emtry save the current config
			if not toadd and is_db_config:
				self.output.info("Value " + ' '.join(input_data) + " for "  +self.PluginName +  " is already configured")
				return 0;

			# add the new elements to the current config
			curr_config.extend(toadd)

			# set new values
			res = self.set(curr_config)

			# if set was ok
			if res == 0:
				self.output.info("Added " + self.PluginName+"  " + ' '.join(toadd))

		except:
			self.printError("Adding "+self.PluginName+" " + ' '.join(data)+": ")
			return 1

		return 0


	def remove(self, data=''):
		''' Relete values
			Return 0 for OK and 1 for error
		'''
		plugin = self.PluginFqn

		try:
			file_type = self.get_xml_field(xmlparser.XML_PLUGIN_FILE_TYPE)
			if not file_type:
				raise ValueError('Field <file_type> in xml is not pressent for plugin '+ plugin)


			# Check input and transform it to a list
			# remove duplicate values
			if file_type == 'cache':
				input_data = self.validate_bulk_data(data)
			else:
				input_data = self.validate_input_data(data)

			todel = input_data


			#Get the configured servers
			current_config = self.get_current_config(self.PluginFqn)

			if not current_config:
				self.output.error("No " + self.PluginName + "(s) configured to be deleted")
				return 0

			bEntryRemoved=False

			for entry in todel:
				# if the entry is in current config remove it
				if entry in current_config:
					# iterate through the current config and remove the entry from command
					current_config = list(filter(lambda curr: curr!= entry, current_config))
					bEntryRemoved=True

			# if no entries were removed show a message and exit
			if not bEntryRemoved:
				self.output.info("Value " + ' '.join(input_data)  + " for " + self.PluginName + " is not configured.")
				return 0

			res = self.set(current_config)

			if res == 0:
				self.output.info("Deleted " + self.PluginName + "(s) " + ' '.join(todel))

		except:
			self.printError("Removing "+self.PluginName+" " + ' '.join(data)+": ")
			return 1

		return 0

	def disable(self):
		''' Removes the related plugin config and comments the key line in the file  '''
		try:
			data = pluginClass.DISABLE_PLUGIN
			res = self.set(data)
			if res == 0:
				self.output.info("Disabled %s" %self.PluginName)

		except:
			self.printError("Removing "+self.PluginName+" " + ' '.join(data)+": ")
			return 1
		return 0

