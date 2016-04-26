#%define _unpackaged_files_terminate_build 0

#Autoreq: no
Summary: onectl add on plugins 
Name: onectl-plugins-network
Version:
Release:
Distribution:
Group: None
Packager: b.louargant 
License: GPL 
BuildArch: noarch
Source0:
#Requires(pre):  onectl
Requires: onectl >= %{version}
BuildRoot:  %{_tmppath}/%{name}-%{version}-buildroot
Provides: onectl-plugins-network
#Obsoletes: onectl <= %{version}


%description
onectl is a tool designed to centralized a plateform configuration.
Its configuration abilities is extended with addon plugins.


%package network
Summary: onectl plugins for network configuration and management
Group: None
Requires: onectl
%description network
Network configuration specific package...

%define ONECTLPATH /usr/share/onectl
%define TEMPLATES %{ONECTLPATH}/templates/network
%define PLUGINPATH %{ONECTLPATH}/plugins
%define XMLPATH %{ONECTLPATH}/xml
%define HOOKS %{ONECTLPATH}/hooks

%prep
%setup

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{PLUGINPATH}/net/conf
mkdir -p $RPM_BUILD_ROOT%{TEMPLATES}

install -m 0755 plugins/net/templates/*.py $RPM_BUILD_ROOT%{TEMPLATES}
install -m 0755 plugins/net/*.py $RPM_BUILD_ROOT%{PLUGINPATH}/net/
install -m 0755 plugins/net/conf/gateway.py $RPM_BUILD_ROOT%{PLUGINPATH}/net/conf/



%clean
rm -rf $RPM_BUILD_ROOT


%files network
%defattr(-,root,root)
%{TEMPLATES}/*.py*
%{PLUGINPATH}/net/conf/*.py*
%{PLUGINPATH}/net/*.py*


%pre

%post network

%preun

%postun network
# If removed
# If removed
if [ $1 -eq 0 ] ; then
	# not removed on uninstallbecause new dir and files were created
	rm -rf %{PLUGINPATH}/net
	if rpm -q onectl >/dev/null ; then
		sed -n '/^net./p' %{ONECTLPATH}/data/onectl.data>/tmp/onectl-network.data
		echo "onectl network config backuped in /tmp/onectl-network.data.Please restore with onectl --load /tmp/onectl-network.data if needed"
		sed -i '/^net./d' %{ONECTLPATH}/data/onectl.data
	fi
fi
