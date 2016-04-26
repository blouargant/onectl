import fcntl
import os
import re
import socket
import struct
import ctypes
import array
import math
import sys
import subprocess

"""
This file makes the following assumptions about data structures:

struct ifreq
{
	union
	{
		char	ifrn_name[16];
	} ifr_ifrn;

	union {
		struct	sockaddr ifru_addr;
		struct	sockaddr ifru_dstaddr;
		struct	sockaddr ifru_broadaddr;
		struct	sockaddr ifru_netmask;
		struct	sockaddr ifru_hwaddr;
		short	 ifru_flags;
		int	   ifru_ivalue;
		int	   ifru_mtu;
		struct	ifmap ifru_map; // 16 bytes long
		char	  ifru_slave[16];
		char	  ifru_newname[16];
		void __user *	ifru_data;
		struct	if_settings ifru_settings;
	} ifr_ifru;
};

typedef unsigned short sa_family_t;

struct sockaddr {
	sa_family_t  sa_family;
	char		 sa_data[14];
};

struct ifconf {
	int				 ifc_len; /* size of buffer */
	union {
		char		   *ifc_buf; /* buffer address */
		struct ifreq   *ifc_req; /* array of structures */
	};
};


// From linux/ethtool.h

struct ethtool_cmd {
	__u32   cmd;
	__u32   supported;	  /* Features this interface supports */
	__u32   advertising;	/* Features this interface advertises */
	__u16   speed;		  /* The forced speed, 10Mb, 100Mb, gigabit */
	__u8	duplex;		 /* Duplex, half or full */
	__u8	port;		   /* Which connector port */
	__u8	phy_address;
	__u8	transceiver;	/* Which transceiver to use */
	__u8	autoneg;		/* Enable or disable autonegotiation */
	__u32   maxtxpkt;	   /* Tx pkts before generating tx int */
	__u32   maxrxpkt;	   /* Rx pkts before generating rx int */
	__u32   reserved[4];
};

struct ethtool_value {
	__u32	cmd;
	__u32	data;
};
"""


SYSFS_NET_PATH = "/sys/class/net"
PROCFS_NET_PATH = "/proc/net/dev"

# From linux/sockios.h
SIOCGIFNAME = 0x8910		# get iface name			#
SIOCSIFLINK = 0x8911		# set iface channel			#
SIOCGIFCONF = 0x8912		# get iface list			#
SIOCGIFFLAGS = 0x8913		# get flags					#
SIOCSIFFLAGS = 0x8914		# set flags					#
SIOCGIFADDR = 0x8915		# get PA address			#
SIOCSIFADDR = 0x8916		# set PA address			#
SIOCGIFDSTADDR = 0x8917		# get remote PA address		#
SIOCSIFDSTADDR = 0x8918		# set remote PA address		#
SIOCGIFBRDADDR = 0x8919		# get broadcast PA address	#
SIOCSIFBRDADDR = 0x891a		# set broadcast PA address	#
SIOCGIFNETMASK = 0x891b		# get network PA mask		#
SIOCSIFNETMASK = 0x891c		# set network PA mask		#
SIOCGIFMETRIC = 0x891d		# get metric				#
SIOCSIFMETRIC = 0x891e		# set metric				#
SIOCGIFMEM = 0x891f			# get memory address (BSD)	#
SIOCSIFMEM = 0x8920			# set memory address (BSD)	#
SIOCGIFMTU = 0x8921			# get MTU size				#
SIOCSIFMTU = 0x8922			# set MTU size				#
SIOCSIFNAME = 0x8923		# set interface name 		#
SIOCSIFHWADDR = 0x8924		# set hardware address 		#
SIOCGIFENCAP = 0x8925		# get/set encapsulations 	#
SIOCSIFENCAP = 0x8926		
SIOCGIFHWADDR = 0x8927		# Get hardware address		#
SIOCGIFSLAVE = 0x8929		# Driver slaving support	#
SIOCSIFSLAVE = 0x8930
SIOCADDMULTI = 0x8931		# Multicast address lists	#
SIOCDELMULTI = 0x8932
SIOCGIFINDEX = 0x8933		# name -> if_index mapping	#
SIOGIFINDEX = SIOCGIFINDEX	# misprint compatibility 	#
SIOCSIFPFLAGS = 0x8934		# set/get extended flags set#
SIOCGIFPFLAGS = 0x8935
SIOCDIFADDR = 0x8936		# delete PA address			#
SIOCSIFHWBROADCAST = 0x8937	# set hardware broadcast add#
SIOCGIFCOUNT = 0x8938		# get number of devices 	#

SIOCGIFBR = 0x8940			# Bridging support			#
SIOCSIFBR = 0x8941			# Set bridging options 		#
SIOCETHTOOL = 0x8946

# From linux/if.h
IFF_UP	   = 0x1
IFF_MASTER = 0x400      	# master of a load balancer 		#
IFF_SLAVE = 0x800        	# slave of a load balancer  		#
IFF_SLAVE_INACTIVE = 0x4 	# bonding slave not the curr. active#
IFF_MASTER_8023AD = 0x8 	# bonding master, 802.3ad.     		#
IFF_MASTER_ALB = 0x10		# bonding master, balance-alb. 		#
IFF_BONDING = 0x20			# bonding master or slave  			#
IFF_MASTER_ARPMON = 0x100	# bonding master, ARP mon in use 	#



# From linux/socket.h
AF_UNIX	  = 1
AF_INET	  = 2

# From linux/ethtool.h
ETHTOOL_GSET = 0x00000001 # Get settings
ETHTOOL_SSET = 0x00000002 # Set settings
ETHTOOL_GLINK = 0x0000000a # Get link status (ethtool_value)
ETHTOOL_SPAUSEPARAM = 0x00000013 # Set pause parameters.

ADVERTISED_10baseT_Half = (1 << 0)
ADVERTISED_10baseT_Full =(1 << 1)
ADVERTISED_100baseT_Half = (1 << 2)
ADVERTISED_100baseT_Full = (1 << 3)
ADVERTISED_1000baseT_Half = (1 << 4)
ADVERTISED_1000baseT_Full = (1 << 5)
ADVERTISED_Autoneg = (1 << 6)
ADVERTISED_TP = (1 << 7)
ADVERTISED_AUI = (1 << 8)
ADVERTISED_MII = (1 << 9)
ADVERTISED_FIBRE = (1 << 10)
ADVERTISED_BNC = (1 << 11)
ADVERTISED_10000baseT_Full = (1 << 12)

# This is probably not cross-platform
SIZE_OF_IFREQ = 40

# From linux/sockios.h
SIOCGIFVLAN = 0x8982
SIOCSIFVLAN = 0x8983

# From linux/if_vlan.h
ADD_VLAN_CMD = 0
DEL_VLAN_CMD = 1
SET_VLAN_INGRESS_PRIORITY_CMD = 2
SET_VLAN_EGRESS_PRIORITY_CMD = 3
GET_VLAN_INGRESS_PRIORITY_CMD = 4
GET_VLAN_EGRESS_PRIORITY_CMD = 5
SET_VLAN_NAME_TYPE_CMD = 6
SET_VLAN_FLAG_CMD = 7
GET_VLAN_REALDEV_NAME_CMD = 8
GET_VLAN_VID_CMD = 9

# bonding calls #
SIOCBONDENSLAVE = 0x8990		# enslave a device to the bond #
SIOCBONDRELEASE = 0x8991		# release a slave from the bond#
SIOCBONDSETHWADDR = 0x8992		# set the hw addr of the bond  #
SIOCBONDSLAVEINFOQUERY = 0x8993	# rtn info about slave state   #
SIOCBONDINFOQUERY = 0x8994		# rtn info about bond state    #
SIOCBONDCHANGEACTIVE = 0x8995	# update to a new active slave #

# bridge calls #
SIOCBRADDBR = 0x89a0			# create new bridge device     #
SIOCBRDELBR = 0x89a1			# remove bridge device         #
SIOCBRADDIF = 0x89a2			# add interface to bridge      #
SIOCBRDELIF = 0x89a3			# remove interface from bridge #


class Interface():
	''' Class representing a Linux network device. '''

	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sockfd = self.sock.fileno()

	def __del__(self):
		self.sock.close()

	def __repr__(self):
		return "<%s %s at 0x%x>" % (self.__class__.__name__, device, id(self))
	
	def set_device_flag(self, device, FLAG):
		# Get existing device flags
		ifreq = struct.pack('16sh', device, 0)
		flags = struct.unpack('16sh', fcntl.ioctl(self.sockfd, SIOCGIFFLAGS, ifreq))[1]

		# Set FLAG
		flags = flags | FLAG
		ifreq = struct.pack('16sh', device, flags)
		fcntl.ioctl(self.sockfd, SIOCSIFFLAGS, ifreq)
	
	def unset_device_flag(self, device, FLAG):
		# Get existing device flags
		ifreq = struct.pack('16sh', device, 0)
		flags = struct.unpack('16sh', fcntl.ioctl(self.sockfd, SIOCGIFFLAGS, ifreq))[1]

		# Unset FLAG
		flags = flags & ~FLAG
		ifreq = struct.pack('16sh', device, flags)
		fcntl.ioctl(self.sockfd, SIOCSIFFLAGS, ifreq)

	def up(self, device):
		''' Bring up the bridge interface. Equivalent to ifconfig [iface] up. '''
		self.set_device_flag(device, IFF_UP)
#		# Get existing device flags
#		ifreq = struct.pack('16sh', device, 0)
#		flags = struct.unpack('16sh', fcntl.ioctl(self.sockfd, SIOCGIFFLAGS, ifreq))[1]
#
#		# Set new flags
#		flags = flags | IFF_UP
#		ifreq = struct.pack('16sh', device, flags)
#		fcntl.ioctl(self.sockfd, SIOCSIFFLAGS, ifreq)

	def down(self, device):
		''' Bring up the bridge interface. Equivalent to ifconfig [iface] down. '''
		self.unset_device_flag(device, IFF_UP)

#		# Get existing device flags
#		ifreq = struct.pack('16sh', device, 0)
#		flags = struct.unpack('16sh', fcntl.ioctl(self.sockfd, SIOCGIFFLAGS, ifreq))[1]
#
#		# Set new flags
#		flags = flags & ~IFF_UP
#		ifreq = struct.pack('16sh', device, flags)
#		fcntl.ioctl(self.sockfd, SIOCSIFFLAGS, ifreq)
	
	def is_iface_flags(self, device, type):
		ifreq = struct.pack('16sh', device, 0)
		flags = struct.unpack('16sh', fcntl.ioctl(self.sockfd, SIOCGIFFLAGS, ifreq))[1]
		return (flags & type ) != 0
	

	def is_up(self, device):
		''' Return True if the interface is up, False otherwise. '''
		try:
			# Get existing device flags
			ifreq = struct.pack('16sh', device, 0)
			flags = struct.unpack('16sh', fcntl.ioctl(self.sockfd, SIOCGIFFLAGS, ifreq))[1]
	
			if flags & IFF_UP:
				return True
			else:
				return False
		except:
			return False

	def get_mac(self, device):
		''' Obtain the device's mac address. '''
		ifreq = struct.pack('16sH14s', device, AF_UNIX, '\x00'*14)
		res = fcntl.ioctl(self.sockfd, SIOCGIFHWADDR, ifreq)
		address = struct.unpack('16sH14s', res)[2]
		mac = struct.unpack('6B8x', address)

		return ":".join(['%02X' % i for i in mac])


	def set_mac(self, newmac, device):
		''' Set the device's mac address. Device must be down for this to
			succeed. '''
		macbytes = [int(i, 16) for i in newmac.split(':')]
		ifreq = struct.pack('16sH6B8x', device, AF_UNIX, *macbytes)
		fcntl.ioctl(self.sockfd, SIOCSIFHWADDR, ifreq)


	def get_ip(self, device):
		ifreq = struct.pack('16sH14s', device, AF_INET, '\x00'*14)
		try:
			res = fcntl.ioctl(self.sockfd, SIOCGIFADDR, ifreq)
		except IOError:
			return None
		ip = struct.unpack('16sH2x4s8x', res)[2]

		return socket.inet_ntoa(ip)


	def set_ip(self, newip, device):
		ipbytes = socket.inet_aton(newip)
		ifreq = struct.pack('16sH2s4s8s', device, AF_INET, '\x00'*2, ipbytes, '\x00'*8)
		fcntl.ioctl(self.sockfd, SIOCSIFADDR, ifreq)


	def get_netmask(self, device):
		ifreq = struct.pack('16sH14s', device, AF_INET, '\x00'*14)
		try:
			res = fcntl.ioctl(self.sockfd, SIOCGIFNETMASK, ifreq)
		except IOError:
			return 0
		netmask = socket.ntohl(struct.unpack('16sH2xI8x', res)[2])

		return 32 - int(round(
			math.log(ctypes.c_uint32(~netmask).value + 1, 2), 1))


	def set_netmask(self, netmask, device):
		netmask = ctypes.c_uint32(~((2 ** (32 - netmask)) - 1)).value
		nmbytes = socket.htonl(netmask)
		ifreq = struct.pack('16sH2sI8s', device, AF_INET, '\x00'*2, nmbytes, '\x00'*8) 
		fcntl.ioctl(self.sockfd, SIOCSIFNETMASK, ifreq)


	def get_index(self, device):
		''' Convert an interface name to an index value. '''
		ifreq = struct.pack('16si', device, 0)
		res = fcntl.ioctl(self.sockfd, SIOCGIFINDEX, ifreq)
		return struct.unpack("16si", res)[1]


	def get_link_info(self, device):
		# First get link params
		ecmd = array.array('B', struct.pack('I39s', ETHTOOL_GSET, '\x00'*39))
		ifreq = struct.pack('16sP', device, ecmd.buffer_info()[0])
		try:
			fcntl.ioctl(self.sockfd, SIOCETHTOOL, ifreq)
			res = ecmd.tostring()
			speed, duplex, auto = struct.unpack('12xHB3xB24x', res)
		except IOError:
			speed, duplex, auto = 65535, 255, 255

		# Then get link up/down state
		ecmd = array.array('B', struct.pack('2I', ETHTOOL_GLINK, 0))
		ifreq = struct.pack('16sP', device, ecmd.buffer_info()[0])
		fcntl.ioctl(self.sockfd, SIOCETHTOOL, ifreq)
		res = ecmd.tostring()
		up = bool(struct.unpack('4xI', res)[0])

		if speed == 65535:
			speed = 0
		if duplex == 255:
			duplex = None
		else:
			duplex = bool(duplex)
		if auto == 255:
			auto = None
		else:
			auto = bool(auto)
		return speed, duplex, auto, up


	def set_link_mode(self, device, speed, duplex):
		# First get the existing info
		ecmd = array.array('B', struct.pack('I39s', ETHTOOL_GSET, '\x00'*39))
		ifreq = struct.pack('16sP', device, ecmd.buffer_info()[0])
		fcntl.ioctl(self.sockfd, SIOCETHTOOL, ifreq)
		# Then modify it to reflect our needs
		#print ecmd
		ecmd[0:4] = array.array('B', struct.pack('I', ETHTOOL_SSET))
		ecmd[12:14] = array.array('B', struct.pack('H', speed))
		ecmd[14] = int(duplex)
		ecmd[18] = 0 # Autonegotiation is off
		#print ecmd
		fcntl.ioctl(self.sockfd, SIOCETHTOOL, ifreq)


	def set_link_auto(self, device, ten=True, hundred=True, thousand=True):
		# First get the existing info
		ecmd = array.array('B', struct.pack('I39s', ETHTOOL_GSET, '\x00'*39))
		ifreq = struct.pack('16sP', device, ecmd.buffer_info()[0])
		fcntl.ioctl(self.sockfd, SIOCETHTOOL, ifreq)
		# Then modify it to reflect our needs
		ecmd[0:4] = array.array('B', struct.pack('I', ETHTOOL_SSET))

		advertise = 0
		if ten:
			advertise |= ADVERTISED_10baseT_Half | ADVERTISED_10baseT_Full
		if hundred:
			advertise |= ADVERTISED_100baseT_Half | ADVERTISED_100baseT_Full
		if thousand:
			advertise |= ADVERTISED_1000baseT_Half | ADVERTISED_1000baseT_Full

		#print struct.unpack('I', ecmd[4:8].tostring())[0]
		newmode = struct.unpack('I', ecmd[4:8].tostring())[0] & advertise
		#print newmode
		ecmd[8:12] = array.array('B', struct.pack('I', newmode))
		ecmd[18] = 1
		fcntl.ioctl(self.sockfd, SIOCETHTOOL, ifreq)
		

	def set_pause_param(self, device, autoneg, rx_pause, tx_pause):
		"""
		Ethernet has flow control! The inter-frame pause can be adjusted, by
		auto-negotiation through an ethernet frame type with a simple two-field
		payload, and by setting it explicitly.

		http://en.wikipedia.org/wiki/Ethernet_flow_control
		"""
		# create a struct ethtool_pauseparm
		# create a struct ifreq with its .ifr_data pointing at the above
		ecmd = array.array('B', struct.pack('IIII',
			ETHTOOL_SPAUSEPARAM, bool(autoneg), bool(rx_pause), bool(tx_pause)))
		import logging
		logging.error("ecmd %r %r", device, ecmd)
		buf_addr, _buf_len = ecmd.buffer_info()
		ifreq = struct.pack('16sP', device, buf_addr)
		fcntl.ioctl(self.sockfd, SIOCETHTOOL, ifreq)

	def get_stats(self, device):
		spl_re = re.compile("\s+")

		fp = open(PROCFS_NET_PATH)
		# Skip headers
		fp.readline()
		fp.readline()
		while True:
			data = fp.readline()
			if not data:
				return None

			name, stats_str = data.split(":")
			if name.strip() != device:
				continue

			stats = [int(a) for a in spl_re.split(stats_str.strip())]
			break

		titles = ["rx_bytes", "rx_packets", "rx_errs", "rx_drop", "rx_fifo",
				  "rx_frame", "rx_compressed", "rx_multicast", "tx_bytes",
				  "tx_packets", "tx_errs", "tx_drop", "tx_fifo", "tx_colls",
				  "tx_carrier", "tx_compressed"]
		return dict(zip(titles, stats))

	#index = property(get_index)
	#mac = property(get_mac, set_mac)
	#ip  = property(get_ip, set_ip)
	#netmask = property(get_netmask, set_netmask)


	def iterifs(self, physical=True):
		''' Iterate over all the interfaces in the system. If physical is
			true, then return only real physical interfaces (not 'lo', etc).'''
		net_files = os.listdir(SYSFS_NET_PATH)
		interfaces = set()
		virtual = set()
		for d in net_files:
			path = os.path.join(SYSFS_NET_PATH, d)
			if not os.path.isdir(path):
				continue
			if not os.path.exists(os.path.join(path, "device")):
				virtual.add(d)
			interfaces.add(d)
	
		# Some virtual interfaces don't show up in the above search, for example,
		# subinterfaces (e.g. eth0:1). To find those, we have to do an ioctl
		if not physical:
			# ifconfig gets a max of 30 interfaces. Good enough for us too.
			ifreqs = array.array("B", "\x00" * SIZE_OF_IFREQ * 30)
			buf_addr, _buf_len = ifreqs.buffer_info()
			ifconf = struct.pack("iP", SIZE_OF_IFREQ * 30, buf_addr)
			ifconf_res = fcntl.ioctl(self.sockfd, SIOCGIFCONF, ifconf)
			ifreqs_len, _ = struct.unpack("iP", ifconf_res)
	
			#assert ifreqs_len % SIZE_OF_IFREQ == 0, (
			#	"Unexpected amount of data returned from ioctl. "
			#	"You're probably running on an unexpected architecture")
	
			res = ifreqs.tostring()
			for i in range(0, ifreqs_len, SIZE_OF_IFREQ):
				d = res[i:i+16].strip('\0')
				test = d.split()
				if len(test) == 1:
					interfaces.add(d)
	
		results = interfaces - virtual if physical else interfaces
		
		return results
	
	
	def findif(self, name):
		for br in self.iterifs(True):
			if name == br:
				return br
		return None
	
	def list_ifs(self, physical=True):
		''' Return a list of the names of the interfaces. If physical is
			true, then return only real physical interfaces (not 'lo', etc). '''
		return [br for br in self.iterifs(physical)]

	def all_interfaces_and_ip(self):
		is_64bits = sys.maxsize > 2**32
		struct_size = 40 if is_64bits else 32
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		max_possible = 8 # initial value
		while True:
			bytes = max_possible * struct_size
			names = array.array('B', '\0' * bytes)
			outbytes = struct.unpack('iL',fcntl.ioctl(
				s.fileno(),
				0x8912,  # SIOCGIFCONF
				struct.pack('iL', bytes,
				names.buffer_info()[0])
			))[0]
			if outbytes == bytes:
				max_possible *= 2
			else:
				break
		namestr = names.tostring()
		return [(namestr[i:i+16].split('\0', 1)[0],
			socket.inet_ntoa(namestr[i+20:i+24]))
			for i in range(0, outbytes, struct_size)]

	def get_active_aliases(self):
		alias=[]
		for ifs in self.all_interfaces_and_ip():
			aifs=ifs[0]
			if re.search(':', aifs):
				alias.append(aifs)
		return alias


	def get_boot_aliases(self):
		BootAliases = []
		ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
		for afile in ifcfg_list:
			if not "ifcfg-" in afile:
				continue
			if not re.search(':', afile):
				continue

			adev = re.sub('.*ifcfg-', '', afile)
			for line in open('/etc/sysconfig/network-scripts/'+afile).readlines():
				if "ONBOOT" in line:
					args = line.split("=",1)
					if "yes" in args[1]:
						BootAliases.append(adev)
						break
						#continue
				#if "IPADDR" in line:
					#args = line.split("=",1)
				#	BootAliases.append(adev)
		return BootAliases

	#### VLAN functions ####

	def del_vlan(self, vlandev):
		'''Delete the VLAN interface.'''
		err = ''
		proc = subprocess.Popen(['vconfig', 'rem', vlandev], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		code = proc.wait()
		for aline in proc.stderr:
			err += aline.strip()
		return err
		#vlanioc = struct.pack('i24s26x', DEL_VLAN_CMD, vlandev)
		#result = struct.unpack('i24s24sh', fcntl.ioctl(self.sockfd, SIOCSIFVLAN, vlanioc))

	def add_vlan(self, ifname, vid):
		err = ''
		proc = subprocess.Popen(['vconfig', 'add', ifname, vid], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		code = proc.wait()
		for aline in proc.stderr:
			err += aline.strip()
		return err
		#vlanioc = struct.pack('i24si22x', ADD_VLAN_CMD, ifname, vid)
		#try:
		#	fcntl.ioctl(self.sockfd, SIOCSIFVLAN, vlanioc)
		#except IOError:
		#  	return False
		#return True
	
	def get_realdev_name(self, ifname):
		'''Get the underlying netdev for a VLAN interface.'''
		ioc = struct.pack('i24s26x', GET_VLAN_REALDEV_NAME_CMD, ifname)
		result = struct.unpack('i24s24s2x', fcntl.ioctl(self.sockfd,
														SIOCGIFVLAN, ioc))
		return result[2].rstrip('\0')
	
	def get_vid(self, ifname):
		print "getting vlan id for "+ifname
		vlanioc = struct.pack('i24s26x', GET_VLAN_VID_CMD, ifname)
		print "got vlanioc for "+ifname
		result = struct.unpack('i24si22x', fcntl.ioctl(self.sockfd, SIOCGIFVLAN, vlanioc))
		return int(result[2])

	def is_vlan(self, ifname):
		''' Try to get real dev, if it work then it's a vlan '''
		try:
			self.get_realdev_name(ifname)
			return True
		except:
			return False
	
	def list_vlans(self):
		''' List all running vlans '''
		vlans = []
		devlist = self.list_ifs(False)
		for adev in sorted(devlist):
			if self.is_vlan(adev):
				if self.is_up(adev):
					vlans.append(adev)

		return vlans

	def list_boot_vlans(self):
		''' List all boot vlans '''
		vlan_list = []
		ifcfg_list = os.listdir("/etc/sysconfig/network-scripts/")
		for afile in sorted(ifcfg_list):
			if "ifcfg-" in afile:
				onboot=False
				bVlan=False
				for line in open("/etc/sysconfig/network-scripts/"+afile).readlines():
					ifname = re.sub('ifcfg-', '', afile)
					if "ONBOOT" in line:
						args = line.split("=")
						if "yes" in args[1]:
							onboot = True
					elif re.search('^VLAN="*yes', line):
						bVlan=True
					if bVlan and onboot:
						 vlan_list.append(ifname)
						 break

		return vlan_list

	#### Bonding functions ####

	def is_bonding(self, device):
		return self.is_iface_flags(device, IFF_BONDING)

	def is_bond_slave(self, device):
		return self.is_iface_flags(device, IFF_SLAVE)
	
	def is_bond_master(self, device):
		return self.is_iface_flags(device, IFF_MASTER)

	def list_bonds(self):
		''' List existing bonds '''
		bonds = []
		#devlist = self.list_ifs(False)
		#for dev in sorted(devlist):
		#	if self.is_bond_master(dev):
		#		bonds.append(dev)

		if os.path.exists("/sys/class/net/bonding_masters"):
			sys_masters = open("/sys/class/net/bonding_masters").readline().strip()
			if len(sys_masters) > 0:
				bonds = sys_masters.split(' ')
		return bonds


	def get_active_slave(self, bond):
		'''The normal value of this option is the name of the currently
			active slave, or the empty string if there is no active slave or
			the current mode does not use an active slave. '''
		active = ''
		if os.path.exists("/sys/class/net/"+bond+"/bonding/active_slave"):
			sys_slaves = open("/sys/class/net/"+bond+"/bonding/active_slave").readlines()
			if len(sys_slaves) > 0:
				active = sys_slaves[0].strip()
		return active
		

	def get_bond_master(self, iface):
		bond = ''
		if os.path.islink('/sys/class/net/'+iface+'/master'):
			dest_path = os.readlink('/sys/class/net/'+iface+'/master')
			bond = re.sub('.*virtual.net.', '', dest_path)
		return bond

	def get_bond_slaves(self, bond):
		slaves = []
		line = ''
		if os.path.exists("/sys/class/net/"+bond+"/bonding/slaves"):
			sys_slaves = open("/sys/class/net/"+bond+"/bonding/slaves").readlines()
			if len(sys_slaves) > 0:
				line = sys_slaves[0]

		slaves = line.strip().split(' ')
		return slaves
	
	def create_bond(self, device):
		err = ''
		try:
			loaded = False
			proc_modules = open("/proc/modules").readlines()
			for module_line in proc_modules:
				if re.search('^bonding ', module_line):
					loaded = True
			if not loaded:
				os.system('modprobe bonding')

			#self.up(device)
			os.system('ifup %s' % device)
			self.set_device_flag(device, IFF_MASTER)
		except:
			err = str(sys.exc_info()[1])
		return err
		
	def release_slave_iface(self, bond, iface):
		''' release iface slave from bond '''
		err = ''
		proc = subprocess.Popen(['ifenslave', '-d', bond, iface], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		code = proc.wait()
		for aline in proc.stderr:
			err += aline.strip()
		return err

	def enslave_iface(self, bond, iface):
		''' Enslave iface to bond '''
		err = ''
		proc = subprocess.Popen(['ifenslave', bond, iface], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		code = proc.wait()
		for aline in proc.stderr:
			err += aline.strip()
		return err


