#!/usr/bin/env bash

virsh net-destroy default
virsh net-undefine default

for file in net_xml/*; do
	virsh net-define $file
done

for i in $(seq 1 4); do
	virsh net-autostart network${i}
	virsh net-start network${i}

done

for i in $(seq 1 10); do
    virsh net-autostart LAN${i}
    virsh net-start LAN${i}
done

for i in $(seq 1 10); do
	virsh net-autostart WAN${i}
	virsh net-start WAN${i}
done

virsh net-autostart hostonly
virsh net-start hostonly
virsh net-autostart bridge
virsh net-start bridge

