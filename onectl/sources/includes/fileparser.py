import re,os

def find_section (file_lines, section,line):
	for line, aline in enumerate(file_lines[line:],start=line):
		if re.search("^ *#", aline) or re.search("^ *!", aline) or re.search("^ *;", aline):
			continue
		if section in aline:
			return line
	return None
	
def get_section_pos(file_lines, section_path):
		
	#serch position in the file
	line=0
	
	if section_path:
		# find the nested sections if any
		sections = section_path.split('/')
		sect_str='{0}'
		nested_sections = []
		#get a list of the nested sections
		for item in sections:
			if not item:
				continue
			sect_str = '[' + sect_str + ']'
			nested_sections.append(sect_str.format(item))
			
		# find if all the sections are present and return the line of the last one
		for section in nested_sections:
			line = find_section (file_lines, section, line)
			if line is None:
				return None
		
		
	return line
		
def get_key(config_file, section, key, key_separator, data_separator):
	''' Get the current config in a list  '''
	if not os.path.exists(config_file):
		raise ValueError('File ' + config_file + ' doest not exist')
	
	# read the ini file
	file_config = open(config_file, 'r')
	file_lines = file_config.readlines()
	file_config.close()
	
	#find the possition of the section and continue search of the key
	line = 0
	if section:
		line = get_section_pos(file_lines, section)
		if line is None:
			raise ValueError('Section specified %s does not exist in file %s' %(section, config_file))
		#get the next position
		line+=1
		
	out_list = []
	for line, aline in enumerate(file_lines[line:],start=line):
		# if a comment skip
		if re.search("^ *#", aline) or re.search("^ *!", aline) or  re.search("^ *;", aline):
			continue
		
		aline = aline.strip()
		if not aline:
			continue
		
		# new section reached and exit
		if section:
			if re.search("^ *\s*\[", aline):
				break
		
		# if key found add to oupput list
		if key:
			if re.search(r'\b%s\b' %key,aline):
				config_args = aline.split(key_separator, 1)
				if not config_args:
					continue
				if key in config_args[0]:
					key_value_str = config_args[1]
					if key_value_str:
						out_list += key_value_str.split(data_separator)
		else:
			# the whole line is taken. Change the separator with =.The input
			# was like that
			config_args = aline.split(key_separator, 1)
			if not config_args:
				continue
			aline = config_args[0]+'='+config_args[1].strip()
			out_list.append(aline)
	return out_list
	
def verify_bulk_data(data, bulk_separator):
	data_list = []
	if type(data) is list:
		data_list = data
	else:
		data_list.append(data)
	
def set_key(config_file, section, key, key_separator, data, data_separator):
	
	if not data_separator:
		data_separator = ' '
	
	data_list = []
	
	# This flag show if the like should be commented
	bDisable = False
	# If there is no imput data then the value to set is empty
	if data:
		if type(data) is list:
			data_list = data
		else:
			data_list.append(data)
	
		# add the new data_list as a string
		new_val_str = data_separator.join(data_list)
	else:
		new_val_str = ''
		bDisable = True
	# keeps output config to be written to the config file
	output_file = []
	# read the conf file
	file_lines = open(config_file, 'r').readlines()
	
	#if there is section get the position
	line_num = 0
	sect_ident = ''
	if section:
		line_num = get_section_pos(file_lines, section)
		if line_num is None:
			raise ValueError('Section '+ section + 'not found in file '+ config_file)
		#get the section identation
		sect_ident = file_lines[line_num].split('[',1)[0]
		#start from the next line
		line_num += 1
		output_file = file_lines[0:line_num]
		
	bIsAdded = False
	# read the conf file and skip all lines where server is configured
	for line_num, line in enumerate(file_lines[line_num:],start=line_num):
		# skip the comments
		if re.search("^ *#", line) or re.search("^ *!", line) or  re.search("^ *;", line):
			if bDisable or  not re.search(r'\b%s\b' %key,line):
				output_file.append(line)
				continue
			
		if section:
			# if new section is starting copy the rest and exit
			if re.search("^ *\s*\[", line):
				# if new section is reached and no entry found for key add new line
				if not bIsAdded and not bDisable:
					output_file.append(sect_ident+key + key_separator + new_val_str + '\n')
					bIsAdded = True
				output_file = output_file + file_lines[line_num:]
				break
		if key:
			if re.search(r'\b%s\b' %key,line):
				if not bIsAdded:
					#new_val_str = re.sub('(?<={0})(.*)'.format(key_separator),new_val_str,line)
					new_val_str = sect_ident+key + key_separator + new_val_str + '\n'
					if bDisable:
						new_val_str = '; '+ new_val_str
					output_file.append(new_val_str)
					bIsAdded = True
			else:
				output_file.append(line)
		else:
			output_file.append(line)
		
	# if the new value was not added add at the end
	if not bIsAdded and not bDisable:
		output_file.append(sect_ident+key + key_separator + new_val_str + '\n')
		
	# write the new config
	open(config_file, 'w').writelines(output_file)
	
	out_str = '\n'.join(data_list)
	return out_str
	
def set_bulk(config_file, section, key_separator, data, data_separator):
	''' Set whole lines in the file. In command a list is entered in the form
	key=value key=value'''
	new_val_conf = ''
		
	if not data_separator:
		data_separator = ' '
		
	key_separator = ' '
	bulk_separator = '='
		
	data_list = []
	if type(data) is list:
		data_list = data
	else:
		data_list.append(data)
		
	# keeps output config to be written to the config file
	output_file = []
	# read the conf file
	file_lines = open(config_file, 'r').readlines()
		
	if section:
		line_num = get_section_pos(file_lines, section)
		if line_num is None:
			raise ValueError('Section '+ section + 'not found in file '+ config_file)
		#get the section identation
		sect_ident = file_lines[line_num].split('[',1)[0]
		#start from the next line
		line_num += 1
		output_file = file_lines[0:line_num]
		
	bIsAdded = False
	for line_num, line in enumerate(file_lines[line_num:],start=line_num):
			# skip the comments
		if re.search("^ *#", line) or re.search("^ *!", line) or  re.search("^ *;", line):
			output_file.append(line)
			continue
			
		if section:
			# if new section is starting copy the rest and exit
			if re.search("^ *\s*\[", line):
				# if new section is reached and no entry found for key add new line
				if not bIsAdded:
					for adata in data_list:
						if re.search(bulk_separator, adata):
							key, value = adata.split(bulk_separator, 1)
							output_file.append('%s%-35s%s%s\n' %(sect_ident, key, key_separator, value))
					output_file.append('\n')
					output_file = output_file + file_lines[line_num:]
					bIsAdded = True
				break
		else:
			output_file.append(line)
			
	if not bIsAdded:
		for adata in data_list:
			if re.search('=', adata):
				key, value = adata.split('=', 1)
				output_file.append('%s%-35s%s%s\n' %(sect_ident, key, key_separator, value))
		output_file = output_file + file_lines[line_num+1:]
				
	open(config_file, 'w').writelines(output_file)
	out_str = '\n'.join(data_list)
	return out_str


