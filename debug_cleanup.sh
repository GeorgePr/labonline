#!/bin/sh

for i in $(seq 1 24); do
	virsh net-destroy natr${i}
	virsh net-undefine natr${i}
	rm net_xml/natpc${i}.xml

	virsh net-destroy natpc${i}
	virsh net-undefine natpc${i}
	rm net_xml/natpc${i}.xml

	virsh net-destroy mgmtr${i}
	virsh net-undefine mgmtr${i}
	rm net_xml/mgmtr${i}.xml

	virsh net-destroy mgmtpc${i}
	virsh net-undefine mgmtpc${i}
	rm net_xml/mgmtpc${i}.xml

	virsh destroy R${i}
	virsh undefine R${i}
	rm images/R${i}.qcow2
	rm domains_xml/R${i}.xml

	virsh destroy PC${i}
	virsh undefine PC${i}
	rm images/PC${i}.qcow2
	rm domains_xml/PC${i}.xml
done

cp /dev/null domains_xml/domains.txt

rm -rf __pycache__