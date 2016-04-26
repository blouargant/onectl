#!/usr/bin/python -u
# Base class for all plugins

import os
import sys
import re
import subprocess
import inspect
import platform
import functools
import shutil
import ordereddict
import PluginsControler

from includes import xmlparser, hash, gprint
from difflib import unified_diff

DISABLE_PLUGIN = PluginsControler.DISABLE_PLUGIN

class Base():

	def __init__(self, gprinter, logger):
		self.messages = {}
		self.executeLaterDic = []
		self.gprint = gprinter
		self.output = gprint.OnectlPrinter(gprinter, self.messages)
		self.log = logger
		## Available logs :
		## log.error, log.warning, log.info, log.debug
		self.PluginName = self._get_name()
		self.PluginFqn = self._get_fqn()
		self.HookDic = ordereddict.OrderedDict()
		self.configDic = {}
		self.live_update = True
		# save the config or not.If default do not save it
		self.bSave = True
		self.XmlDic = {}
	def _set_configDic(self, configDic):
		self.configDic = configDic
	
	def _get_name(self):
		file = os.path.basename(inspect.getfile(self.__class__))
		tmpstr1 = re.sub('.*plugins.', '', file.replace("/", "."))
		tmpstr2 = re.sub('\.py$', '', tmpstr1)
		name = re.sub('\.pyc$', '', tmpstr2)
		return name
	
	def setOptions(self):
		''' Create additional argument parser options
			specific to the plugin '''
		'''
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
		
		Example:
		
		dic = []
		### Additional options, the line below is mandatory for bash autocompletion
		### OPTION: dothat
		opt1 = {}
		opt1['name'] = '--dothat'
		opt1['metavar'] = 'THING'
		opt1['action'] = 'store'
		opt1['nargs'] = '?'
		opt1['help'] = 'Do that THING.'
		dic.append(opt1)
		
		## To disable the --set options - for a read-only plugin
		### NO OPTION: set
		opt2 = {}
		opt2['name'] = '--set'
		opt2['metavar'] = ''
		opt2['action'] = ''
		opt2['nargs'] = ''
		opt2['help'] = ''
		dic.append(opt2)
		
		return dic
		'''
	
	def inputValidation(self, data):
		''' TO OVERWRITE IN PLUGINS -- MANDATORY --
		In this function, plugin creator must implement a data input validator
		If input is valid then the function must valid input data, else it must return None
		This function is automatically called, there is no need to call it within <set> function.
		Returns two values list to be set and list to be shown. Used in case
		of bind plugins
		'''
		return None
	
	def _get_fqn(self):
		file = os.path.abspath(inspect.getfile(self.__class__))
		#sys.modules[self.__class__.__module__].__file__
		tmpstr1 = re.sub('.*plugins.', '', file.replace("/", "."))
		#tmpstr2 = tmpstr1.strip(".py")
		#pluginFqn = tmpstr2.strip(".pyc")
		
		tmpstr2 = re.sub('\.py$', '', tmpstr1)
		pluginFqn = re.sub('\.pyc$', '', tmpstr2)
		return pluginFqn
	
	def set_output(self, enable_output):
		'''
		set_output(True/False) : Enable or disable screen output
		'''
		self.output.enable_output = enable_output
	
	
	def listToString(self, list):
		'''Convert a python list to a string of white-space sparated elements '''
		str = ""
		for astr in list:
			if str:
				str += " "+astr
			else:
				str = astr
		return str
	
	def _set(self, data):
		ret = 0
		try:
			ret = self.set(data)
			if len(self.messages["error"]) > 0:
				ret = 1
		except:
			err = str(sys.exc_info()[1])
			ret = 1
		
		if ret > 0:
			self.log.error('Cannot set '+self.PluginFqn+' to '+str(data))
		else:
			self.log.info(self.PluginFqn+' set to '+str(data))
		return ret
	
	def set(self, data):
		self.output.info(data)
	
	def get(self) :
		''' Get real implemanted configuration.
		    This function should be overwriten. '''
		self.show()
		return 0

	def get_active(self):
		''' Returns list of values! '''
		try:
			#self.output.disable()
			self.get()
			curr_config = self.listToString(self.messages["info"])
			self.output.clear_messages()
			#self.output.enable()
	
		except:
			raise
		return curr_config
		
	def clear(self,data):
		''' Clears the plugin configuration '''
		# if these was a previos value set it
		if hasattr(self, 'remove'):
			self.remove(data)
		else:
			self.bSave=False
			self.set(data)
			
		# if not set empty
		# remove the configuration
		
	def getopts(self):
		dic = []
		return dic
		
	def info(self):
		title = self.PluginFqn+" configuration"
		msg = "Show information on how to configure this plugin\n"
		msg += "--info should be more verbose than the --help message\n"
		msg += "something like a short man ...\n"
		self.output.help(title, msg)
		
	def view(self, data):
		input = data[0]
		if input == "diff":
			self.check()
		elif input == "saved":
			self._show()
		elif input == "actual":
			self.get()
		else:
			self.output.error("Unknown parameter "+str(input))
			self.output.warning("Possible values are: actual, saved or diff")
		
	def _show(self):
		self.show(True)
		return 0
	
	def show(self, verbose = False):
		if verbose:
			self.output.enable()
		else:
			self.output.disable()
		
		data = self.load_data()
		if data.has_key(self.PluginFqn):
			self.output.info(data[self.PluginFqn])
		else:
			self.output.warning(self.PluginFqn+" has not been set.")
		
		if not verbose:
			self.output.enable()
		return 0
	
	def _check(self, info_get='',info_show=''):
		''' Check the difference between the get and show function.
			This is used to check for unwanted modifications.
			info_get and info_show can be overwriten if their output is not
			exactly the same.
		'''
		try:
			self.output.disable()
			if not info_get:
				self.get()
				info_get = self.listToString(self.messages["info"])
				self.output.clear_messages()
			if not info_show:
				self.show()
				info_show = self.listToString(self.messages["info"])
		
			check_get = info_get.strip()
			check_show = info_show.strip()
			self.output.enable()
			if not check_show:
				if self.output.show_warnings:
					self.output.warning("Key has not been set!")
					self.output.info(self.PluginFqn+" active setup: "+check_get)
				else:
					if not check_get:
						check_get = "None"
					self.output.fail(self.PluginFqn+" active setup: "+check_get)
				return 1
			if check_get != check_show:
				self.output.warning("Key configuration does not match active setup!")
				self.output.info(self.PluginFqn+" is set to:\n"+check_show+"\nwhile active setup is: \n"+check_get)
				return 1
		
			else:
				self.output.title("Key's configuration is active.")
				self.output.info(self.PluginFqn+" = "+check_show)
				return 0
		except:
			self.printError()
			return 1
		
	def check(self):
		res = self._check()
		return res
		
	def check_short(self):
		self.output.show_warnings = False
		res = self.check()
		return res
		
	def createPlugin(self, template, newPlugin):
		''' Use createPlugin to dynamicaly create plugins.
			"template" is the template name to use, it must be placed in templates directory
			"newPlugin" is the FQN name of the plugin to create (eg net.conf.eth0)
			The template will be linked to newPlugin, thus any update on "template" will
			be available on "newPlugin".
		'''
		try:
			newPath = re.sub('\.', '/', newPlugin)
			file = inspect.getfile(self.__class__)
			#base = re.sub('/plugins.*', '', file)
			base = re.sub('onectl.*', 'onectl/', file)
			template_path = os.path.join(base, "templates/"+template)
			if  not os.path.exists(template_path):
				raise ValueError('Template %s does not exist.Call support ' %template_path)
			
			if os.path.isfile(template_path):
				dest_path = os.path.join(base, "plugins/"+newPath+".py")
			else:
				dest_path = os.path.join(base, "plugins/"+newPath)
			
			dest_dir = os.path.dirname(dest_path)
			if not os.path.lexists(dest_dir):
				os.makedirs(dest_dir)
			#shutil.copy2(template_path, dest_path)
			if not os.path.lexists(dest_path):
				os.symlink(template_path, dest_path)
		except:
			self.printError()
			return 1
		
		return 0
		
	def removePlugin(self, plugin):
		try:
			#data = ordereddict.OrderedDict()
			
			path = re.sub('\.', '/', plugin)
			file = inspect.getfile(self.__class__)
			#base = re.sub('/plugins.*', '', file)
			base = re.sub('onectl.*', 'onectl/', file)
			dest_path_py = os.path.join(base, "plugins/"+path+".py")
			dest_path_pyc = os.path.join(base, "plugins/"+path+".pyc")
			dest_dir = os.path.dirname(dest_path_py)
			if os.path.exists(dest_path_py):
				#os.unlink(dest_path_py)
				os.remove(dest_path_py)
			if os.path.exists(dest_path_pyc):
				os.remove(dest_path_pyc)
			if os.path.exists(dest_dir):
				if len(os.listdir(dest_dir)) == 0:
					os.removedirs(dest_dir)
			self.output.debug("Removing "+plugin+" entry in data file")
			data = self.load_data()
			if data.has_key(plugin):
				del data[plugin]
			self.output.debug(str(data))
			self.write_data(data)
		
		except:
			self.printError()
			return 1
		
		return 0
		
	def load_bound(self):
		bound = ordereddict.OrderedDict()
		if "bind_path" in self.configDic:
			bindFile = self.configDic["bind_path"]
			if os.path.exists(bindFile):
				fdata = open(bindFile, 'r')
				data_lines = fdata.readlines()
				fdata.close()
				for aline in data_lines:
					if not re.search("^ *#", aline) and  re.search("=",aline):
						data_args = aline.split('=', 1)
						bound[data_args[0].strip()] = data_args[1].strip()
		return bound
		
	def load_data(self):
		try:
			bound = self.load_bound()
			data = ordereddict.OrderedDict()
			if "data_path" in self.configDic:
				dataFile = self.configDic["data_path"]
				if os.path.exists(dataFile):
					fdata = open(dataFile, 'r')
					data_lines = fdata.readlines()
					fdata.close()
					for aline in data_lines:
						if re.search("^ *#", aline):
							continue
						
						aline = aline.strip()
						if not aline:
							continue
						
						aline = re.sub('#.*', '', aline)
						
						if not  re.search("=",aline):
							raise ValueError("Invalid input %s.Format is KEY=VALUE" %aline)
					
						data_args = aline.split('=', 1)
						data[data_args[0].strip()] = data_args[1].strip()
						
			for link in bound:
				if bound[link] in data:
					data[link] = data[bound[link]]
		except:
			self.printError()
		
		return data
		
	def write_data(self, data, file=None):
		try:
			if not data:
				return
				
			bound = self.load_bound()
				
			if not file:
				file = self.configDic["data_path"]
				# if no data_path configured return
				if not self.configDic.has_key("data_path"):
					return
			lines = []
			for akey in data:
				if not data[akey] or data[akey]==DISABLE_PLUGIN:
					continue
				if akey in bound:
					lines.append(akey+" = "+ bound[akey]+"\n")
				elif data[akey]:
					lines.append(akey+" = "+data[akey]+"\n")
			
			fdata = open(file, 'w')
			fdata.writelines(lines)
			fdata.close()
		
		except:
			self.printError()
		
	def getBoundValue(self, value):
		''' Check if plugin and get the value if not return the same value '''
		if type(value) is list:
			if len(value) == 1:
				conf_value = value[0]
			else:
				return value
		# Get the whole config
		config = self.get_current_config()
		# if the configured value is a plugin get the value and check if saved
		if conf_value in config:
		
			if type(value) is list:
				return [config[conf_value]]
			else:
				return config[conf_value]
		else:
			return value
		
	def getConfig(self):
		''' Return plugin configuration '''
		conf = ''
		self.output.disable()
		self.show()
		self.output.enable()
		if len(self.messages["info"]) > 0:
			conf = self.messages["info"][0]
		return conf
		
	def get_current_config(self, plugin = None):
		''' Get the current confiiguration. If plugin is specified return
		config for plugin only config. returened value is a list  '''
		out_config = []
		config = self.load_data()
		if plugin: 
			if plugin in config:
				config_str = config[plugin]
				config_str.strip()
				if config_str:
					out_config = config_str.split(' ')
		else:
			out_config = config
		return out_config
		
	def validate_input_data(self, data, bSort = True):
		''' Get the input data and place it in a list ,remove duplicate values
		and sort it . If bSort is True output is sorted'''
		outdata = []
		data_list = []
		
		if not data:
			return outdata
		
		# If disable was set
		if data == DISABLE_PLUGIN:
			return outdata
			
		if type(data) is list:
			data_list = data
		elif type(data) is str:
			# in case a list of values
			data_list = data.split()
		else:
			data_list.append(data)
			
		#remove duplicate values
		for value in data_list:
			if value not in outdata:
				outdata.append(value)
			
		if bSort:
			outdata = sorted(outdata)
		return outdata
		
		
	def validate_bulk_data(self, data, bulk_separator = '='):
		''' Validate input when in form key=value key=value  '''
		
		try:
			data_list = []
			
			if not data:
				return data_list
				
			if data == DISABLE_PLUGIN:
				return data_list
				
			if type(data) is list:
				data_list = data
			else:
				data_list.append(data)
			
			key_list = []
			out_list = []
			for adata in data:
				if re.search(bulk_separator, adata):
					key, value = adata.split(bulk_separator, 1)
					if adata not in out_list and key not in key_list:
						out_list.append(adata)
						key_list.append(key)
				else:
					raise ValueError('Invalid input: should be key=value')
		except:
			raise
		
		return out_list
		
	def printError(self,error_header = None):
		''' On fail get the error print it and log it '''
		#add check here
		if not error_header:
			error_header=''
		
		err=""
		if len(sys.exc_info()) > 0:
			err = str(sys.exc_info()[1])
		if self.log:
			self.log.error(error_header+err)
		self.output.error(error_header+err)
		
	def printWarn(self,error_header=None, post_message=None):
		''' On fail get the warning print it and log it '''
		if not error_header:
			error_header = ""
		if not post_message:
			post_message=""
		#add check here
		err=""
		if len(sys.exc_info()) > 0:
			err = str(sys.exc_info()[1])
		if self.log:
			self.log.warning(error_header+err)
		self.output.warning(error_header+err)
		if post_message:
			if self.log:
				self.log.warning(post_message)
			self.output.warning(post_message)
		
	def pluginToPath(self, plugin):
		newPath = re.sub('\.', '/', plugin)
		base = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
		dest_path = os.path.join(base, "plugins/"+newPath+".xml")
		return dest_path
		
	def pathToPlugin(self, path):
		tmpline = path.replace("/", ".")
		path_plugin = re.sub('.xml$', '', tmpline)
		plugin = re.sub('.*plugins.', '', path_plugin)
			
		return plugin
		
	def updateKeyListEntry(self, data_list, separator = ':'):
		''' update an entry of type List.
			data_list contains a list of Key:Values.
			By default a Key and a Value is separated by ":".
			The separator can be overwriten by the "separator" parameter.
			Note that the separator must be the same that the one used in the original configuration.
		'''
		try:
			org_list = self.get_current_config(self.PluginFqn)
			dic = {}
			# First populate dic with the original settings
			for entry in org_list:
				if not re.search(separator, entry):
					continue
				infos = entry.split(separator)
				dic[infos[0]] = infos[1]
			# Then overwrite dic with the updated entries
			for entry in data_list:
				if not re.search(separator, entry):
					continue
				infos = entry.split(separator)
				dic[infos[0]] = infos[1]
			
			# Finaly recreate the list with the updated content
			# and call set() function
			list = []
			for key in dic.keys():
				list.append(key+':'+dic[key])
			self.set(list)
		
		except:
			self.printError("updateKeyListEntry "+self.PluginName+": ")
			return 1
		
		return 0
		
	def addSimpleListEntry(self, data_list):
		''' add data_list to plugin entry of type List.
			data_list contains a list of simple values to add.
		'''
		try:
			org_list = self.getConfig().split(',')
			org_list.extend(data_list)
			self.set(org_list)
		
		except:
			self.printError("addSimpleListEntry "+self.PluginName+": ")
			return 1
		
		return 0
		
	def removeSimpleListEntry(self, data_list):
		''' remove data_list content from plugin entries (of type List).
			data_list contains a list of simple values to remove.
			If a value is not present in the original list it is ignored.
		'''
		try:
			org_list = self.getConfig().split(',')
			
			for value in data_list:
				if value in org_list:
					org_list.pop(org_list.index(value))
			
			self.set(org_list)
		
		except:
			self.printError("removeSimpleListEntry "+self.PluginName+": ")
			return 1
		
		return 0
		
	def executePlugin(self, plugin_fqn, funct, *args):
		''' Execute another plugin
				* plugin_fqn : plugin fully qualified name, eg net.vlans
				* funct      : plugin's function to execute
				* args		 : List of arguments to provide to function funct
			NB: args must always be a python list, even when there is only on argument
			return None if the plugin do not exists
		'''
		messages = ""
		try:
			pluginCtl = PluginsControler.Controler(self.gprint)
			pluginCtl.configDic = self.configDic
			pluginCtl.load_hooks()
			pluginCtl.PluginModule = pluginCtl.load_plugin(plugin_fqn)
			if pluginCtl.PluginModule:
				pluginCtl.PluginModule.live_update = self.live_update
				if args:
					result = pluginCtl.execute_function(funct, False, *args)
				else:
					result = pluginCtl.execute_function(funct, False)
				
				errors = pluginCtl.PluginModule.messages['error']
				#if errors:
				#	return 1
				if len(errors):
					messages = errors[0]
				elif len(pluginCtl.PluginModule.messages['info']) > 0:
					messages = pluginCtl.PluginModule.messages['info'][0]
				else:
					messages = ''
			else:
				#return 1
				messages = 'Error: cannot load plugin '+plugin_fqn
				#self.output.error(messages)
			#self.output.debug('\n'.join(errors))
		except:
			err = str(sys.exc_info()[1])
			self.output.debug("error executing "+plugin_fqn+" --"+funct+" "+str(args))
			self.output.debug("--> "+err)
			messages = 'Error: '+str(err)
		
		return messages
		
	def executePluginLater(self, plugin_fqn, funct, *args):
		''' Execute another plugin after the caller has terminated successfuly
				* plugin_fqn : plugin fully qualified name, eg net.vlans
				* funct      : plugin's function to execute
				* args       : List of arguments to provide to function funct
			NB: args must always be a python list, even when there is only on argument
			return None if the plugin do not exists
		'''
		try:
			entry = {}
			entry['plugin'] = plugin_fqn
			entry['function'] = funct
			entry['args'] = args
			self.executeLaterDic.append(entry)
		
		except:
			self.printError()
			return 1
		return 0
		
	def create_xml_plugins(self):
		''' Read the xmls and create plugins  '''
		try:
			localpath = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
			xml_main_dir = os.path.join(localpath, "xml/")
			xml_path = ''
			
			if not os.path.exists(xml_main_dir):
				return
				
			bIsCreationOK = True
			xml_dirs = os.listdir(xml_main_dir)
			for dir in xml_dirs:
				xml_dir = os.path.join(xml_main_dir, dir)
				# Generate plugins from xmls describing plugins in xml dir
				# keep hash for each xml in a file.Compare to check if updated
				# if file does not exist create it
				installed_xmls = os.path.join(xml_dir, ".installed_xml")
				prev_installed_xmls = os.path.join(xml_dir, ".prev_installed_xmls")
				if not os.path.exists(installed_xmls):
					hash.create_hash_file(xml_dir, installed_xmls)
					# for all xmls in the xml dir
					xml_files = os.listdir(xml_dir)
					for xml in xml_files:
						if not re.search('\.xml$', xml):
							continue
							
						# Get the xml path
						xml_path = os.path.join(xml_dir, xml)
						try:
							self.cretePluginFromXml(xml_path)
						except:
							bIsCreationOK = False
							self.printWarn("Xml file %s plugins were not created: " %xml_path, "Please fix the problem and execute onectl --load-plugins")
							pass
				else:
					os.system('mv ' + installed_xmls + ' ' + prev_installed_xmls)
					hash.create_hash_file(xml_dir, installed_xmls)
					
					OLD_PATH = prev_installed_xmls
					NEW_PATH = installed_xmls
					old = open(OLD_PATH, 'r')
					old_lines = list(old)
					old.close()
					
					new = open(NEW_PATH, 'r')
					new_lines = list(new)
					new.close()
					
					for line in unified_diff(old_lines, new_lines, fromfile=OLD_PATH,tofile=NEW_PATH):
						line_parts=line.split(',',1)
						if len(line_parts) != 2:
							continue
						xml_path = line_parts[1].rstrip()
						if not re.search('\.xml$', xml_path):
							continue
						if line.startswith('-'):
							self.deletePluginFromXml(xml_path)
						elif line.startswith('+'):
							try:
								self.cretePluginFromXml(xml_path)
							except:
								bIsCreationOK = False
								self.printWarn("Plugin creation from xml file %s: " %xml_path, "Relevant plugins were not created.Please fix the problem and execute onectl --load-plugins")
								continue
				if not bIsCreationOK:
					if os.path.exists(installed_xmls):
						os.system('rm -rf ' +  installed_xmls)
					if os.path.exists(prev_installed_xmls):
						os.system('rm -rf ' +  prev_installed_xmls)
				else:
					if os.path.exists(prev_installed_xmls):
						os.system('rm -rf ' +  prev_installed_xmls)
					
				# Generate the plugins from files listed in the xml
				# xml/dynamic dir
				dync_xml_dir = os.path.join(xml_dir, "dynamic/")
				if os.path.exists(dync_xml_dir):
					xml_files = os.listdir(dync_xml_dir)
					for xml in xml_files:
						if not re.search('\.xml$', xml):
							continue
						
						# Get the xml path
						xml_path = os.path.join(dync_xml_dir, xml)
						try:
							self.creteDyncPluginFromXml(xml_path)
						except:
							self.printWarn("Plugin creation from  xml %s: " %xml_path, "Relevant plugins were not created.Please fix the problem and execute onectl --load-plugins")
		except:
			self.printError("Create plugin from xml %s failure.Please fix the problem and execute onectl --load-plugins: " %xml_path)
		
	def get_xml_field(self,tag):
		""" Get the value from xml."""
		# if xml file was not read before make a dictionary and save it
		if not self.XmlDic:
			plugin = self.PluginFqn
			newPath = re.sub('\.', '/', plugin)
			base = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
			xml_path = os.path.join(base, "plugins/"+newPath+".xml")
			
			if not os.path.exists(xml_path):
				self.output.error("No XML file specified for plugin %s" %self.PluginName)
				return None
			# create the dictionary
			self.XmlDic = xmlparser.create_xml_dict(xml_path)
		
		# get the requested field from the dictionary
		value = xmlparser.get_xml_field_from_dict(self.XmlDic, tag)
		return value
		
	def cretePluginFromXml(self,xml_file):
		''' Crete plugins from xmls '''
		try:
			if not xml_file:
				return
				
			file_type = xmlparser.get_xml_field_from_xmlfile(xml_file,xmlparser.XML_PLUGIN_FILE_TYPE)
			if not file_type:
				raise ValueError('Field <file_type> in xml %s is not pressent ' %xml_file)
			
			if file_type not in xmlparser.XML_FILE_TYPES:
				raise ValueError('Unknown filetype %s in xml %s. Valid types: %s' %(file_type,xml_file, ' '.join(xmlparser.XML_FILE_TYPES)))
			
			# If xml is for creation dynamicaly exit
			if file_type in xmlparser.XML_DYNC_FILE_TYPES:
				return
			
			template_plugin = ''
			if file_type == 'service':
				template_plugin = "plugin_service.py"
			else:
				file = xmlparser.get_xml_field_from_xmlfile(xml_file,xmlparser.XML_PLUGIN_FILE)
				if not file:
					raise ValueError('Field <file> in xml %s is not pressent '%xml_file)
				template_plugin = "plugin_general.py"
			
			# get the plugins
			plugins=xmlparser.get_xml_field_from_xmlfile(xml_file,'plugins/plugin')
			plugins = self.validate_input_data(plugins)
			for plugin in plugins:
				# Validate the xml file for the plugin
				xmlparser.validatePluginFromXml( xml_file,file_type, plugin)
				
				plugin_name = plugin['name']
				# Create the plugin
				self.createPlugin(template_plugin, plugin_name)
				plugin_path = self.pluginToPath(plugin_name)
				if not os.path.lexists(plugin_path):
					os.symlink(xml_file, plugin_path)
				
				# in case of a service create the same plugin_name linked to service dir
				if file_type == 'service' and  not plugin_name.startswith('services.'):
					synonym_pugin = plugin_name[plugin_name.index('service'):]
					# replace the start of the of the plugin_name with services
					# always
					synonym_pugin = re.sub("^service\.", "services.", synonym_pugin,1)
					self.createPlugin(template_plugin, synonym_pugin)
					plugin_path = self.pluginToPath(synonym_pugin)
					if not os.path.lexists(plugin_path):
						os.symlink(xml_file, plugin_path)
						
		except:
			raise
		
	def deletePluginFromXml(self,xml_file):
		''' Delete the plugins in an xml  '''
		try:
			if not xml_file:
				return
			
			# xml file was removed or plugin deleted
			# remove the plugins assosiated with this xml file
			for root, dirs, files in os.walk('/usr/share/onectl/plugins'):
				for filename in files:
					path = os.path.join(root,filename)
					if os.path.islink(path):
						target_path = os.readlink(path)
						if not os.path.isabs(target_path):
							target_path = os.path.join(os.path.dirname(path),target_path)
						if not os.path.exists(target_path) or target_path == xml_file:
							plugin = self.pathToPlugin(path)
							os.unlink(path)
							self.removePlugin( plugin)
		except:
			self.printError("Remove plugin from xml %s failure: " %xml_file)
		
	def creteDyncPluginFromXml(self,xml_file):
		''' Crete plugins from xmls '''
		try:
			if not xml_file:
				return
			
			file = xmlparser.get_xml_field_from_xmlfile(xml_file,xmlparser.XML_PLUGIN_FILE)
			if not file:
				raise ValueError('Field <file> in xml %s is not pressent ' %xml_file)
			
			if not os.path.exists(file):
				raise ValueError('File %s configured in field <file> does not exist ' %(file))
			
			file_type = xmlparser.get_xml_field_from_xmlfile(xml_file,xmlparser.XML_PLUGIN_FILE_TYPE)
			if not file_type:
				raise ValueError('Field <file_type> in xml %s is not pressent ' %xml_file)
			
			if file_type not in xmlparser.XML_FILE_TYPES:
				raise ValueError('Unknown filetype %s in xml %s. Valid types: %s' %(file_type,xml_file, ' '.join(xmlparser.XML_FILE_TYPES)))
			
			template_plugin = ''
			template_plugin = "plugin_xml.py"
			plugin_start = xmlparser.get_xml_field_from_xmlfile(xml_file,xmlparser.XML_PLUGIN_DESTINATION)
			if not plugin_start:
				raise ValueError('Field <location> in xml %s is not pressent ' %xml_file)
			
			if file_type == 'log4j':
				# get the plugins
				parents=xmlparser.get_log4j_plugins_tocreate(file,'appender[@name]/param[@name]')
				for parent,children in parents.iteritems():
					for child in children:
						plugin= plugin_start + '.' + parent + '.' + child
						self.createPlugin(template_plugin, plugin)
						plugin_path = self.pluginToPath(plugin)
						if not os.path.lexists(plugin_path):
							os.symlink(xml_file, plugin_path)
		except:
			raise

