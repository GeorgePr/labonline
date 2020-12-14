#!/bin/sh

for i in $(seq 1 4); do
    virsh net-destroy network${i}
    virsh net-undefine network${i}
    virsh net-destroy hostonly${i}
    virsh net-undefine hostonly${i}
done

for i in $(seq 1 8); do
    virsh net-destroy internal${i}
    virsh net-undefine internal${i}
done

virsh net-destroy bridge
virsh net-undefine bridge