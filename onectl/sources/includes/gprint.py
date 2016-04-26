#!/usr/bin/python -u


class GraphicalPrinter:

	def __init__(self):	
		self.debug = False
		self.DEBUG = '\033[90m'
		self.HEADER = '\033[95m'
		self.OKBLUE = '\033[94m'
		self.OKGREEN = '\033[92m'
		self.WARNING = '\033[93m'
		self.FAIL = '\033[91m'
		self.ENDC = '\033[0m'
		self.BOLD = "\033[1m"
		self.ITALIC= "\033[3m"
		self.UNDERLINE = "\033[4m"
		self.BLINK = "\033[5m"
	
	
	def disable(self):
		self.HEADER = ''
		self.OKBLUE = ''
		self.OKGREEN = ''
		self.WARNING = ''
		self.FAIL = ''
		self.ENDC = ''
		
	def fail(self, msg):
		return self.HEADER + msg + self.ENDC
	
	def info(self, msg):
		return msg
	
	def ok(self, msg):
		return self.OKGREEN + msg + self.ENDC
	
	def i_ok(self, msg):
		return self.ITALIC + self.OKGREEN + msg + self.ENDC
	
	def ital(self, msg):
		return self.ITALIC + msg + self.ENDC
	
	def title(self, msg):
		return self.OKBLUE + msg + self.ENDC
	
	def warn(self, msg):
		return self.WARNING + "Warning: " + msg + self.ENDC
	
	def warn_debug(self, msg):
		if self.debug:
			return self.WARNING + "Debug: " + msg + self.ENDC
		else:
			return None
	
	def err(self, msg):
		return self.FAIL + "Error: " + msg + self.ENDC
	
	#def debug(self, msg):
	#		print self.DEBUG + msg + self.DEBUG
	
	def help(self, header, opts):
		msg = self.title(header)
		msg = msg + '\n' +self.ok(opts)
		return msg


class OnectlPrinter:
	def __init__(self, gprint, msgDic):
		self.printer = gprint
		self.msgDic = msgDic
		self.msgDic["info"] = []
		self.msgDic["error"] = []
		self.msgDic["warning"] = []
		self.msgDic["debug"] = []
		self.msgDic["output"] = []
	
		self.show_warnings = True
		self.enable_output = True

	def clear_messages(self, bOutput=False):
		''' Clear messages dictionary. If bOutput is set clear output '''
		self.msgDic["info"] = []
		self.msgDic["error"] = []
		self.msgDic["warning"] = []
		self.msgDic["debug"] = []
		if bOutput:
			self.msgDic["output"] = []
	
	def title(self, msg):
		if self.enable_output and self.show_warnings:
			msg = self.printer.title(msg)
			self.msgDic["output"].append(msg)
	
	def info(self, msg):
		self.msgDic["info"].append(msg)
		if self.enable_output :
			msg = self.printer.info(msg)
			self.msgDic["output"].append(msg)
	
	def error(self, msg):
		#self.msgDic["error"].append(msg)
		if self.enable_output :
			msg = self.printer.err(msg)
			self.msgDic["output"].append(msg)
		self.msgDic["error"].append(msg)
		

	def warning(self, msg):
		#self.msgDic["warning"].append(msg)
		if self.enable_output and self.show_warnings:
			msg = self.printer.warn(msg)
			self.msgDic["output"].append(msg)
		self.msgDic["warning"].append(msg)
	
	def debug(self, msg):
		self.msgDic["debug"].append(msg)
		if self.enable_output :
			msg = self.printer.warn_debug(msg)
			if msg:
				self.msgDic["output"].append(msg)

	def warn_debug(self, msg):
		msg = self.printer.warn_debug(msg)
		if msg:
			self.msgDic["output"].append(msg)

	def help(self, title, msg):
		if self.enable_output :
			msg = self.printer.help(title, msg)
			self.msgDic["output"].append(msg)
		
	def fail(self, msg):
		if self.enable_output :
			msg = self.printer.ital(msg)
			self.msgDic["error"].append(msg)
			self.msgDic["output"].append(msg)


	def i_ok(self, msg):
		msg = self.printer.i_ok(msg)
		self.msgDic["output"].append(msg)
		
	def enable(self):
		self.enable_output = True
	
	def disable(self):
		self.enable_output = False
	
	def mprint(self, msg):
		print msg


