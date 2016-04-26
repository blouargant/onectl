import argparse
import re, sys
import gprint
# to be removed from here!!!!!
from includes import PluginsControler
from includes import onectlLib
from includes import onectlServer
from getpass import getpass

class OnectlCLI:
	def __init__(self, gprinter = None):
		""" Plugin's Core functions """
		self.logger = None
		if gprinter:
			self.gprint = gprinter
		else:
			self.gprint = gprint.GraphicalPrinter()
		self.messages = {}
		self.messages["output"] = []
		self.output = gprint.OnectlPrinter(self.gprint, self.messages)
	
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
		if "error" in self.messages:
			self.output.mprint('\n'.join(self.messages["error"]))
		
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
		if "warning" in self.messages:
			self.output.mprint('\n'.join(self.messages["warning"]))
	
	def create_parser( self, argv):
		try:
			# Take the first key and check if it is a plugin
			args_add = {}
			args_out = {}
			plugin_options = []
			plugin = None
			parser = None
			for anarg in argv:
				if anarg == '-d':
					args_add['d'] = True
				elif anarg =='--init':
					args_add['init'] = True
					break
				elif anarg == '-n' or anarg == '--nolive':
					args_add['nolive'] = True
				elif anarg =='--load-plugins':
					args_add['load-plugins'] = True
					break
				elif anarg =='--start':
					args_add['start'] = ' '.join(argv[1:])
					# in case no arguments
					if not args_add['start']:
						args_add['start'] = True
					break
				elif anarg =='--connect':
					args_add['connect'] = ' '.join(argv[1:])
					break
				elif anarg =='--remote':
					args_add['remote'] = ' '.join(argv[1:])
					break
				elif anarg =='--subscribe':
					args_add['subscribe'] = ' '.join(argv[1:])
					break
				elif anarg.startswith('-'):
					parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, description='System Central Configuration Tool.', usage='%(prog)s KEY [options]')
					parser.add_argument('--list', nargs='?', metavar='KEY', help='List available keys.')
					parser.add_argument('--dump', action='store', metavar='KEY', nargs='?', help='Dump keys configuration. If [KEY] is omitted then all keys are dumped.')
					parser.add_argument('--load', action='store', metavar='FILENAME', nargs=1, help='Load keys configuration from file.')
					parser.add_argument('--show', nargs='?', metavar='KEY', help='Show key or sub-keys configuration.')
					parser.add_argument('--info', action='store', metavar='KEY', nargs='?', help='Show information for plug-in or group of plug-ins.')
					parser.add_argument('KEY', nargs='?', default='None', help='Name of the key to set. Eg: sys.time.ntp.servers.')
					parser.add_argument('--nolive', '-n', action='store_true', help='Do not proceed to a live configuration of the system.')
					parser.add_argument('-d', action='store_true', help='activate debug mode.')
					parser.add_argument('--bind', nargs=2, metavar=('KEY1','KEY2'), help='Link config of two plug-ins. If one is changed the other is changed also.')
					parser.add_argument('--unbind', nargs=1,metavar='KEY', help='Unlink config of two plugins.')
					tmphelp = 'Show the configuration change history. With an optional changeset ID specified, dumps configuration available at given commit time.'
					parser.add_argument('--history', action='store',metavar='ID', nargs='?', help=tmphelp)
					tmphelp = 'Restore the configuration to a previously saved state. If a changeset ID is specified, then the configuration is restored at the given commit time'
					parser.add_argument('--rollback', action='store',metavar='ID', nargs='?', help=tmphelp)
					break
				elif not anarg.startswith('-'):
					#Argument is a plugin
					key = anarg

					# To be removed !!!!
					pluginsCtl = PluginsControler.Controler()
					
					PluginModule = pluginsCtl.load_plugin(key)
					if PluginModule:
					#if key:
						plugin = key
						command = None
						if len(argv) > 1:
							command= argv[argv.index(key) + 1]
						parser = argparse.ArgumentParser(description='System Central Configuration Tool.')
						parser.add_argument('--nolive', '-n', action='store_true', help='Do not proceed to a live configuration of the system')
						parser.add_argument('-d', action='store_true', help='activate debug mode')
						
						plugin_options = PluginModule.setOptions()
						subparsers = parser.add_subparsers(help='plugin options')
						plugin_parser = subparsers.add_parser(key, help=key+' help')
						## Common options
						key_name = re.sub('.*\.', '', key).title()
						key_name_upper = key_name.upper()
						global_group = plugin_parser.add_argument_group('Common options')
						global_group.add_argument('--info', action='store_true', help='show information about '+key_name+' configuration')
						global_group.add_argument('--view', action='store', metavar="[actual|saved|diff]", nargs=1, help='view '+key_name+' different states setup')
						#global_group.add_argument('--show', action='store_true', help='one line version of \"--view diff\" command')
						#global_group.add_argument('--check', action='store_true', help='check difference between Key configuration and current configuration')
						#global_group.add_argument('-d', action='store_true', help='activate debug mode')
							
						set_opt_to_add = True
						if len(plugin_options) > 0:
							plugin_group = plugin_parser.add_argument_group('Plugin options')
							for an_opt in plugin_options:
								if an_opt['name'] == "--set":
									set_opt_to_add = False
								if len(an_opt['action']) > 0:
									if command and command != an_opt['name'] :
										continue
									if an_opt.has_key('metavar') and an_opt['metavar'] != '':
										if an_opt.has_key('nargs') and an_opt['nargs'] != '':
											plugin_group.add_argument(an_opt['name'], action=an_opt['action'], nargs=an_opt['nargs'], metavar=an_opt['metavar'], help=an_opt['help'])
										else:
											plugin_group.add_argument(an_opt['name'], action=an_opt['action'], metavar=an_opt['metavar'], help=an_opt['help'])
									else:
										if an_opt.has_key('nargs') and an_opt['nargs'] != '':
											plugin_group.add_argument(an_opt['name'], action=an_opt['action'], nargs=an_opt['nargs'], help=an_opt['help'])
										else:
											plugin_group.add_argument(an_opt['name'], action=an_opt['action'], help=an_opt['help'])
						
						if set_opt_to_add:
							global_group.add_argument('--set', metavar=key_name_upper ,action='store', help='set '+key_name+' configuration')
					
					break
			if parser:
				args_out = vars(parser.parse_args())
				if plugin:
					args_out['plugin'] = plugin
			args_out = dict(args_add.items() + args_out.items())
			return args_out
			
		except:
			self.printError()
			return None
			#raise
		
	def parse_cli(self, in_args):
		''' take the command and execute corresponding action  '''
		try:
			plugin = None
			nolive = True
			debug = False
			commands_noargs = ['dump' , 'show', 'list', 'info', 'onectl', 'history', 'rollback' , 'init', 'exchange', 'upload', 'download', 'disable']
			
			if 'plugin' in in_args:
				plugin = in_args['plugin']
				del in_args['plugin']

			if 'd' in in_args:
				if in_args['d']:
					debug = True
				del in_args['d']
			
			if 'nolive' in in_args:
				nolive = in_args['nolive']
				del in_args['nolive']
	
			for action in  in_args:
				if action == 'KEY':
					continue

				data = in_args[action]
			
				#print action, data, type(data)
				if type(data) is bool:
					if not data:
						continue
					data = None
				else:
					if action not in commands_noargs and  not data:
						continue
				# send to onectl
				result, message  = self.cli_command_handle( plugin, action, data, debug, nolive)
				if message:
					self.output.mprint(message)
		except:
			self.printError()
			return None
	
	def cli_command_handle(self, plugin, action, data, debug, nolive):
		try:
			result = 0
			message = None
			if not plugin and action == 'start':
				result = self.onectl_server_start(data)
				return result, message
			#elif action == 'connect':
			#	result = self.remote_client_connect()
			#	return result
			elif not plugin and  action == 'subscribe':
				result = self.remote_client_subscribe(data)
				return result, message
			elif not plugin and action == 'remote':
				result, message = self.remote_client_request(data)
				return result, message
			elif plugin and plugin.startswith('neighbors.conf') and  (action == 'exchange' or action == 'upload' or action == 'download' or action == 'disable'):
				data = self.prompt_password(data)
			
			host = 'localhost'
			# use the default port
			port = None
			result, message = self.cli_send_request(host, port, plugin, action, data, debug,nolive)
			
			return result, message
		except:
			raise
		
	def cli_send_request(self, ip, port, plugin, action, data, debug, nolive):
		try:
			onectlClient = onectlLib.OnectlClient(ip,port)
			onectlClient.connect()
			self.output.debug("Connection to %s %s" %(ip, port))
			self.output.debug("Prepared request to %s %s - plugin %s action %s data %s" %(ip, port, plugin, action, data))
			result, message = onectlClient.request(plugin, action, data, debug, nolive)
			self.output.debug("Reply received from  %s %s - %s" %(ip, port, message))
			onectlClient.disconnect()
			self.output.debug("Disconnected from  %s %s" %(ip, port))
			return result, message
		except:
			raise
		return 0
		
	def remote_client_request(self, data):
		''' Connect to the remote client  '''
	
		try:
			if type(data) is str:
				data_list = data.split(' ')
			
			ip = data_list[0]
			port = data_list[1]
			if data_list[2].startswith('--'):
				action = data_list[2][2:]
				data = data_list[3:]
				plugin = None
			else:
				plugin = data_list[2]
				action = data_list[3][2:]
				data = data_list[4:]
			debug = False
			nolive = False
			# use the default port
			port = None
			result , message = self.cli_send_request(ip, port, plugin, action, data, debug, nolive)
			#if message:
			#	self.output.mprint(message)
			return result , message
		except:
			raise
		
	def remote_client_subscribe(self, data):
		''' Subscribe for change. Input is a list of IPs  '''
		try:
			if type(data) is list:
				subsc_list = data
			elif type(data) is str:
				subsc_list = [data]
			else:
				raise ValueError('Invalid input format for remote_client_subscribe')
			# use the default port
			port = None
			for ip in subsc_list:
				onectlSub = onectlLib.OnectlSubClient()
				onectlSub.run_subscriber(ip, port)
		except:
			raise
		return 0
	
	def onectl_server_start(self, port=None):
		''' Start the server. data  is port  '''
		try:
			Server = onectlServer.OnectlServer(port)
			self.output.debug("Starting server on port %s" %port)
			Server.run_server()
		except:
			raise
		return 0
	
	def prompt_password(self, data):
		try:
			if not data:
			#if not password:
				#self.output.info("Please enter password ")
				password = getpass("Password: ")
				data = [password]
			return data
		except:
			raise
