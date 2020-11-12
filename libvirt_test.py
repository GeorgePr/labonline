import libvirt
import sys
import subprocess


# Initialize connection

try:
	conn = libvirt.open("qemu:///system")
except libvirt.libvirtError:
	print('Failed to connect to the hypervisor')
	sys.exit(1)


# Create and start domain based on sample_domain.xml

xml_file = 'sample_domain.xml'
xml_open = open(xml_file)
xmlconfig = xml_open.read()
dom = conn.defineXML(xmlconfig)


"""
if dom == None:
	print('Failed to define a domain from XML definition', file = sys.sdterr)
	exit(1)

if dom.create() < 0:
	print('Cannot boot domain', file = sys.stderr)
"""

# List domains

names = conn.listDefinedDomains()
print(names)


# Start domain

dom.create()
print('Guest ' + dom.name() + ' has booted', file = sys.stderr)


# Wait for keypress to remove domain

input('Press Enter to remove domain...')
dom.destroy()
dom.undefine()


# Close connection

conn.close()
exit(0)