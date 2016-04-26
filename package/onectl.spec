
Summary: onectl tool
Name: onectl
Version: %{version}
Release:
Distribution:
Group: None
Packager: b.louargant 
License: GPL 
BuildArch: noarch
Source0:
Requires: bash, python, python-argparse, git >= 1.7.12.4, python-zmq >= 14.3.1-1, libzmq3 >= 3.2.2, python-paramiko
BuildRoot:  %{_tmppath}/%{name}-%{version}-buildroot
Provides: onectl

%description
onectl is a tool designed to centralized a plateform configuration.
Its configuration abilities is extended with addon plugins.


%define ONECTL_DIR /usr/share/onectl
%define LOG_FILE /var/log/onectl.log
%prep
%setup

%build

%install
rm -rf $RPM_BUILD_ROOT
# onectl global files
mkdir -p $RPM_BUILD_ROOT/usr/share/doc/%{name}
mkdir -p $RPM_BUILD_ROOT/etc/%{name}
mkdir -p $RPM_BUILD_ROOT/etc/bash_completion.d
mkdir -p $RPM_BUILD_ROOT/etc/profile.d
mkdir -p $RPM_BUILD_ROOT/usr/share/man/man1/
mkdir -p $RPM_BUILD_ROOT/etc/rc.d/init.d/
install -m 0644 releasenote-%{name}-%{version}.txt $RPM_BUILD_ROOT/usr/share/doc/%{name}/
install -m 0644 onectl.bash $RPM_BUILD_ROOT/etc/bash_completion.d/
install -m 0644 one_completition.sh $RPM_BUILD_ROOT/etc/profile.d/
install -m 0644 onectl.conf $RPM_BUILD_ROOT/etc/%{name}/
install -m 0644 docs/man/onectl.1 $RPM_BUILD_ROOT/usr/share/man/man1/
install -m 0755 onectld $RPM_BUILD_ROOT/etc/rc.d/init.d/

# onectl core
#mkdir -p $RPM_BUILD_ROOT%{ONECTL_DIR}
mkdir -p $RPM_BUILD_ROOT%{ONECTL_DIR}/hooks
mkdir -p $RPM_BUILD_ROOT%{ONECTL_DIR}/docs
mkdir -p $RPM_BUILD_ROOT%{ONECTL_DIR}/plugins/sys/time/ntp
mkdir -p $RPM_BUILD_ROOT%{ONECTL_DIR}/plugins/services
mkdir -p $RPM_BUILD_ROOT%{ONECTL_DIR}/includes
mkdir -p $RPM_BUILD_ROOT%{ONECTL_DIR}/templates/network
mkdir -p $RPM_BUILD_ROOT%{ONECTL_DIR}/data

# core
install -m 0755 onectl/onectl $RPM_BUILD_ROOT%{ONECTL_DIR}/
# Includes
install -m 0755 onectl/includes/*.py $RPM_BUILD_ROOT%{ONECTL_DIR}/includes/
# templates
install -m 0755 onectl/templates/network/*.py $RPM_BUILD_ROOT%{ONECTL_DIR}/templates/network/
install -m 0755 onectl/templates/*.py $RPM_BUILD_ROOT%{ONECTL_DIR}/templates/

# hooks
install -m 0755 onectl/hooks/*.hook $RPM_BUILD_ROOT%{ONECTL_DIR}/hooks/

# Docs
#install -m 0755 docs/*.sh $RPM_BUILD_ROOT%{ONECTL_DIR}/docs/
#install -m 0755 docs/*.html $RPM_BUILD_ROOT%{ONECTL_DIR}/docs/

# PLUGINS
# Plugins system
install -m 0755 onectl/plugins/sys/*.py $RPM_BUILD_ROOT%{ONECTL_DIR}/plugins/sys/
# Plugins time
install -m 0755 onectl/plugins/sys/time/*.py $RPM_BUILD_ROOT%{ONECTL_DIR}/plugins/sys/time/
install -m 0755 onectl/plugins/sys/time/ntp/*.py $RPM_BUILD_ROOT%{ONECTL_DIR}/plugins/sys/time/ntp/
# Plugins services
install -m 0755 onectl/plugins/services/*.py $RPM_BUILD_ROOT%{ONECTL_DIR}/plugins/services/

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root)
%{ONECTL_DIR}/onectl
%{ONECTL_DIR}/hooks/*.hook
#%{ONECTL_DIR}/docs/*

# core
/etc/bash_completion.d/onectl.bash
/etc/profile.d/one_completition.sh
/etc/rc.d/init.d/onectld

# docs
%config(noreplace) /etc/%{name}/onectl.conf
%doc /usr/share/doc/%{name}/releasenote-%{name}-%{version}.txt
/usr/share/man/man1/onectl.1.gz

# include
%{ONECTL_DIR}/includes/*.py*

# templates
%{ONECTL_DIR}/templates/network/*.py*
%{ONECTL_DIR}/templates/*.py*

# general plugins
%{ONECTL_DIR}/plugins/sys/time/*.py*
%{ONECTL_DIR}/plugins/sys/time/ntp/*.py*
%{ONECTL_DIR}/plugins/sys/*.py*
%{ONECTL_DIR}/plugins/services/*.py*


%pre

%post
# If install
#if [ $1 -eq 1 ] ; then
#fi

if [ ! -e "%{ONECTL_DIR}/data/onectl.data" ]; then
	mkdir -p %{ONECTL_DIR}/data/
	touch %{ONECTL_DIR}/data/onectl.data
fi

cd %{ONECTL_DIR}/data
if ! $(git rev-parse --git-dir > /dev/null 2>&1); then
	git init
	git config --global user.name $USER
	git config --global user.email 'root@localhost'
	git add onectl.data
fi

if ! $(git config --list --global 1>/dev/null 2>&1); then 
	git config --global user.name $USER
	git config --global user.email 'root@localhost'
fi

if [ ! -e "%{LOG_FILE}" ]; then
	touch %{LOG_FILE}
fi
chmod 666 %{LOG_FILE}


# create link 
ONECTL_LINK=`ls /usr/bin/onectl 2>/dev/null`
if [ -z "$ONECTL_LINK" ]; then
	ln -s %{ONECTL_DIR}/onectl /usr/bin/onectl
fi

echo "Please login again or execute"
echo "source /etc/bash_completion.d/onectl.bash"

chkconfig --add onectld
chkconfig --level 345 onectld on
service onectld restart

%preun
#echo "Preuninstall"
if [ $1 -eq 0 ] ; then
   echo "Stopping onectld service ..."
   service onectld stop
   chkconfig --del onectld
fi

%postun
if [ $1 -eq 0 ] ; then
	
	\cp -r %{ONECTL_DIR}/data   /tmp/onectl.data
	echo "onectl config backuped in /tmp/onectl.data.Please restore with onectl --load onectl.data if needed"

	rm -f /usr/bin/onectl
	# not removed on uninstallbecause new dir and files were created
	rm -rf %{ONECTL_DIR}
	if  rpm -qa | grep -qw onectl-plugins-network; then
		echo 'Please uninstall onectl-plugins-network too'
	fi
	if  rpm -qa | grep -qw onectl-plugins-neighbors; then
		echo 'Please uninstall onectl-plugins-neighbors too'
	fi
	if  rpm -qa | grep -qw onectl-plugins-kvm; then
		echo 'Please uninstall onectl-plugins-kvm too'
	fi

fi


%changelog
