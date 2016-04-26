#!/usr/bin/python -u
""" 
Run onectl service that answers requests 
"""

import sys
import subprocess
import threading
import os
import json
import re
import time
import zmq
from zmq import ssh
from multiprocessing import Process
import PluginsControler
import getconfig

class OnectlServer:
	def __init__(self, port = None, debug=False):
		try:
			self.port=port
			self.context = None
			self.socket = None
			self.pluginsCtl = PluginsControler.Controler()
			self.pluginsCtl.get_config("/etc/onectl/onectl.conf")
			self.pluginsCtl.load_hooks()
			self.pluginsCtl.load_xml_plugins()
			confPort, subPort = getconfig.get_ports(self.pluginsCtl.configDic)
			if not self.port:
				self.port = confPort
		
			# run the substription server
			self.pluginsCtl.subServer = OnectlSubServer(subPort)
			self.pluginsCtl.subServer.start()
		except:
			raise
	
	def _get_socket(self):
		''' get the socket from for an IP '''
		self.socket = socket
		return socket
		
	def _set_socket(self, socket):
		''' save the socket per type '''
		self.socket = socket
		#self.connections[ip] = {type:socket}
		
	def server(self, port):
		""" start server listening to requests """
		try:
			if not self.context:
				self.context=zmq.Context()
				
			if not self.socket:
				socket = self.context.socket(zmq.REP)
				socket.setsockopt(zmq.LINGER, 0)
				socket.bind("tcp://*:%s" % port)
				self.socket = socket
			else:
				socket = self.socket
			
			#print "Starting server on port: %s" %port
			while True:
				message = socket.recv()
				req_dict = self.decode_message(message)
				res_dct = self.handle_requests(req_dict)
				result_message = self.encode_message_from_dct(res_dct)
				socket.send(result_message)
		except:
			raise
			
		return 0
		
	def handle_requests(self, req_dict):
		''' plugin action data 
		input - dictionary with keys plugin, action,data
		return - dictionary with output in data'''
		try:
			plugin = None
			action = None
			data = None
			debug = None
			nolive = None
			# from encode_message
			if 'plugin' in req_dict:
				plugin = req_dict['plugin']
			if 'action' in req_dict:
				action = req_dict['action']
			if 'data' in req_dict:
				data = req_dict['data']
			if 'debug' in req_dict:
				debug = req_dict['debug']
			if 'nolive' in req_dict:
				nolive = req_dict['nolive']
			
			pluginsCtl = self.pluginsCtl
			result, messages = pluginsCtl.execute_action(plugin, action, data, debug, nolive)
			req_dict['data'] = '\n'.join(messages)
			req_dict['result'] = result
			return req_dict
		except:
			raise
		
		return None
		
	def run_server(self):
		''' Run the server on the specified port  '''
		
		try:
			# if port i snot specified use the default port
			#if not port:
			port = self.port
			
			#serverR = Process(target=self.server,args=(port,))
			#serverR.start()
			
			self.server(port)
			#port = 3333
		#	serverP = Process(target=self.server_publisher,args=(port,))
		#	serverP.start()
		except:
			raise
		return 0
		
	def stop_server(self):
		socket.close()
		self.context.term()
		self.pluginsCtl.subServer.stop()
		return 0
		
	def encode_message_from_dct(self, msg_dict):
		''' Create a message for getting informationm '''
		try:
			output = json.dumps(msg_dict)
			return output
		except:
			raise
		
	def decode_message(self, json_message):
		''' Turn json to dict '''
		try:
			msg_dict = json.loads(json_message)
			if type(msg_dict['data']) is list:
				msg_dict['data'] = [s.encode('utf-8') for s in msg_dict['data']]
			else:
				if msg_dict['data']:
					msg_dict['data'] = str(msg_dict['data'])
	
			return msg_dict
		except:
			raise
		
		
class OnectlSubServer:
	def __init__(self, port, debug=False):
		self.context = None
		self.socket = None
		if not port:
			confPort, subPort = getconfig.get_ports()
			self.subs_port = subPort
		else:
			self.subs_port = port
		
	def _get_socket(self):
		''' get the socket from for an IP '''
		socket = self.socket 
		return socket
		
	def _set_socket(self, socket):
		''' save the socket per type '''
		#self.connections[ip] = {type:socket}
		self.socket = socket
		
	def start(self):
		""" start server listening to requests """
		try:
			#if not port:
			port = self.subs_port
			if not self.context:
				self.context = zmq.Context()
			if not self.socket:
				socket = self.context.socket(zmq.PUB)
				socket.bind("tcp://*:%s" % port)
				self._set_socket(socket)
		except:
			raise
		
		return 0
		
	def stop(self):
		self.socket.close()
		self.context.term()
		return 0
		
	def send_event(self, data):
		''' data is a list of changed plugins  '''
		try:
			port = self.subs_port
			context = self.context
			socket = self.socket
			message = self.encode_message_from_dct(data)
			time.sleep(1)
			if socket:
				#socket.send_json(work_message)
				#socket.send(message, zmq.NOBLOCK)
				socket.send(message)
			else:
				raise ValueError("No service listening to evens" )
		except:
			if socket:
				socket.close()
		
	def encode_message_from_dct(self, msg_dict):
		''' Create a message for getting informationm '''
		
		try:
			output = json.dumps(msg_dict)
			return output
		except:
			raise
		
