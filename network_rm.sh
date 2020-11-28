#!/bin/sh

for i in $(seq 1 4); do
    virsh net-destroy network${i}
    virsh net-undefine network${i}
    virsh net-destroy hostonly${i}
    virsh net-undefine hostonly${i}
done

virsh net-destroy bridge1
virsh net-undefine bridge1