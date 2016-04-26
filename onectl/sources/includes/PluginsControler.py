#!/usr/bin/python -u

import os
import sys
import re
import imp
import subprocess
import gprint
import onectlog
import ordereddict
import fnmatch
import git
import getconfig
DISABLE_PLUGIN = 'none'

class Controler:
	def __init__(self, gprinter = None):
		""" Plugin's Core functions """
		self.log = None
		if gprinter:
			self.gprint = gprinter
		else:
			self.gprint = gprint.GraphicalPrinter()
		self.messages = {}
		self.output = gprint.OnectlPrinter(self.gprint, self.messages)
		self.PluginModule = None
		self.PluginName = ""
		self.pluginList = []
		self.logger = None
		self.debug = False
		self.nolive = False
		self.configDic = {}
		self.HookDic = ordereddict.OrderedDict()
		self.data = ordereddict.OrderedDict()
		# keeps bound plug-ins
		self.bound = ordereddict.OrderedDict()
		self.priorityPlugins=['net.devices','net.vlans','net.aliases','net.bonds']
		#start the subscribe server on the default port
		self.subServer = None
		
	def printError(self,error_header = None):
		''' On fail get the error print it and log it '''
		#add check here
		if not error_header:
			error_header=''
		
		err=""
		if len(sys.exc_info()) > 0:
			err = str(sys.exc_info()[1])
		if self.logger:
			self.logger.error(error_header+err)
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
		if self.logger:
			self.logger.warning(error_header+err)
		self.output.warning(error_header+err)
		if post_message:
			if self.logger:
				self.logger.warning(post_message)
			self.output.warning(post_message)
		
	def ListToString(self, list):
		str = ""
		for astr in list:
			if str:
				str += " "+astr
			else:
				str = astr
		return str
		
	def get_config(self, configFile):
		self.configDic = getconfig.load_config_file(configFile)
		self.debug = self.configDic["debug"]
		self.logger = onectlog.Logger(self.configDic["log"])
		
	def order_data(self,dataDic):
		''' From config dictionary order it for correct applying '''
		out_data = ordereddict.OrderedDict()
		for plugin in self.priorityPlugins:
			if plugin in dataDic:
				out_data[plugin] = dataDic[plugin]
				del dataDic[plugin]
		if out_data:
			out_data=ordereddict.OrderedDict(out_data.items() + dataDic.items())
		else:
			out_data=dataDic
		return out_data
	
	def load_data(self, dataFile):
		''' load onectl config from file to dictionary '''
		try:
			# get the data for the linked plugins
			boundFile = self.configDic["bind_path"]
			if os.path.exists(boundFile):
				fdata = open(boundFile, 'r')
				data_lines = fdata.readlines()
				fdata.close()
				for aline in data_lines:
					if re.search("^ *#", aline):
						continue
					if not  re.search("=", aline):
						raise ValueError("Invalid input %s.Format is KEY=VALUE" %aline)
					
					data_args = aline.split('=', 1)
					self.bound[data_args[0].strip()] = data_args[1].strip()
			
			out_data = ordereddict.OrderedDict()
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
					out_data[data_args[0].strip()] = data_args[1].strip()
			
			for bind in self.bound:
				if self.bound[bind] in out_data:
					out_data[bind] = out_data[self.bound[bind]]
		
		except:
			self.printError()
			raise
		
		return out_data
	
	def write_data(self, dataFile, dataDic=None):
		try:
			lines = []
			if not dataDic:
				dataDic = self.data
			
			for akey in dataDic:
				value = dataDic[akey]
				if not value or value==DISABLE_PLUGIN:
					continue
				if type(value) is list:
					value = ' '.join(value)
				if akey in self.bound:
					lines.append(akey+" = "+ self.bound[akey]+"\n")
				else:
					lines.append(akey+" = "+value+"\n")
			
			fdata = open(dataFile, 'w')
			fdata.writelines(lines)
			fdata.close()
		
		except:
			self.printError()
	
	def saveDataIfModified(self, dataPrime):
		try:
			if dataPrime != self.data:
				self.write_data(dataPrime)
		
		except:
			self.printError()
		
	def show_keys_config(self, akey=None):
		''' Return 0 on ok and 1 on error  '''
		try:
			if akey == None:
				akey = ""
			plug_list = self.get_plugin_list(akey)
			if len(plug_list) > 0:
				for aplugin in plug_list:
					PluginModule = self.load_plugin(aplugin)
					if not PluginModule:
						self.output.warning('Cannot find '+str(aplugin)+' key.')
					else:
						PluginModule.check_short()
						self.messages['output'].extend(PluginModule.messages['output'])
		except:
			self.printError()
			return 1
		return 0
		
	def show_plugin_info(self, akey=None):
		try:
			if akey == None:
				akey = ""
			output_arr = []
			plug_list = self.get_plugin_list(akey)
			if len(plug_list) > 0:
				for aplugin in plug_list:
					PluginModule = self.load_plugin(aplugin)
					if not PluginModule:
						self.output.warning('Cannot find '+str(aplugin)+' key.')
					else:
						PluginModule.info()
						info = PluginModule.messages['output']
						self.messages['output'].extend(info)
		except:
			self.printError()
			return 1
		return 0

	def print_plugin_list(self, key_name=None):
		''' print the plugins available '''
		output_str = ''
		try:
			plug_list = self.get_plugin_list(key_name)
			if len(plug_list) > 0:
				self.output.i_ok("Available keys:")
				output_str = '\n'.join(plug_list)
				self.output.info(output_str)
		except:
			self.printError()
			return 1
		return 0
		
	def dump_config(self, key=""):
		''' Return config as a string '''
		try:
			output_str = ''
			if os.path.exists(self.configDic["data_path"]):
				fdata = open(self.configDic["data_path"], 'r')
				data_lines = fdata.readlines()
				fdata.close()
				output_list = []
				for aline in data_lines:
					if re.search("^ *#", aline):
						continue
					if key and re.search("^"+key, aline):
						#self.gprint.info(aline.strip())
						output_list.append(aline.strip())
					elif not key:
						output_list.append(aline.strip())
						#self.gprint.info(aline.strip())
				output_str = '\n'.join(output_list)
				self.output.info(output_str)
		
		except:
			self.printError()
			return 1
			
		return 0
		
	def bind_plugins(self, data):
		''' Link two plugins. Data is a list 0 holds source 1 destination  '''
		src_plugin = data[0]
		dst_plugin = data[1]
		try:
			plug_list = self.get_plugin_list()
			if src_plugin not in plug_list:
				raise ValueError('Please enter valid source plug-in.%s is not a valid plug-in' %src_plugin)
			if dst_plugin not in plug_list:
				raise ValueError('Please enter valid destination plug-in.%s is not a valid plug-in' %dst_plugin)
			
			# create the hook file set , get
			# copy in data file the new value
			bindFile = self.configDic["bind_path"]
			line  = src_plugin +' = '+ dst_plugin + '\n'
			with open(bindFile,'a+') as f: f.write(line)
			
			self.data = self.load_data(self.configDic["data_path"])
			if dst_plugin in self.data:
				data = self.data[dst_plugin]
				if data:
					srcPlugin = self.load_plugin(src_plugin)
					if srcPlugin:
						res = self._execute_function(srcPlugin, 'set', False, [data])
			
			# create the hook
			lines=[]
			lines.append('targetPlugin = ' + dst_plugin + '\n')
			lines.append('targetFunction = set' + '\n')
			lines.append('callPlugin = ' + src_plugin + '\n')
			lines.append('callFunction = set' + '\n')
			
			localpath = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
			hooks_file = os.path.join(localpath, "hooks/",src_plugin+'.hook')
			
			with open(hooks_file,'a+') as f: f.writelines(lines)
		
		except:
			self.printError()
			return 1
		return 0
	
	def unbind_plugins(self, argv):
		#src_plugin = argv[0]
		dst_plugin = argv[0]
		try:
			# delete bound plugin
			# del self.bound[dst_plugin]
			bindFile = self.configDic["bind_path"]
			if os.path.exists(bindFile):
				# Get the current config from the data file
				self.data = self.load_data(self.configDic["data_path"])
				
				# Remove the bind file
				f = open(bindFile,"r")
				lines = f.readlines()
				f.close()
				f = open(bindFile,"w")
				for line in lines:
					if not re.search("=", aline):
						continue
					line_data = line.split('=',1)
					if dst_plugin not in line_data[0]:
						f.write(line)
				f.close()
				
				# if the bind file is emtry delete it
				if os.stat(bindFile).st_size==0:
					os.remove(bindFile)
				
				# remove the entry so that the data file is updated correctly below
				if dst_plugin in self.bound:
					del self.bound[dst_plugin]
				
				# Remove the hooks related to the bind
				localpath = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
				hooks_file = os.path.join(localpath, "hooks/",dst_plugin +'.hook')
				if os.path.exists(hooks_file):
					os.remove(hooks_file)
				
				self.write_data(self.configDic["data_path"])
		
		except:
			self.printError()
			return 1
		return 0
	
	def load_config(self, newconfig, oldconfig=None):
		''' Reload the config from two dictionaries  '''
		try:
		
			backup_file  = self.configDic["backup_path"]
			firstconfig = self.load_data(backup_file)
			all_plugins = self.get_plugin_list()
			
			plugins = []
			for key in newconfig.keys():
				plugins.append(key)
			if oldconfig:
				for key in oldconfig.keys():
					plugins.append(key)
			
			# Get the plugins to be updated
			plugins_update = ordereddict.OrderedDict()
			# The plugins to be deleted
			plugins_clear = ordereddict.OrderedDict()
			# previous state plugins not in the config
			plugins_default = ordereddict.OrderedDict()
			for plugin in plugins:
				# value to set
				if plugin  in newconfig:
					plugins_update[plugin]=newconfig[plugin]
				elif plugin in oldconfig:
					# it should be deleted.First check if it had value before
					if plugin in firstconfig:
						plugins_default[plugin]= firstconfig[plugin]
					
					else:
						# should be deleted get the old values
						plugins_clear[plugin]=oldconfig[plugin]
					# it is not in the new config but was in the old.Delete it
				elif plugin in firstconfig:
					plugins_default[plugin]= firstconfig[plugin]
				else:
					plugins_clear[plugin]=''
			
			# Check all lines before proceeding to configuration
			self.output.title('Checking new configuration ...')
			# put the priority plugins first
			plugins_update = self.order_data(plugins_update)
			for plugin in plugins_update:
				key = plugin
				values = plugins_update[key]
				# if no values was configured skip
				if not values:
					continue
				# assigned value is plugin
				if values in all_plugins:
					if values not in newconfig:
						raise ValueError("Bound plugin %s=%s.No value configured for %s" %(key,values,values))
					else:
						values = newconfig[values]
				
				PluginModule = self.load_plugin(key)
				if not PluginModule:
					self.output.warning('Cannot verify '+str(key)+' yet.')
				else:
					self.PluginName = key
					self.PluginModule = PluginModule
					values=self.PluginModule.validate_input_data(values)
					validated = self.PluginModule.inputValidation(values)
					if not validated:
						return 1
			
			# Delete plugins
			self.output.title('Clearing keys ...')
			for plugin in plugins_clear:
				key = plugin
				values = plugins_clear[plugin]
				
				PluginModule = self.load_plugin(key)
				if not PluginModule:
					continue
					#raise ValueError('Plugin %s does not exist.Please check the name or if it was configured correctly in advance.\nThe same plugin on new line delete previous config' %key)
				
				self.PluginName = key
				self.PluginModule = PluginModule
				values=self.PluginModule.validate_input_data(values)
				# if these was a previos value set it
				self.output.info('%s = %s' %(key,values))
				if hasattr(self.PluginModule, 'remove'):
					res = self.execute_function("remove", False, values)
				else:
					self.PluginModule.bSave=False
					res = self.execute_function("set", False, values)
			
			self.output.title('Reverting keys ...')
			for plugin in plugins_default:
				key = plugin
				values = plugins_default[plugin]
				
				PluginModule = self.load_plugin(key)
				if not PluginModule:
					continue
				
				self.output.info('%s = %s' %(key,values))
				self.PluginName = key
				self.PluginModule = PluginModule
				values=self.PluginModule.validate_input_data(values)
				self.PluginModule.bSave=False
				res = self.execute_function("set", False, values)
			
			# file has been validated
			# proceeding with configuration
			self.output.title('Configuring new keys ...')
			for plugin in plugins_update:
				key = plugin
				values = plugins_update[plugin]
				self.output.info('%s = %s' %(key,values))
				
				# if the configured value is a plugin get the value and check if saved
				if values in all_plugins:
					input_data=[key, values]
					self.bind_plugins(input_data)
				else:
					PluginModule = self.load_plugin(key)
					if not PluginModule:
						self.output.warning('Plugin %s does not exist.Please check the name or if it was configured correctly in advance.\nThe same plugin on new line delete previous config' %key)
						continue
					
					self.PluginName = key
					self.PluginModule = PluginModule
					values=self.PluginModule.validate_input_data(values)
					if values:
						res = self.execute_function("set", False, values)
						if res == 1 :
							self.output.error('Error while applying %s = %s' %(key,values))
							#self.messages['output'].extend(self.PluginModule.messages['output'])
							self.output.error('Aborting !')
							return 1
			
			self.output.title("Configuration file correctly applied")
		
		except:
			self.printError()
		
	def load_file(self, input_file):
		''' set new config from a configuration file '''
		try:
			if type(input_file) is list:
				input_file = input_file[0]
			
			if input_file[0] != "/":
				HERE = os.getcwd()
				filename = HERE+"/"+input_file
			else:
				filename = input_file
			if not os.path.exists(filename):
				self.output.error('File %s not found' %filename)
				return 1
			if not os.path.isfile(filename):
				self.output.error('%s is not a file' %filename)
				return 1
			
			config_file = self.configDic["data_path"]
			# get the previous state
			oldconfig = self.load_data(config_file)
			
			newconfig=self.load_data(filename)
			if not newconfig:
				self.output.error('%s is empty' %filename)
				return 1
			self.load_config(newconfig, oldconfig)
		except:
			self.printError()
			return 1
		return 0
		
	def load_xml_plugins(self):
		try:
			localpath = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
			plugin_path = os.path.join(localpath, "templates/plugin_general.py")
			py_mod = imp.load_source('plugin_general',plugin_path)
			if hasattr(py_mod, "PluginControl"):
				class_ = getattr(py_mod, "PluginControl")
				class_inst = class_(self.gprint, self.logger)
				#class_inst.set = self.set_methode_wrapper(class_inst.set)
				
				# call creation of plugins in the xml dir
				class_inst.configDic = self.configDic
				res = getattr(class_inst, 'create_xml_plugins')()
			else:
				self.output.error("Error loading plug-ins")
		except:
			self.printError()
		
	def remote_client_inform(self):
		''' Send change to subscibed. Input is changed fields  '''
		try:
			result = git.gitGetLastChanges(self.configDic["repo_path"])
			if result:
				if not self.subServer:
					raise ValueError("Subscription server is not running")
				self.subServer.send_event(result)
		except:
			self.printError()
			return 1
		return 0
		
	def execute_action(self, plugin, action, data = None, debug = False, nolive = None):
		''' if data is several parameters use a list '''
		actionDic = {}
		
		if not plugin:
			actionDic['onectl'] = self.print_plugin_list
			actionDic['init'] = self.plugin_data_init
			actionDic['list'] = self.print_plugin_list
			actionDic['dump'] = self.dump_config
			actionDic['load'] = self.load_file
			actionDic['show'] = self.show_keys_config
			actionDic['info'] = self.show_plugin_info
			actionDic['bind'] = self.bind_plugins
			actionDic['unbind'] = self.unbind_plugins
			actionDic['load-plugins'] = self.load_xml_plugins
			actionDic['history'] = self.show_history
			actionDic['rollback'] = self.history_revert
			# Remote
#			actionDic['start'] = self.remote_server_start
#			actionDic['connect'] = self.remote_client_connect
#			actionDic['subscribe'] = self.remote_client_subscribe
#			actionDic['remote'] = self.remote_client_request
		try:
			result = 1
			output = ''
			if not plugin:
				if actionDic.has_key(action):
					callback = actionDic[action] 
					if data:
						result = callback(data)
					else:
						result = callback()
			else:
				PluginModule = self.load_plugin(plugin)
				if not PluginModule:
					raise ValueError("Plugin %s can not be loaded" %plugin)
				self.PluginName = plugin
				self.PluginModule = PluginModule
					
				if nolive:
					self.PluginModule.live_update = False
				if debug:
					self.gprint.debug = True
					
				if not data:
					result = self.execute_function(action, True)
				else:
					result = self.execute_function(action, True, data)
			
			import threading
			# get the changes and send them to the remote clients subscribed
			t = threading.Thread(target = self.remote_client_inform(), args=())
			t.start()
			# save change history
			t = threading.Thread(target = git.gitCommit, args=(self.configDic["repo_path"],))
			t.start()
			# get the changes and send them to the remote clients subscribed
			#self.remote_client_inform()
			# save change history
			#git.gitCommit( self.configDic["repo_path"])
		except:
			self.printError()
		finally:
			output = self.messages['output']
			self.output.clear_messages(True)
		return result, output
		
	def execute_function(self, function, output = False, *args):
		try:
			result = self._execute_function(self.PluginModule, function, output, *args)
			if output:
				# save messages for printing
				if 'output' in self.PluginModule.messages:
					self.messages['output'].extend(self.PluginModule.messages['output'])
				# clear  messages
				self.PluginModule.output.clear_messages(True)
			return result
		except:
			raise
		
	def _execute_function(self, plugin, function, output = False, *args):
		''' Return res, output '''
		if plugin:
			plugin.set_output(output)
			try:
				res = {}
				if hasattr(plugin, function):
					if args:
						res = getattr(plugin, function)(*args)
					else:
						res = getattr(plugin, function)()
							
					if res:
						return 1
					if len(plugin.messages['error']) > 0:
						return 1
				else:
					self.output.error(plugin.PluginFqn+" has no function "+function)
					return 1
					
				pluginFqn = plugin._get_fqn()
				if self.HookDic.has_key(pluginFqn):
					if self.HookDic[pluginFqn].has_key(function):
						callback_list =  self.HookDic[pluginFqn][function]
						for callback in callback_list:
							hookedPlugin = self.load_plugin(callback["plugin"])
							if hookedPlugin:
								res = self._execute_function(hookedPlugin, callback["function"], False, *args)
								if res > 0:
									return 1
				
			except:
				self.printError("Command not found !\n")
				return 1
			return 0
		else:
			return 1
		
	def set_methode_wrapper(self, pluginCtr, func):
		def inner(*args, **kwargs):
			ret = 1
			try:
				# Check the input and get value to be set
				data_ok = pluginCtr.inputValidation(*args)
				if data_ok != None:
					#ret = func(*args, **kwargs)
					self.output.clear_messages()
					# get the current state before setting the new value
					oldValue = pluginCtr.get_active()
					ret = func(data_ok)
				else:
					return ret
			except:
				ret = 1
				self.printError("Error excuting set command:")
			
			if len(pluginCtr.messages["error"]) > 0:
				if self.gprint.debug:
					self.output.error('\n'.join(self.PluginModule.messages["error"]))
				ret = 1
			if ret == 0:
				if type(data_ok) is list:
					info = self.ListToString(data_ok)
				else:
					info = data_ok
				self.data = self.load_data(self.configDic["data_path"])
				# This is the first configuration for the plugin
				if pluginCtr.PluginFqn not in self.data:
					# save the previous state to a backup file
					backupFile=self.configDic["backup_path"]
					bck_dict = self.load_data(backupFile)
					bck_dict[pluginCtr.PluginFqn] = oldValue
					self.write_data(backupFile, bck_dict)
				if not pluginCtr.bSave:
					# remove from data file
					info=''
				self.data[pluginCtr.PluginFqn] = info
				self.write_data(self.configDic["data_path"])
				
				# Once data has been saved we can execute plugins in executeLaterDic
				for entry in pluginCtr.executeLaterDic:
					plg = entry['plugin']
					fct = entry['function']
					fc_args = entry['args']
					self.output.warn_debug("Post execution of "+str(plg)+" "+str(fct)+" "+str(fc_args))
					msg = pluginCtr.executePlugin(plg, fct, *fc_args)
					if re.search('Error :', msg):
						self.output.warning("Action %s for plugin %s failed" %(fct, plg))
						
				return ret
		return inner
		
	def load_plugin(self, plugin_name):
		class_inst = None
		py_mod = None
		try:
			plugin_path = re.sub("\.", "/", plugin_name)
			expected_class = 'MyClass'
			localpath = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
			filepath = os.path.join(localpath, "plugins/"+plugin_path+".py")
			if not os.path.exists(filepath):
				return False
			
			mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
			if file_ext.lower() == '.py':
				py_mod = imp.load_source(mod_name, filepath)
				if hasattr(py_mod, "PluginControl"):
					class_ = getattr(py_mod, "PluginControl")
					class_inst = class_(self.gprint, self.logger)
					class_inst.set = self.set_methode_wrapper(class_inst,class_inst.set)
			
			elif file_ext.lower() == '.pyc':
				py_mod = imp.load_compiled(mod_name, filepath)
				if hasattr(py_mod, "PluginControl"):
					class_ = getattr(py_mod, "PluginControl")
					class_inst = class_(self.gprint, self.logger)
					class_inst.set = self.set_methode_wrapper(class_inst, class_inst.set)
			
			if class_inst:
				class_inst._set_configDic(self.configDic)
		
		except:
			self.printError()
			return False
		
		return class_inst
		#return py_mod
		
	def get_plugin_list(self, key_name=None):
		plugins = []
		try:
			if not key_name:
				key_name = ""
			
			if type(key_name) is list:
				key_name = key_name[0]
				
			localpath = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
			plugin_path = os.path.join(localpath, "plugins/", key_name.replace('.', '/'))
			
			plugin_path = plugin_path + '*'
			
			proc = subprocess.Popen(["find %s -name '*.py'" %plugin_path ], stdout=subprocess.PIPE, shell=True)
			code = proc.wait()
			for aline in proc.stdout:
				aline = aline.strip()
				if re.search(".*.py$", aline):
					tmpline = aline.replace("/", ".")
					path_plugin = re.sub('.py$', '', tmpline)
					plugin = re.sub('.*plugins.', '', path_plugin)
					plugins.append(plugin)
		except:
			self.printError()
		
		plugins.sort()
		return plugins
		
	def load_hooks(self):
		''' List all .hook files located in hooks/ directory and load them in a dictionnary '''
		try:
			localpath = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
			hooks_path = os.path.join(localpath, "hooks/")
			hooks_files = os.listdir(hooks_path)
			for aHook in hooks_files:
				if re.match(".*\.hook", aHook):
					fhook = open(hooks_path+"/"+aHook, 'r')
					hook_lines = fhook.readlines()
					fhook.close()
					targetPlugin = ""
					targetFunction = ""
					callPlugin = ""
					callFunction = ""
					for aline in hook_lines:
						if re.search ("=", aline) and not re.search("^ *#", aline) :
							hook_args = aline.split('=')
							data = re.sub("#.*", "", hook_args[1]).strip()
							if "targetPlugin" in hook_args[0]:
								targetPlugin = data
							if "targetFunction" in hook_args[0]:
								targetFunction = data
							if "callPlugin" in hook_args[0]:
								callPlugin = data
							if "callFunction" in hook_args[0]:
								callFunction = data
					
					if targetPlugin and targetFunction and callPlugin and callFunction:
						if not self.HookDic.has_key(targetPlugin):
							self.HookDic[targetPlugin] = {}
						if not self.HookDic[targetPlugin].has_key(targetFunction):
							self.HookDic[targetPlugin][targetFunction] = []
						newHook = {}
						newHook["plugin"] = callPlugin
						newHook["function"] = callFunction
						self.HookDic[targetPlugin][targetFunction].append(newHook)
					
					else:
						self.logger.warning(aHook+" not formated properly. Skipped")
			
		except:
			self.printError("load_hooks: ")
		
	def plugin_data_init(self, akey=None):
		''' Get all active states and save them to a file '''
		try:
			if akey == None:
				akey = ""
			data={}
			plug_list = self.get_plugin_list(akey)
			if len(plug_list) > 0:
				for aplugin in plug_list:
					if aplugin == 'sys.kernel' or aplugin == 'sys.distro':
						continue
					PluginModule = self.load_plugin(aplugin)
					if not PluginModule:
						self.output.warning('Cannot find '+str(aplugin)+' key.')
					else:
						try:
							curr_state = PluginModule.get_active()
						except:
							self.printWarn(" ")
							continue
						if type(curr_state) is list:
							curr_state = ' '.join(curr_state)
						data[PluginModule.PluginFqn]  = curr_state
			dataFile = self.configDic["data_path"]+'.all'
			self.write_data(dataFile, data)
		except:
			self.printError()
		
	def show_history(self,commitId=None):
		''' Get the history and display it  '''
		# input can be unicode also
		if type(commitId) is list:
			ID = commitId[0]
		else:
		#elif type(commitId) is str:
			ID = commitId
		#else:
		#	ID=None
		
		try:
			repoDir=self.configDic["repo_path"]
			if ID:
				ID = git.gitGetCommitIdBySeqNum(repoDir, ID)
				if ID:
					output = git.gitShow(repoDir, ID)
				else:
					output="Error: Invalid Changeset ID. Please check onectl --history"
			else:
				output = git.gitHistory(repoDir)
			self.output.info(output)
		except:
			self.printError()
			return 1
		return 0
		
	def history_revert(self, commitId=None):
		''' Revert config to a saved state  '''
		if type(commitId) is list:
			ID = commitId[0]
		elif type(commitId) is str:
			ID = commitId
		else:
			ID=None
		try:
			# get the data file
			fileData = self.configDic["data_path"]
			tmpFile=fileData+'.tmp'
			# get the previous state
			oldconfig = self.load_data(fileData)
			# get the repository location
			repoDir=self.configDic["repo_path"]
			ID = git.gitGetCommitIdBySeqNum(repoDir, ID)
			if ID:
				output = git.gitShow(repoDir, ID)
			else:
				raise ValueError("Invalid Changeset ID")
			
			# keep data
			file = open(tmpFile, "w")
			file.write(output)
			file.close()
			newconfig = self.load_data(tmpFile)
			# load the new config
			self.load_config(newconfig, oldconfig)
		except:
			self.printError()
			return 1
		return 0

