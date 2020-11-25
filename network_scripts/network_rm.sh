#!/bin/sh

for i in $(seq 1 4); do
    virsh net-destroy network${i}
    virsh net-undefine network${i}
done