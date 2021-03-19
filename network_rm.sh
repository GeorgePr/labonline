#!/usr/bin/env bash

for i in $(seq 1 4); do
	virsh net-destroy network${i}
	virsh net-undefine network${i}
done

for i in $(seq 1 10); do
	virsh net-destroy LAN${i}
	virsh net-undefine LAN${i}
done

for i in $(seq 1 10); do
	virsh net-destroy WAN${i}
	virsh net-undefine WAN${i}
done

virsh net-destroy hostonly
virsh net-undefine hostonly
virsh net-destroy bridge
virsh net-undefine bridge