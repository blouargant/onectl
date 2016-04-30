# onectl
One tool to control them all.

ONECTL is designed to centralize system configuration. It can configure certain aspects of the system at run-time, postponed after reboot 
or to show active or saved system settings. 
It can  ease and automate system configuration and to allow more precise control over the system.

ONECTL comes with a set of plug-ins responsible for each module config. Each plugin has a set of options in the 
command line. Get acquainted with the Using Command Line Interface in onectl man.


How to build package 

run the following command at the root of the directory:
> make all

The rpm package will be available in RPMS directory.
While the src.rpm package can be found in SRPMS directory.
packages generated:
onectl - onectl core package
onectl-plugins-network  - network related plugins

* To only create the core onectl package
  > make core
* To only create the KVM plugin use
  > make kvm
* To only create the Network plugin use
  > make network

Otherwise you can also use the PLG variable to set the plugin to build:
eg:
> make PLG=kvm
will build the kvm plugin.
