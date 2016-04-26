# onectl
One tool to control them all.


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
