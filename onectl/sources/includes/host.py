import paramiko
import pwd, os

def remote_host_connect(host, username, password):
	''' open connection to host/close it after use '''
	try:
		ssh_client = paramiko.SSHClient()
		ssh_client.load_system_host_keys()
		ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		try:
			ssh_client.connect(host, username=username, timeout=1)
		except:
			ssh_client.connect(host, username=username, password=password)
		return ssh_client
	except:
		raise

def _get_password(data):
	''' get the password from input '''
	try:
		if not data:
			return None
		
		if type(data) is list:
			data_list = data
		elif type(data) is str:
			# in case a list of values
			data_list = data.split()
		else:
			data_list.append(data)
			
		if data_list:
			password = data_list[0]
		else:
			password = None
		return password
	except:
		raise
		
def getlogin():
	return pwd.getpwuid(os.getuid()).pw_name
	
