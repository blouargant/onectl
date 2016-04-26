#%define _unpackaged_files_terminate_build 0

#Autoreq: no
Summary: onectl add on plugins 
Name: onectl-plugins
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
Provides: onectl-plugins-neighbors
#Obsoletes: onectl <= %{version}


%description
onectl is a tool designed to centralized a plateform configuration.
Its configuration abilities is extended with addon plugins.

%package neighbors
Requires: onectl
Summary: onectl tool for neighbors support
Group: None
%description neighbors
 specific plugins...


%define ONECTLPATH /usr/share/onectl
%define TEMPLATES %{ONECTLPATH}/templates/neighbors
%define PLUGINPATH %{ONECTLPATH}/plugins

%prep 
%setup

%build 

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{PLUGINPATH}/neighbors
mkdir -p $RPM_BUILD_ROOT%{TEMPLATES}

# neighbors
install -m 0755 plugins/neighbors/templates/*.py $RPM_BUILD_ROOT%{TEMPLATES}
install -m 0755 plugins/neighbors/*.py $RPM_BUILD_ROOT%{PLUGINPATH}/neighbors/

%clean
rm -rf $RPM_BUILD_ROOT


%files neighbors
%defattr(-,root,root)
%{TEMPLATES}/*.py*
%{PLUGINPATH}/neighbors/*.py*

%pre neighbors

%post neighbors
if rpm -q onectl >/dev/null ; then
	onectl neighbors.names --init
fi


%preun neighbors

%postun neighbors
if [ $1 -eq 0 ] ; then
	rm -rf %{PLUGINPATH}/neighbors
	if rpm -q onectl >/dev/null ; then
		sed -n '/^neighbors./p' %{ONECTLPATH}/data/onectl.data>/tmp/onectl-neighbors.data
		echo "onectl neighbour config backuped in /tmp/onectl-neighbors.data.Please restore with onectl --load /tmp/onectl-neighbors.data if needed"
		sed -i '/^neighbors./d' %{ONECTLPATH}/data/onectl.data
	fi
fi
# make sure that avahi service is running
chkconfig --level 345 avahi-daemon on
service avahi-daemon restart 1>/dev/null 2>&1
