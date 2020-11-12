import libvirt
import sys
import subprocess
import xml.etree.ElementTree as ET
import re
import os

from shutil import copyfile


# Initialize connection

try:
	conn = libvirt.open("qemu:///system")
except libvirt.libvirtError:
	print('Failed to connect to the hypervisor')
	sys.exit(1)

dom_number = 0

for file in sorted(os.listdir('domains_xml/')):
	if file.endswith('.xml'):
		filename = os.path.join('', file)
		number = re.findall('[0-9]', filename)
		dom_number = int("".join(number))
		print('Domain R' + str(dom_number) + ' already exists')

dom_number = dom_number + 1

dom_name = 'R' + str(dom_number)
print('Domain', dom_name, 'will be created')

# Print domain disk location

img_dest = '~/images/R' + str(dom_number) + '.qcow2'
print('Disk image location:', img_dest)
img_dest = os.path.expanduser(img_dest)

# Create domain disk from template

print('Creating disk...')
copyfile(os.path.expanduser('~/images/BSDRP.qcow2'), img_dest)

# Use sample XML

xml_file = 'sample_domain.xml'

# Get tree root in XML file

tree = ET.parse(xml_file)
root = tree.getroot()

# Set name in new XML file

attr_name = root.find('name')
attr_name.text = str(dom_name)

# Set image file in new XML file

source = root.find('./devices/disk/source')
source.set('file', img_dest)

# Create XML for new domain

xml_dest = 'domains_xml/' + dom_name + '.xml'

tree.write(xml_dest)
xml_open = open(xml_dest)
xmlconfig = xml_open.read()

# Create domain from new XML file

dom = conn.defineXML(xmlconfig)

# List domains

'''
definedDomains = conn.listDefinedDomains()
print('Defined instances: {}'.format(definedDomains))
'''

# Start domain

dom.create()
print('Guest ' + dom.name() + ' has booted', file = sys.stderr)


# Wait for keypress to remove domain

user_input = input('Press d to remove or x to exit.\n')

if user_input == 'd':
	dom.destroy()
	dom.undefine()
	os.remove(xml_dest)
	os.remove(img_dest)

# Close connection

conn.close()
sys.exit(0)