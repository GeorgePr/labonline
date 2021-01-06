#!/bin/sh

for i in $(seq 1 20); do
    virsh net-destroy nat${i}
    virsh net-undefine nat${i}
    rm net_xml/nat${i}.xml

    virsh destroy R${i}
    virsh undefine R${i}
    rm images/R${i}.qcow2
    rm domains_xml/R${i}.xml
done

cp /dev/null domains_xml/domains_r.txt

rm -rf __pycache__