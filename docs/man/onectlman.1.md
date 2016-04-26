% ONECTL User Manuals
% May 8, 2015

# NAME

onectl - configuration tool

# SYNOPSIS

onectl [*options*] [*input-file*]...

# DESCRIPTION


ONECTL is a tool designed to centralize platform configuration. It can configure certain 
aspects of the system at run-time, postponed after reboot or to show active or saved system settings. 
The purpose is to ease and automate system configuration and to allow more sophisticated control over the system.

ONECTL provides a set of commands to view, set, and automate system settings.  
ONECTL comes with a set of plug-ins responsible to configure the system. Each plugin has a set of options in the 
command line allowing the specific configuration. For more information check the Using Command Line Interface section below.

For a quick overview of all settings configurable in ONECTL type the onectl as root. The output will be something like this

**onectl**  
sys.distro  
sys.kernel  
sys.time.timezone  
sys.time.ntp.service  
sys.time.ntp.servers  
net.conf.eth5.ip  
net.conf.bonds.bond1.ip  
net.conf.eth4.ip  
net.conf.eth3.ip  
net.conf.gateway  
net.bonds  
net.devices  
net.vlans  
neighbors.names  
neighbors.conf.prometheus.ip  
neighbors.conf.prometheus.ssh  


ONECTL configuration abilities will be extended in future releases with add-on plugins.

# SYNOPSIS

**onectl**                      [--help] [--list] [--dump] [--load FILE] [bind SRC-PLUGIN DSCT-PLUGIN] [unbind SRC-PLUGIN DST-PLUGIN] [-d]

**onectl**                      [--history] [--rollback]

**onectl sys.distro**           [--help] [--info] [--view  actual|saved|diff] [--showall]

**onectl sys.kernel**           [--help] [--info] [--view actual|saved|diff]

**onectl sys.hostname**         [--help] [--info] [--view actual|saved|diff] [--set]

**onectl sys.time.timezone**    [--help] [--info] [--view actual|saved|diff] [--zones]

**onectl sys.time.ntp.service** [--help] [--info] [--view actual|saved|diff] [--set]

**onectl sys.time.ntp.servers** [--help] [--info] [--view actual|saved|diff] [--set SERVER SERVER..] [--add SERVER SERVER..] [--remove SERVER SERVER..] 

**onectl net.devices**          [--help] [--info] [--view actual|saved|diff] [--set ETH:STATE ETH:STATE] [--all up|down] [--up ETH ETH] [--down ETH ETH]

**onectl net.conf.ethX.ip**     [--help] [--info] [--view actual|saved|diff] [--set IPADDR/MASK] [--ip IPADDR] [--mask MASK]

**onectl net.conf.gateway**     [--help] [--info] [--view actual|saved|diff] [--set GATEWAY]  [--remove GATEWAY]

**onectl net.bonds**            [--help] [--info] [--view actual|saved|diff] [--set bondX:ethX,ethY] [--add  bondX:ethX,ethY] [--remove bondX]

**onectl net.vlans**            [--help] [--info] [--view actual|saved|diff] [--set ETHX.VID1 ETHX.VID2] [--add ETHX.VID] [--remove ETHX.VID]

**onectl neighbors.names**     [--help] [--info] [--view actual|saved|diff] [--set HOST HOST] [--add HOST HOST] [--remove HOST HOST]

**onectl net.conf.hostX.ip**    [--help] [--info] [--view actual|saved|diff] [--set IPADDR] [--disable]

**onectl net.conf.hostX.ssh**   [--help] [--info] [--exchange] [--import] [--export] [--disable]


# OPTIONS

\--help
:   Information for onectl usage for the specified command
\--list
:   [PLUG-IN]
    Displays list of all available plug-ins. If PLUG-IN or part of a plugin is
    specified only relevant information will be shown.If PLUG-IN is omitted
    all plug-ins will be shown
\--load
:   FILE
    Loads configuration from a FILE. For clean machine. 
    FILE is created in advance in the following format:
    PLUG-IN = VALUE on new line each
\-–dump
:   [PLUG-IN]
    Dumps the current configuration. If plug-in or part of it is specified only related configuration is shown.If [PLUG-IN] is omitted then all keys are shown.  

    Example:  
         **onectl --dump**  
         net.devices = eth3:up eth6:down  
         net.conf.eth4.ip = 163.165.0.3/32  
         net.bonds = bond4:eth7 bond3:eth1  
         net.conf.eth8.ip = 222.168.2.2/32  
         net.vlans = eth3.100 eth5.200  
         **onectl --dump net.conf.b**  
         net.conf.bonds.bond0.ip = 172.18.198.232/24  
         net.conf.bonds.bond1.ip = 172.31.3.232/24  

\-–show
:   [PLUG-IN]
    Displays the active and saved config and the difference between them
    if any. If PLUG-IN or part of it is specified then only relevant plug-in
    configuration is shown.If PLUG-IN is omitted all configuration is shown
    Similar to using the "--view diff" command of a plugin.

\-–info
:   [PLUG-IN]
    Displays information for plug-ins usage and how to perform configuration. If PLUG-IN or part of it is
    specified then only relevant information is shown.If PLUG-IN is omitted information for all plug-ins is shown

\--nolive, -n
:   Do not proceed to a live configuration of the system. The configuration is saved and executed later after reload

\-–bind
:   SRC-PLUG-IN DST-PLUG-IN
    Links two plug-ins from the same type. If the value of DST-PLUG-IN is
    changed SRC-PLUG-IN is changed also. 

\-–unbind
:   SRC-PLUG-IN DST-PLUG-IN
    Removes the lin between two plug-ins from the same type. The oposite of --bind. 

\-–history
:   [CHANGEID]
    Shows configuration change history - date,change. If CHANGEID is specified
    the the onectl configuration state is dumped.
    Available IDs can be viewed with onectl --history command.
    History is lost on uninstall 

\-–rollback
:   [CHANGEID]
    Revert configuration to a previous state identified by CHANGEID. If CHANGEID is not specified
    the config is reverted to the previous config.
    Available CHANGEIDs can be viewed with onectl --history command. 



\-d
:   Activate debug mode. Place -d option in each command to be debugged  

    Example:  
    onectl -d net.bonds --add bond0:eth4,eth5  
PLUG-IN
:   Plug-in name

# Advanced usage:
\--load-plugin 
:    Use this command to load (or reload) dynamic plugins.

# PLUG-IN  

\ sys.distro
:   Provide information about the installed OS (Version and Profile)

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps actual system configuration  
        saved  –     Configured but not actual yet  
        diff   –     Difference between saved and actual configuration  
    --**showall**      Show all Operating System information-both installed OS – version  
                   and profile and kernel information

\ sys.kernel
:   Provide information about the running kernel

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  

\ sys.hostname
:   Configure system name

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** HOSTNAME  Change the name of the system



\ sys.time.timezone
:   Provides ability to configure and view the system's timezone

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**zones all|ZONE** 
    
         Lists all available time zone if all command is used or a specific ZONE··
         Used with sys.time.timezone


\ sys.time.ntp.service
:   Provides ability to start/stop NTP service and view current status

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set on|off**  
    
        Start or stop NTP service.
        Used with sys.time.ntp.service  
    --**status**  
          
        Show service status: if enabled or disable/if synchronized
        or not. Used with sys.time.ntp.service

\ sys.time.ntp.servers
:   Provides ability to configure NTP servers

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** SERVER SERVER..  
    
        Deletes all servers set in /etc/ntp.conf and adds
        the list specified in the command in the same order  
    --**add** SERVER SERVER..  

        Adds the list of servers specified to the already saved ones··
    --**remove** SERVER SERVER..  

        Removes servers from configuration  


\ net.devices
:   Activate or deactivate physical network interfaces

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** ETH:STATE ETH:STATE  
    
        Activate or deactivate physical network interfaces in this format:
        ETH:STATE ETH:STATE.  
        Example: --set eth0:up eth1:down  
    --**all up|down**  
        
        Activate or deactivate all interfaces at once
    --**up ETH ETH**  

        Activate one or more interfaces  
    --**down ETH ETH**  

        Activate one or more interfaces  


\ net.conf.ethX.ip    net.conf.bonds.bondX.ip   net.conf.vlans.ethX.Y.ip
:   Configures IP and/or mask to a  physical network interfaces
    An interface must first be activated before being able to proceed with its
    configuration. It is done by net.devices by activating or deactivating the
    interface  

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** IPADDR/MASK | dhcp | none  
    
        Configure an IP address and or mask to an interface  
        It is done in the following format: set IP/MASK  
        eg: --set 192.168.1.1/24  
        The 'dhcp' keyword can also be used for dynamic IP configuration.  
        Example: --set dhcp  
        To unset an interface IP you can use either "0.0.0.0/0" or "none".  

    --**ip** IPADDR

        Configures IP address··
    --**mask** MASK..  

        Configures mask  

\ net.aliases
:   Creates alias network interfaces

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** ETHX:NUM ETHX:NUM..  
    
        Configures subinterfaces in this format ETH:NUM ETH:NUM. Removes the existing aliases
        Example: --set eth0:1 eth1:0

    --**add** ETHX:NUM ETHX:NUM..  

        Add  alias interfaces to already.  
        Example: --add eth0:1 eth1:0  
    --**remove** ETHX:NUM ETHX:NUM..  

        Removes alias interfaces  

\ net.conf.aliases.ethX:NUM.ip  net.conf.aliases.bondX:1.ip
:   Configures IP and/or mask to a alias interfaces
    An interface must first be activated before being able to proceed with its
    configuration. It is done by net.devices by activating or deactivating the
    interface  

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** IPADDR/MASK | dhcp | none  
    
        Configure an IP address and or mask to an interface  
        It is done in the following format: set IP/MASK  
        eg: --set 192.168.1.1/24  
        The 'dhcp' keyword can also be used for dynamic IP configuration.  
        Example: --set dhcp  
        To unset an interface IP you can use either "0.0.0.0/0" or "none".  

    --**ip** IPADDR

        Configures IP address··
    --**mask** MASK..  

        Configures mask  

\ net.conf.gateway 
:   Configures default gateway

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** IP..  
    
        Configures the default gateway:
        Example:set 10.165.110.254

    --**remove** IP  

        Removes default gateway  

\ net.bonds 
:   Activates or deactivates bonding interfaces

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** bondX:ethX,ethY.. | none  
    
        Creates bonding interface:  
        Example: --set bond0:eth0,eth1 bond1:eth2,eth3  
        Keyword "none" can be used to remove all bonds  
        Set command removes previous configuration and applied the new one  

    --**add** bondX:ethX,ethY  

        Add a bond. Adds the bond to the previous configuration.  
        Example: --add bond3:eth2,eth5  
    --**remove** bondX..  

        Removes a bond  

\ net.vlans
:   Activates or deactivates bonding interfaces

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** ETHX.VID1 ETHX.VID2  
    
        Creates vlan(s):  
        Example: --set eth0.100 eth1.200  
        Keyword "none" can be used to remove all vlans  
        Set command removes previous configuration and applies the new one  

    --**add** ETHX.VID  

        Add a vlan. Add command adds configuration to the existing one.  
        Example: --add eth3.100  
    --**remove** ETHX.VID..  

        Remove a vlan  

# neighbors PLUG-INs  
 Plug-ins used for neigbouring host configuration like ip to hostname mapping
 and ssh key exchange keys

\ neighbors.names
:   Create plugins for neighbor host configuration

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** HOST HOST  
    
        Create plugins for neighbor host configuration. New plugins will
        appear as neighbors.conf.hostX.ip and neighbors.conf.hostX.ssh.
        The set command will remove previously configured neighbor plugins.  
        Example: onectl neighbors.name --set prometheus  
    
    --**add** HOST HOST  

        Add neighbor plugins to already existing ones.  
        Example: onectl neighbors.name --add prometheus1  

    --**remove** HOST HOST..  

        Remove plugins and configuration for the listed neighbors.
        --disable is done for ip and ssh before deleting the plugins  
        Example: onectl neighbors.name --remove prometheus1··


\ neighbors.conf.hostX.ip
:   Configure IP address of the host and save it as an entry in /etc/hosts
    Plugin neighbors.names should be first configured before being able to proceed with this
    configuration.  

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** IPADDR  
    
        Configures the ip address of the host and saves it in /etc/hosts  
        eg: --set 192.168.1.1/24  

    --**disable** 
        Removes the entry for the hostname in /etc/hosts

\ neighbors.conf.hostX.ssh
:   Exchanges ssh key with hostX or removes it. Before key is exchanges neighbors.conf.hostX.ip
    must be configured in order communication with the host is established.  

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in  
    --**exchange** [PASS]  
    
        Exchange ssh keys with hostX. This plugin creates DSA keys on the local machine and hostX if they don't exist and
        copies them to the other machine respectivelly in ~/.ssh/authorized_keys.
        If key is already exchanged with the host, password will not be required  
        Optional parameter is password.  
        eg: --exchange NetCen  

    --**import** [PASS]  
    
        Get ssh key from hostX. This plugin creates DSA key on hostX if it does not exist and
        copies it on the local machine in ~/.ssh/authorized_keys  
        If key is already exchanged with the host, password will not be required··

        eg: --import  

    --**export** [PASS]  
    
        Send ssh key to hostX. This plugin creates DSA key on the local machine if it does not exist and
        copies it on hostX in ~/.ssh/authorized_keys  
        If key is already exchanged with the host, password will not be required··
        eg: --export  

    --**disable** [PASS] 
        Removes the copied DSA keys  and clears the host entries in ~/.ssh/known_hosts from local machine and hostX  
        If key is already exchanged with the host, password will not be required··


# SERVICE PLUG-INs  
 Plug-ins used for easy service configuration  
 Examples: ntpd.services.ntpd.  
 All the service plugins are also mapped to services. plugin for easier use.  
 ntp.services.ntpd will also appear as services.ntpd as an example  

\ ntp.services.. services.. and etc
:   Plug-ins used for easy service configuration. All of them have the following commands in common:

    --**help**         Command information  
    --**info**         Provides information for the specified plug-in, available commands, valid values  
    --**view actual|saved|diff**   Dumps plug-in configuration  

        actual –     Dumps active system configuration  
        saved  –     Configured but not active yet  
        diff   –     Difference between saved and active configuration  
    --**set** on|off  Configures the service  
        
        on –    Executes chkconfig --del then chkconfig --add··
        off –   Executes chkconfig --del service··

    --**start** SERVICE  

        Starts the SERVICE. Equal to service SERVICE sart  
        Example: onectl services.ntpd --start  
    --**stop** SERVICE  

        Stops the service. Equal to service SERVICE stop  
        Example: onectl service.ntpd --stop  

    --**restart** SERVICE  

        Restarts the SERVICE. Equal to service SERVICE resart  
        Example: onectl services.ntpd --restart  
    --**rank** START:KILL  

        Sets the position in which the service is started and stopped.START is for start position and KILL for kill position  
        The command will change # chkconfig: - START KILL in /etc/init.d/SERVICE   
        Example: onectl service.ntpd --rank 58:74  

    --**level** LEVELS  

        Change the runlevel in which the service is started. List of levels represented like a string.Eg:345  
        The command will change # chkconfig: LEVELS 58 74 in /etc/init.d/SERVICE···
        Example: onectl services.ntpd --level 35  
    --**status**  

        Displays information for the service  
        Example: onectl service.ntpd --status  

