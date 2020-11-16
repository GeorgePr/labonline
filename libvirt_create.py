import libvirt
import sys
import subprocess
import xml.etree.ElementTree as ET
import re
import os

from shutil import copyfile

# This file contains a function which creates the
# number of domains specified by the argument.

def create_domains(domains_input):

	# Initialize connection

	try:
		conn = libvirt.open("qemu:///system")
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

	# Find and print existing domains

	dom_number = 0

	domain_file = open('domains_xml/domains.txt', 'r')

	print('Defined domains:')
	lines = domain_file.read().splitlines()
	for dom_number in lines:
		print('R' + dom_number)

	domain_file.close()

	dom_number = int(dom_number)
	dom_number = dom_number + 1

	# Input number of domains to create

	if not domains_input.isdigit():
		print('You entered ' + domains_input + ' which is not a number. Exiting...')
		sys.exit(1)

	if domains_input == "1":
		print(domains_input + ' domain will be created')
	else:
		print(domains_input + ' domains will be created')

	domains_input = int(domains_input)

	for j in range(dom_number, dom_number + domains_input):

		dom_name = 'R' + str(j)
		print('\nDomain', dom_name, 'will be created')

		# Print domain disk location

		img_dest = '~/images/R' + str(j) + '.qcow2'
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
		attr_name.text = dom_name

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

		# Start domain

		dom.create()
		print('Guest ' + dom.name() + ' has booted\n', file = sys.stderr)

		# Append domains.txt and add new domain index

		domain_file = open('domains_xml/domains.txt', 'a')

		domain_file.write(str(j) + '\n')

		domain_file.close()

	# Find and print existing domains (again)

	domain_file = open('domains_xml/domains.txt', 'r')

	print('Defined domains:')

	lines = domain_file.read().splitlines()
	for i in lines:
		print('R' + i)

	domain_file.close()

	# Close connection

	conn.close()
	sys.exit(0)