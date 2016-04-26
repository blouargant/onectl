import re
import os

def load_config_file(configFile):
	''' Read the config file and save to dict '''
	debug = False
	localpath = re.sub('onectl.*', 'onectl/', os.path.realpath(__file__))
	configDic = {}
	configDic["log"] = "/var/log/onectl.log"
	configDic["debug"] = False
	configDic["data_path"] = localpath+"data/onectl.data"
	configDic["bind_path"] = localpath+"data/bind"
	configDic["repo_path"] = localpath+"data"
	configDic["backup_path"] = localpath+"data/backup.data"
	try:
		if os.path.exists(configFile):
			fconfig = open(configFile, 'r')
			config_lines = fconfig.readlines()
			fconfig.close()
			for aline in config_lines:
				if not re.search("^ *#", aline) and re.search("=", aline):
					config_args = aline.split('=')
					key = config_args[0]
					value = config_args[1].strip()
					if "log_file" in key:
						configDic["log"] = value
					if "data_path" in key:
						configDic["data_path"] = value
					if "bind_path" in key:
						configDic["bind_path"] = value
					if "repo_path" in key:
						configDic["repo_path"] = value
					if "debug" in key:
						configDic["debug"] = value
					if "onectl_port" in key:
						configDic["server_port"] = value
					if "onectl_sub_port" in key:
						configDic["server_sub_port"] = value
	
	except:
		raise
	
	return configDic
	
def get_ports(configDic = None):
	''' Get the ports from /etc/onectl/onectl.conf  
		If no difctionary is passed it is created
	'''
	confPort = None
	subPort = None
	
	try:
		if not configDic:
			configDic = load_config_file("/etc/onectl/onectl.conf")
		
		if "server_port" in configDic:
			confPort = configDic["server_port"]
	
		if "server_sub_port" in configDic:
			subPort = configDic["server_sub_port"]
	
		if not confPort:
			raise ValueError("Server ONECTL port not configured. Please add onectl_port = PORT in /etc/onectl/onectl.conf")
	
		if not subPort:
			raise ValueError("Server subscribe port not configured. Please add onectl_sub_port = PORT in /etc/onectl/onectl.conf")
	except:
		raise
	return confPort, subPort

