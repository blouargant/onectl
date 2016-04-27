#%define _unpackaged_files_terminate_build 0

#Autoreq: no
Summary: onectl add on plugins 
Name: onectl-plugins
Version:
Release:
Distribution:
Group: Comverse
Packager: b.louargant <bertrand.louargant@atoutlinux.net>
License: GPL 
BuildArch: noarch
Source0:
# we fix initscripts version because we rename /etc/init.d/network
Requires: onectl >= %{version}, initscripts = 9.03.40-2.el6
BuildRoot:  %{_tmppath}/%{name}-%{version}-buildroot
Provides: onectl-plugins-kvm
#Obsoletes: onectl <= %{version}


%description
onectl is a tool designed to centralized a plateform configuration.
Its configuration abilities is extended with addon plugins.

%package kvm
Requires: onectl python-xmltodict libvirt-python
Summary: onectl tool for KVM network configuration
Group: Comverse
%description kvm
KVM networking plugins...


%define ONECTLPATH /usr/share/onectl
%define TEMPLATES %{ONECTLPATH}/templates
%define PLUGINPATH %{ONECTLPATH}/plugins
%define XMLPATH %{ONECTLPATH}/xml
%define HOOKS %{ONECTLPATH}/hooks

%prep
%setup

%build

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT%{PLUGINPATH}/net/conf
mkdir -p $RPM_BUILD_ROOT%{PLUGINPATH}/services
mkdir -p $RPM_BUILD_ROOT%{PLUGINPATH}/kvm
mkdir -p $RPM_BUILD_ROOT%{TEMPLATES}/kvm
mkdir -p $RPM_BUILD_ROOT%{HOOKS}/

install -m 0755 plugins/kvm/networks.py $RPM_BUILD_ROOT%{PLUGINPATH}/services/
install -m 0755 plugins/kvm/networks.hook $RPM_BUILD_ROOT%{HOOKS}/
install -m 0755 plugins/kvm/networks-start.hook $RPM_BUILD_ROOT%{HOOKS}/
install -m 0755 plugins/kvm/networks-start.hook $RPM_BUILD_ROOT%{HOOKS}/
install -m 0755 plugins/kvm/net/*.py $RPM_BUILD_ROOT%{PLUGINPATH}/net/
install -m 0755 plugins/kvm/net/conf/*.py $RPM_BUILD_ROOT%{PLUGINPATH}/net/conf/
install -m 0755 plugins/kvm/kvm/*.py $RPM_BUILD_ROOT%{PLUGINPATH}/kvm/
install -m 0755 plugins/kvm/template_ovsbr.py $RPM_BUILD_ROOT%{TEMPLATES}/kvm/
install -m 0755 plugins/kvm/openkvi_vm_access.py $RPM_BUILD_ROOT%{TEMPLATES}/kvm/
install -m 0755 plugins/kvm/openkvi_vm.py $RPM_BUILD_ROOT%{TEMPLATES}/kvm/

%clean
rm -rf $RPM_BUILD_ROOT

%files kvm
%defattr(-,root,root)
# Net specific
%{PLUGINPATH}/services/networks.py
%{HOOKS}/networks.hook
%{HOOKS}/networks-start.hook
%{PLUGINPATH}/net/*.py*
%{PLUGINPATH}/net/conf/*.py*
%{PLUGINPATH}/kvm/*.py*
%{TEMPLATES}/kvm/template_ovsbr.py
%{TEMPLATES}/kvm/openkvi_vm_access.py
%{TEMPLATES}/kvm/openkvi_vm.py


%pre

%post kvm
if [ $1 -eq 1 ]; then
	IFCFG="/etc/sysconfig/network-scripts/ifcfg-*"
	OVSBR_LST=$(ls $IFCFG | xargs grep '^TYPE *= *"*OVSBridge' | sed -e "s/.*ifcfg-//" | sed -e "s/:.*//")
	onectl net.bridges --set $OVSBR_LST
fi
if [ -e /etc/rc.d/init.d/network ]; then
	chkconfig --del network
	mv /etc/rc.d/init.d/network /etc/rc.d/init.d/lowlevel-network
	chkconfig --add lowlevel-network
fi

# Remove files from a previous packaging error
if [ -e %{PLUGINPATH}/kvm/openkvi_vm.py ]; then 
	rm -f %{PLUGINPATH}/kvm/openkvi_vm.py* 2>/dev/null
	rm -f %{PLUGINPATH}/kvm/template_ovsbr.py* 2>/dev/null
	rm -f %{PLUGINPATH}/kvm/openkvi_vm_access.py 2>/dev/null
fi

# If updated, then we need to correctly set openkvi mode
rm -f /tmp/OpenKVI.xm 2>/dev/null
virsh dumpxml OpenKVI 1>/tmp/OpenKVI.xml 2>/dev/null
if [ -e /tmp/OpenKVI.xml ]; then
	ENABLED=$(onectl kvm.openkvi --view saved | grep -vi "Warning")
	if [ -z "$ENABLED" ]; then
		onectl kvm.openkvi --set enable
		NAT=$(grep "iptables -I FORWARD -p tcp -i .* -o .* --dport 443 -j ACCEPT" /etc/rc.d/rc.local)
		if [ "$NAT" ]; then
			BRMGNT=$(echo "$NAT" | sed -e "s/.*tcp -i //" | sed -e "s/ -o .*//")
			echo "Setting OpenKVI in NAT mode on $BRMGNT"
			onectl openkvi.access.bridge --set $BRMGNT
			onectl openkvi.access.mode --set nat
		else
			echo "Setting OpenKVI in Bridge mode"
			onectl openkvi.access.mode --set direct
		fi
	fi
fi

%preun

%postun kvm
# If removed
if [ $1 -eq 0 ]; then
	if [ -e /etc/rc.d/init.d/lowlevel-network ]; then
		chkconfig --del lowlevel-network
		mv /etc/rc.d/init.d/lowlevel-network /etc/rc.d/init.d/network
		chkconfig --add network
	fi
fi
