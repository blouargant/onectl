import os,hashlib,time,sys

def get_file_md5(file, block_size=2**20):
	try:
		f=open(file,'r')
		md5 = hashlib.md5()
		for chunk in iter(lambda: f.read(8192), b''):
			md5.update(chunk)
		f.close()
		return md5.hexdigest()
	except:
		return None


def create_hash_file(dir,hash_file_name):
	file_handle = open(hash_file_name, "w+")
	for path, subFolders, files in os.walk(dir):
		for file in files:
			hash = get_file_md5(os.path.join(path,file))
			file_handle.write(hash+","+os.path.join(os.path.abspath(path),file+"\n"))
	file_handle.close()

