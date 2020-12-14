#!/bin/sh

for file in net_xml/*; do
    virsh net-define $file
done

for i in $(seq 1 4); do
    virsh net-autostart network${i}
    virsh net-start network${i}
    virsh net-autostart hostonly${i}
    virsh net-start hostonly${i}
done

for i in $(seq 1 8); do
    virsh net-autostart internal${i}
    virsh net-start internal${i}
done

virsh net-autostart bridge
virsh net-start bridge
