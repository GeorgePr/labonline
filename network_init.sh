#!/bin/sh

for file in net_xml/*; do
    virsh net-define $file
done

for i in $(seq 1 4); do
    virsh net-autostart network${i}
    virsh net-start network${i}
done