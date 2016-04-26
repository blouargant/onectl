from includes import xmltodic
import re
import xml.etree.ElementTree as ET

# INI XML paths
XML_INFO = '/plugins/plugin[name={0}]/info'
XML_PLUGIN_FILE = '/plugins/file'
XML_PLUGIN_FILE_TYPE = '/plugins/file_type'


# INI XML PATHS
XML_INI_KEY = '/plugins/plugin[name={0}]/key'
XML_INI_SECTION = '/plugins/plugin[name={0}]/section'
XML_INI_KEY_FORMAT = '/plugins/plugin[name={0}]/input/format'
XML_INI_KEY_SEPARATOR = '/plugins/plugin[name={0}]/input/separator'
XML_INI_KEYTYPE = '/plugins/plugin[name={0}]/input/type'
XML_INI_LIVE = '/plugins/plugin[name={0}]/live'
XML_INI_REGEXP = '/plugins/plugin[name={0}]/input/validation/regexp'
XML_INI_VAL_MIN = '/plugins/plugin[name={0}]/input/validation/min'
XML_INI_VAL_MAX = '/plugins/plugin[name={0}]/input/validation/max'

# XML files
XML_PLUGIN_DESTINATION = '/plugins/destination'
LOG4j_XML_PATH = "appender[@name={0}]/param[@name={1}]"


XML_FILE_TYPES = ['ini', 'service', 'cache', 'log4j']
XML_DYNC_FILE_TYPES = ['log4j']

def get_xml_field_from_dict(dct, path):
	xml_tags = path.strip('/').split('/')
	for tag in xml_tags:
		try:
			if('[' in tag) and (']' in tag):
				# get valuew between []
				match = tag.split('[')[1].split(']')[0]
				tag=tag.split('[',1)[0]
				#get the value to mach key=ivalue @param=value
				key=None
				keyvalue=None
				if re.search("=", match) :
					keys = match.split('=',1)
					key=keys[0]
					keyvalue=keys[1]
				else:
					key=match
				dct  = dct[tag]
				bIsValidKey=False
				if type(dct)is list:
					for entry in dct:
						if keyvalue:
							if (entry[key] == keyvalue):
								dct=entry
								bIsValidKey=True
								break
						elif key in entry:
							dct=entry
							bIsValidKey=True
							break
					if not bIsValidKey:
						return None
			else:
				dct = dct[tag]
		except (KeyError, TypeError):
			return None
	return dct


def create_xml_dict(xml_file_name):
	# open the xml file
	xml_file = open(xml_file_name, "r")
	# take contents
	xml_string = xml_file.read()
	# create dictionary
	xml_dict = xmltodic.parse(xml_string)
	
	return xml_dict

def get_xml_field_from_xmlfile(xml_file_name, tag):
	# get the dictionary
	xml_dict = create_xml_dict(xml_file_name)
	if not xml_dict:
		return None

	# get the value
	res = get_xml_field_from_dict(xml_dict, tag)
	return res

def validatePluginFromXml(xml_file, file_type, plugin_dict):
	''' Validate if xml was correctly writen'''

	if not plugin_dict:
		raise ValueError('Empty plugin in XML %s.Please check documentation' %xml_file)

	if not file_type:
		raise ValueError('Missing file_type in xml ' + xml_file)

	if not 'name' in plugin_dict:
		raise ValueError('Missing plugin name in xml ' + xml_file)

	if not 'info' in  plugin_dict:
			raise ValueError('Missing <info> field for plugin %s in xml %s.Please change the xml and execute onectl -load-plugins' %(plugin_dict['name'], xml_file))

	if file_type not in XML_FILE_TYPES:
		raise ValueError('Unknown filetype %s in xml %s. Valid types: %s' %(file_type,xml_file, ' '.join(XML_FILE_TYPES)))

	if file_type == 'service':
		pass
	elif file_type == 'ini':
		if not 'name' in plugin_dict:
			raise ValueError('Missing plugin name in xml ' + xml_file)

		if not 'key' in  plugin_dict:
			raise ValueError('Missing <key> field for plugin %s in xml %s.Please change the xml and execute onectl -load-plugins' %(plugin_dict['name'], xml_file))
		
		if not 'info' in  plugin_dict:
			raise ValueError('Missing <info> field for plugin %s in xml %s.Please change the xml and execute onectl -load-plugins' %(plugin_dict['name'], xml_file))

		if not 'input' in plugin_dict:
			raise ValueError('Missing <input> field for plugin %s in xml %s.Please change the xml and execute onectl -load-plugins' %(plugin_dict['name'], xml_file))
		else:
			if not 'type' in plugin_dict['input']:
				raise ValueError('Missing <input/type> field for plugin %s in xml %s.Please change the xml and execute onectl -load-plugins' %(plugin_dict['name'], xml_file))
			else:
				input_type = plugin_dict['input']['type']
				if (input_type.lower() != 'list') and (input_type.lower() != 'integer-list') and (input_type.lower() != 'string') and (input_type.lower() != 'integer'):
					raise ValueError('Field <input/type>:%s for plugin %s in xml %s can be one of the following: STRING,INTEGER,LIST,INTEGER-LIST' %(input_type, plugin_dict['name'], xml_file))

				if 'validation' in plugin_dict['input']:
					if not plugin_dict['input']['validation']:
						return
					# in case of a digit
					if (input_type.lower() == 'integer') or (input_type.lower() == 'integer-list'):
						if 'min' in plugin_dict['input']['validation']:
							min_check = plugin_dict['input']['validation']['min']
							if min_check is not None:
								if not re.match("^-?\d*\.{0,1}\d+$", min_check):
									raise ValueError('Field <input/validation/min>:%s for plugin %s in xml %s should be a digit' %(min_check, plugin_dict['name'], xml_file))
							if 'max' in plugin_dict['input']['validation']:
								max_check = plugin_dict['input']['validation']['max']
								if max_check is not None:
									if not re.match("^-?\d*\.{0,1}\d+$", max_check):
										raise ValueError('Field <input/validation/max>:%s for plugin %s in xml %s should be a digit' %(max_check, plugin_dict['name'], xml_file))
					else:
						if 'min' in plugin_dict['input']['validation']:
							 raise ValueError('Field validation/min in plugin %s in xml %s can be used with input/type INTEGER or INTEGER-LIST only' %(plugin_dict['name'], xml_file))
				
						if 'max' in plugin_dict['input']['validation']:
							raise ValueError('Field validation/max in plugin %s in xml %s can be used with input/type INTEGER or INTEGER_LIST only' %(plugin_dict['name'], xml_file))

# XML plugin element object


def get_log4j_plugins_tocreate(xml_file_name, tag):
	tree = ET.parse(xml_file_name)
	root = tree.getroot()
	elems = root


	res_list = {}
	for parent in root.findall('appender'):
		parent_name = parent.attrib['name']
		child_list = []
		for child in parent.findall('param'):
			child_name = child.attrib['name']

			child_list.append(child_name)
		#child_list = get_attrib_list(parent,param,attrib)

		if child_list:
			res_list[parent_name]=child_list

	return res_list

def get_xml_tag_values(tag):
	param=None
	arrib=None
	attribvalue=None
	if('[' in tag) and (']' in tag):
		# get valuew between []
		match = tag.split('[')[1].split(']')[0]
		param=tag.split('[',1)[0]
		#get the value to mach key=value @param=value
		attribs = match.split('=',1)
		attrib=attribs[0]
		if attrib.startswith('@'):
			attrib = attrib.strip('@')
			attribvalue=attribs[1]
		else:
			attrib = attribs[0]
			attribvalue=attribs[1]
	else:
			param=tag
	
	return param, attrib, attribvalue

def get_element_tree_elem( elems, tag):
	''' get element from tree '''
	try:
		
		param, attrib, attribvalue = get_xml_tag_values(tag)

		out_list = []
		if param and attrib and attribvalue:
			out_list = []
			for elem in elems:
				if attrib:
					if attribvalue and attribvalue == elem.get(attrib,None):
						out_list=elem
		#elif param and attrib:

		elif param:
			out_list = elems.findall(param)

		return out_list
	except:
		raise

def get_elem_tree(xml_file, path):
	try:
		tags = path.split('/')
		
		tree = ET.parse(xml_file)
		root = tree.getroot()
		#elems = root.findall(param)
	
		elems=[]
		for tag in tags:
			if not elems:
				param, attrib, attribvalue = get_xml_tag_values(tag)
				elems = root.findall(param)
			elems = get_element_tree_elem(elems,tag)
	
		return tree,elems
	except:
		raise

def get_xml_elem_value(xml_file, path, attrib):
	''' Get attribute from xml file and path'''
	try:
		tree, elem = get_elem_tree(xml_file, path)
		if attrib:
			return elem.get(attrib,None)
		else:
			return elem
	except:
		raise

def set_xml_elem_value(xml_file, path, attrib, new_value):
	''' Set attribute from xml file and  path  '''
	try:
	
		tree, elem = get_elem_tree(xml_file, path)
		if attrib:
			elem.attrib['value']=new_value
			tree.write(xml_file)
	except:
		raise
	
