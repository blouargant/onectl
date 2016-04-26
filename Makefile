.PHONY: make_rpm

make_rpm:
	./package/build_rpm.sh $(PLG)

package: make_rpm

clean:
	find . -name '*.py?' -delete
	find . -name '*~' -delete
	rm -rf RPMS SRPMS

all: clean package
core:
	./package/build_rpm.sh core
kvm:
	./package/build_rpm.sh kvm
network:
	./package/build_rpm.sh network

target: all
target: package
target: clean
target: core
target: kvm
target: network
