#!/usr/bin/python -u
""" 
Send requests to onectl server 
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
import paramiko
from multiprocessing import Process
import getconfig

class OnectlClient:
	def __init__(self, ip, port=None , debug=False):
		self.ip = ip
		confPort, subPort = getconfig.get_ports()
		self.port = port or confPort
		self.context = None
		self.socket = None
		
	def _get_socket(self):
		''' get the socket from for an IP '''
		socket = self.socket
		return socket
		
	def _set_socket(self, socket):
		''' save the socket per type '''
		#self.connections[ip] = {type:socket}
		self.socket = socket
		
	def connect(self, passw = None):
		''' Connect to a remote host '''
		try:
			#if not port:
			ip = self.ip
			port = self.port
			
			if not self.context:
				self.context = zmq.Context()
			if not self.socket:
				socket = self.context.socket(zmq.REQ)
				socket.setsockopt(zmq.LINGER, 0)
				#self.socket = socket
				self._set_socket(socket)
			else:
				socket = self.socket
			#for port in ports:
			server = "tcp://%s:%s" %(ip, port)
			if ip == 'localhost' or ip == '127.0.0.1':
				socket.connect(server)
			else:
				ssh_server = ip
				if not passw:
					tunnel = ssh.tunnel_connection(socket, server, ssh_server, paramiko=True, timeout=5)
				else:
					tunnel = ssh.tunnel_connection(socket, server, ssh_server, password = passw, paramiko=True, timeout=5)
		except:
			raise
		return 0
		
	def disconnect(self):
		try:
			#	port = self.port
			#  disconnect
			self.socket.close();
			self.context.term();
		except:
			raise
		return 0
		
	def request(self, plugin, action, data, debug, nolive):
		''' Request information 
			action is the command to execute
			plugin - can be None for not plugin requests
			data - data provided for the action. Data is string. If multiple values 
			separation is space
			all parameters are passed as strings
		'''
		try:
			#if not port:
			ip = self.ip
			port = self.port
			
			message = self.encode_message(plugin, action, data, debug, nolive)
			self.send_request(ip, port, message)
			message = self.recv_request(ip, port)
			result, output = self.get_result(message)
			return result, output
		except:
			raise
		
	def get_result(self, json_message):
		try:
			output = None
			result = None
			res_dct = self.decode_message(json_message)
			if 'data' in res_dct:
				output = res_dct['data']
			if 'result' in res_dct:
				result = res_dct['result']
			return result, output
		except:
			raise

	def send_request(self, ip, port, message):
		''' Send request on a host '''
		
		try:
			socket = self._get_socket()
			if socket:
				#print "Sending request ", message
				socket.send(message)
			else:
				raise ValueError('No connection established to %s' %ip)
		except:
			raise
		return 0
		
	def recv_request(self, ip, port):
		''' Receive a message . Return the message '''
		try:
			socket = self._get_socket()
			if socket:
				message = socket.recv()
				#print "Received reply %s" %(message)
			else:
				raise ValueError("No connection established to %s" %ip)
			return message
		except:
			raise
		
	def encode_message(self, plugin, action, data, debug, nolive):
		''' Create a message for getting informationm '''
		try:
			msg_dict={}
			msg_dict['plugin'] = plugin
			msg_dict['action'] = action
			msg_dict['data'] = data
			msg_dict['debug'] = debug
			msg_dict['nolive'] = nolive
			
			output = self.encode_message_from_dct(msg_dict)
			return output
		except:
			raise
		
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
			return msg_dict
		except:
			raise
		
		
class OnectlSubClient:
	def __init__(self ,debug=False):
		#self.ip = ip
		self.context = None
		self.socket = None
	
	def _get_socket(self):
		''' get the socket from for an IP '''
		socket = self.socket 
		return socket
		
	def _set_socket(self,socket):
		''' save the socket per type '''
		self.socket = socket
		
	def run_subscriber(self, ip, port):
		''' Run the server on the specified port  '''
		
		try:
			self.subscribe(ip, port)
		except:
			raise
		return 0
		
	# Subscribe for evens
	def subscribe(self, ip, port):
		''' Subscribe to receive events to a node'''
		try:
			if not port:
				confPort, subPort = getconfig.get_ports()
				port = subPort
			if not self.context:
				self.context = zmq.Context()
			if not self.socket:
				socket = self.context.socket(zmq.SUB)
				self._set_socket(socket)
			server = "tcp://%s:%s" %(ip, port)
			socket.connect (server)
			socket.setsockopt(zmq.SUBSCRIBE,'')
			while True:
				message = socket.recv()
				print message
				# can connect to several hosts
		except:
			raise
		return 0
			
	def unsubcribe(self, ip, port):
		try:
			if not port:
				confPort, subPort = getconfig.get_ports()
				port = subPort
			server = "tcp://%s:%s" %(ip, port)
			self.socket.disconnect(server)
		except:
			raise
		return 0

