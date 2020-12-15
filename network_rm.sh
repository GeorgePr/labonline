#!/bin/sh

for i in $(seq 1 4); do
    virsh net-destroy network${i}
    virsh net-undefine network${i}
    virsh net-destroy hostonly${i}
    virsh net-undefine hostonly${i}
done

for i in $(seq 1 5); do
    virsh net-destroy LAN${i}
    virsh net-undefine LAN${i}
done

for i in $(seq 1 5); do
    virsh net-destroy WAN${i}
    virsh net-undefine WAN${i}
done

virsh net-destroy bridge
virsh net-undefine bridge