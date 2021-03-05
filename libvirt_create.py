''' This file contains a function which creates a specified number of domains '''

from shutil import copyfile
import os
import xml.etree.ElementTree as ET
import sys
import re
import libvirt


def create_router(netconf: list):
	''' Creates a domain '''

	# Initialize connection
	try:
		conn = libvirt.open('qemu:///system')
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

	# Find and print existing domains
	dom_number = 0
	print('Defined domains:')
	with open('domains_xml/domains.txt', 'r') as f:
		dom_numbers = []
		max_pc = 0
		max_r = 0
		lines = f.read().splitlines()
		for domain in lines:
			dom_number = int(re.sub('[PCR]', '', domain))
			if 'R' in domain:
				max_r = dom_number
			if 'PC' in domain:
				max_pc = dom_number
			dom_numbers.append(dom_number)
		print(dom_numbers, max_r, max_pc)
	
	j = max_r + 1

	dom_name = 'R' + str(j)
	print('\nDomain', dom_name, 'will be created')

	# Print domain disk location
	abs_path = os.path.dirname(__file__)
	img_dest = os.path.join(abs_path, 'images/' + dom_name + '.qcow2')
	print('Disk image location:', img_dest)

	# Create domain disk from template
	linked_dest = os.path.join(abs_path, 'images/BSDRP_linked.qcow2')
	copyfile(linked_dest, img_dest)

	# Create network for management interface
	# Use sample domain XML
	xml_file = 'net_xml/sample_nat.xml'

	# Get tree root in network XML file
	tree = ET.parse(xml_file)
	root = tree.getroot()

	# Set name in new network XML file
	attr_name = root.find('name')
	attr_name.text = 'nat' + dom_name.lower()

	# Set UUID in new network XML file
	b_hex = int('b0', 16)
	uuid_last_mgmt = j + b_hex
	uuid_last_mgmt = '{:02x}'.format(uuid_last_mgmt)
	uuid = root.find('./uuid')
	uuid.text = '6ac5acf9-940b-41fc-87a7-1ae02af8cc' + uuid_last_mgmt

	# Set bridge name in new network XML file
	bridge_name = root.find('./bridge')
	bridge_name.set('name', 'virbr' + str(j+18))

	# Set network MAC address in new network XML file
	mac_add = root.find('./mac')
	mac_add.set('mac', '52:54:00:' + uuid_last_mgmt + ':4d:00')

	# Set host IP in new network XML file
	host_ip = root.find('./dns/host')
	host_ip.set('ip', '172.22.' + str(j) + '.1')

	# Set hostname in new network XML file
	hostname = root.find('./dns/host/hostname')
	hostname.text = dom_name

	# Set DHCP IP in new network XML file
	ip = root.find('./ip')
	ip.set('address', '172.22.' + str(j) + '.200')

	# Set host MAC and IP in new network XML file
	host = root.find('./ip/dhcp/host')
	host.set('mac', '52:54:00:' + uuid_last_mgmt + ':4d:01')
	host.set('ip', '172.22.' + str(j) + '.1')

	# Create XML for new network
	xml_dest = 'net_xml/nat' + dom_name.lower() + '.xml'
	tree.write(xml_dest)
	xml_open = open(xml_dest)
	xmlconfig = xml_open.read()

	# Create network from new XML file
	nat_network = conn.networkDefineXML(xmlconfig)

	# Set as autostart and start network
	nat_network.setAutostart(True)
	nat_network.create()
	print('Network nat' + dom_name.lower() + ' has been created\n', file = sys.stderr)

	# Create domain
	# Use sample domain XML
	xml_file = 'domains_xml/sample_domain.xml'

	# Get tree root in domain XML file
	tree = ET.parse(xml_file)
	root = tree.getroot()

	# Set name in new domain XML file
	attr_name = root.find('name')
	attr_name.text = dom_name

	# Set image file in new domain XML file
	source = root.find('./devices/disk/source')
	source.set('file', img_dest)

	# Set last octet of MAC address
	k = '{:02x}'.format(j)

	# Create new NIC in XML if applicable
	for i, val in enumerate(netconf):
		devices = root.find('.devices')
		current_interface = val

		if current_interface == 'NAT':
			interface = ET.Element('interface')
			interface.set('type', 'network')
			mac = ET.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:c' + str(i+1) + ':4d:' + k)
			source = ET.SubElement(interface, 'source')
			source.set('network', 'network' + str(i+1))
			source.set('bridge', 'virbr' + str(i))
			target = ET.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = ET.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = ET.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = ET.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'hostonly':
			interface = ET.Element('interface')
			interface.set('type', 'bridge')
			mac = ET.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:d' + str(i+1) + ':4d:' + k)
			source = ET.SubElement(interface, 'source')
			source.set('bridge', 'virbr' + str(i+4))
			target = ET.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = ET.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = ET.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = ET.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'bridge':
			interface = ET.Element('interface')
			interface.set('type', 'bridge')
			mac = ET.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:e1:4d:' + k)
			source = ET.SubElement(interface, 'source')
			source.set('bridge', 'virbr8')
			target = ET.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i+4))
			model = ET.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = ET.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = ET.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		else:
			regex_match = re.match('LAN|WAN', current_interface)
			if regex_match:
				# if LAN 0, if WAN 5
				int_type = 0
				if regex_match[0] == 'WAN':
					int_type = 5
				net_number = current_interface.split(regex_match[0], )
				net_number = int(net_number[1])
				interface = ET.Element('interface')
				interface.set('type', 'bridge')
				f_hex = int('f0', 16)
				uuid_last = int_type + net_number + f_hex
				uuid_last = '{:02x}'.format(uuid_last)
				mac = ET.SubElement(interface, 'mac')
				mac.set('address', '52:54:00:' + uuid_last + ':4d:' + k)
				source = ET.SubElement(interface, 'source')
				source.set('bridge', 'virbr' + str(int_type + net_number + 8))
				target = ET.SubElement(interface, 'target')
				target.set('dev', 'vnet' + str(i))
				model = ET.SubElement(interface, 'model')
				model.set('type', 'e1000')
				alias = ET.SubElement(interface, 'alias')
				alias.set('name', 'net' + str(i))
				address = ET.SubElement(interface, 'address')
				address.set('type', 'pci')
				address.set('domain', '0x0000')
				address.set('bus', '0x00')
				address.set('slot', '0x0' + str(i+2))
				address.set('function', '0x0')
				devices.append(interface)

		i = i + 1

	# Define management interface
	interface = ET.Element('interface')
	interface.set('type', 'network')
	mac = ET.SubElement(interface, 'mac')
	mac.set('address', '52:54:00:' + uuid_last_mgmt + ':4d:01')
	source = ET.SubElement(interface, 'source')
	source.set('network', 'nat' + dom_name.lower())
	source.set('bridge', 'virbr' + str(j+18))
	target = ET.SubElement(interface, 'target')
	target.set('dev', 'vnet' + str(i))
	model = ET.SubElement(interface, 'model')
	model.set('type', 'virtio')
	alias = ET.SubElement(interface, 'alias')
	alias.set('name', 'net' + str(i))
	address = ET.SubElement(interface, 'address')
	address.set('type', 'pci')
	address.set('domain', '0x0000')
	address.set('bus', '0x00')
	address.set('slot', '0x0' + str(i+2))
	address.set('function', '0x0')
	devices.append(interface)

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
	with open('domains_xml/domains.txt', 'a') as f:
		f.write(dom_name)

	# Find and print existing domains (again)
	print('Defined domains:')
	with open('domains_xml/domains.txt', 'r') as f:
		dom_numbers = []
		max_pc = 0
		max_r = 0
		lines = f.read().splitlines()
		for domain in lines:
			dom_number = int(re.sub('[PCR]', '', domain))
			if 'R' in domain:
				max_r = dom_number
			if 'PC' in domain:
				max_pc = dom_number
			dom_numbers.append(dom_number)
		print(dom_numbers, max_r, max_pc)

	# Close connection
	conn.close()

def create_pc(netconf: list):
	''' Creates a domain '''

	# Initialize connection
	try:
		conn = libvirt.open('qemu:///system')
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

	# Find and print existing domains
	dom_number = 0
	print('Defined domains:')
	with open('domains_xml/domains.txt', 'r') as f:
		dom_numbers = []
		max_pc = 0
		max_r = 0
		lines = f.read().splitlines()
		for domain in lines:
			dom_number = int(re.sub('[PCR]', '', domain))
			if 'R' in domain:
				max_r = dom_number
			if 'PC' in domain:
				max_pc = dom_number
			dom_numbers.append(dom_number)
		print(dom_numbers, max_r, max_pc)
	
	j = max_r + 1

	dom_name = 'R' + str(j)
	print('\nDomain', dom_name, 'will be created')

	# Print domain disk location
	abs_path = os.path.dirname(__file__)
	img_dest = os.path.join(abs_path, 'images/' + dom_name + '.qcow2')
	print('Disk image location:', img_dest)

	# Create domain disk from template
	linked_dest = os.path.join(abs_path, 'images/BSDRP_linked.qcow2')
	copyfile(linked_dest, img_dest)

	# Create network for management interface
	# Use sample domain XML
	xml_file = 'net_xml/sample_nat.xml'

	# Get tree root in network XML file
	tree = ET.parse(xml_file)
	root = tree.getroot()

	# Set name in new network XML file
	attr_name = root.find('name')
	attr_name.text = 'nat' + dom_name.lower()

	# Set UUID in new network XML file
	b_hex = int('b0', 16)
	uuid_last_mgmt = j + b_hex
	uuid_last_mgmt = '{:02x}'.format(uuid_last_mgmt)
	uuid = root.find('./uuid')
	uuid.text = '6ac5acf9-940b-41fc-87a7-1ae02af8cc' + uuid_last_mgmt

	# Set bridge name in new network XML file
	bridge_name = root.find('./bridge')
	bridge_name.set('name', 'virbr' + str(j+18))

	# Set network MAC address in new network XML file
	mac_add = root.find('./mac')
	mac_add.set('mac', '52:54:00:' + uuid_last_mgmt + ':4d:00')

	# Set host IP in new network XML file
	host_ip = root.find('./dns/host')
	host_ip.set('ip', '172.22.' + str(j) + '.1')

	# Set hostname in new network XML file
	hostname = root.find('./dns/host/hostname')
	hostname.text = dom_name

	# Set DHCP IP in new network XML file
	ip = root.find('./ip')
	ip.set('address', '172.22.' + str(j) + '.200')

	# Set host MAC and IP in new network XML file
	host = root.find('./ip/dhcp/host')
	host.set('mac', '52:54:00:' + uuid_last_mgmt + ':4d:01')
	host.set('ip', '172.22.' + str(j) + '.1')

	# Create XML for new network
	xml_dest = 'net_xml/nat' + dom_name.lower() + '.xml'
	tree.write(xml_dest)
	xml_open = open(xml_dest)
	xmlconfig = xml_open.read()

	# Create network from new XML file
	nat_network = conn.networkDefineXML(xmlconfig)

	# Set as autostart and start network
	nat_network.setAutostart(True)
	nat_network.create()
	print('Network nat' + dom_name.lower() + ' has been created\n', file = sys.stderr)

	# Create domain
	# Use sample domain XML
	xml_file = 'domains_xml/sample_domain.xml'

	# Get tree root in domain XML file
	tree = ET.parse(xml_file)
	root = tree.getroot()

	# Set name in new domain XML file
	attr_name = root.find('name')
	attr_name.text = dom_name

	# Set image file in new domain XML file
	source = root.find('./devices/disk/source')
	source.set('file', img_dest)

	# Set last octet of MAC address
	k = '{:02x}'.format(j)

	# Create new NIC in XML if applicable
	for i, val in enumerate(netconf):
		devices = root.find('.devices')
		current_interface = val

		if current_interface == 'NAT':
			interface = ET.Element('interface')
			interface.set('type', 'network')
			mac = ET.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:c' + str(i+1) + ':4d:' + k)
			source = ET.SubElement(interface, 'source')
			source.set('network', 'network' + str(i+1))
			source.set('bridge', 'virbr' + str(i))
			target = ET.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = ET.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = ET.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = ET.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'hostonly':
			interface = ET.Element('interface')
			interface.set('type', 'bridge')
			mac = ET.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:d' + str(i+1) + ':4d:' + k)
			source = ET.SubElement(interface, 'source')
			source.set('bridge', 'virbr' + str(i+4))
			target = ET.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = ET.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = ET.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = ET.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'bridge':
			interface = ET.Element('interface')
			interface.set('type', 'bridge')
			mac = ET.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:e1:4d:' + k)
			source = ET.SubElement(interface, 'source')
			source.set('bridge', 'virbr8')
			target = ET.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i+4))
			model = ET.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = ET.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = ET.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		else:
			regex_match = re.match('LAN|WAN', current_interface)
			if regex_match:
				# if LAN 0, if WAN 5
				int_type = 0
				if regex_match[0] == 'WAN':
					int_type = 5
				net_number = current_interface.split(regex_match[0], )
				net_number = int(net_number[1])
				interface = ET.Element('interface')
				interface.set('type', 'bridge')
				f_hex = int('f0', 16)
				uuid_last = int_type + net_number + f_hex
				uuid_last = '{:02x}'.format(uuid_last)
				mac = ET.SubElement(interface, 'mac')
				mac.set('address', '52:54:00:' + uuid_last + ':4d:' + k)
				source = ET.SubElement(interface, 'source')
				source.set('bridge', 'virbr' + str(int_type + net_number + 8))
				target = ET.SubElement(interface, 'target')
				target.set('dev', 'vnet' + str(i))
				model = ET.SubElement(interface, 'model')
				model.set('type', 'e1000')
				alias = ET.SubElement(interface, 'alias')
				alias.set('name', 'net' + str(i))
				address = ET.SubElement(interface, 'address')
				address.set('type', 'pci')
				address.set('domain', '0x0000')
				address.set('bus', '0x00')
				address.set('slot', '0x0' + str(i+2))
				address.set('function', '0x0')
				devices.append(interface)

		i = i + 1

	# Define management interface
	interface = ET.Element('interface')
	interface.set('type', 'network')
	mac = ET.SubElement(interface, 'mac')
	mac.set('address', '52:54:00:' + uuid_last_mgmt + ':4d:01')
	source = ET.SubElement(interface, 'source')
	source.set('network', 'nat' + dom_name.lower())
	source.set('bridge', 'virbr' + str(j+18))
	target = ET.SubElement(interface, 'target')
	target.set('dev', 'vnet' + str(i))
	model = ET.SubElement(interface, 'model')
	model.set('type', 'virtio')
	alias = ET.SubElement(interface, 'alias')
	alias.set('name', 'net' + str(i))
	address = ET.SubElement(interface, 'address')
	address.set('type', 'pci')
	address.set('domain', '0x0000')
	address.set('bus', '0x00')
	address.set('slot', '0x0' + str(i+2))
	address.set('function', '0x0')
	devices.append(interface)

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
	with open('domains_xml/domains.txt', 'a') as f:
		f.write(dom_name)

	# Find and print existing domains (again)
	print('Defined domains:')
	with open('domains_xml/domains.txt', 'r') as f:
		dom_numbers = []
		max_pc = 0
		max_r = 0
		lines = f.read().splitlines()
		for domain in lines:
			dom_number = int(re.sub('[PCR]', '', domain))
			if 'R' in domain:
				max_r = dom_number
			if 'PC' in domain:
				max_pc = dom_number
			dom_numbers.append(dom_number)
		print(dom_numbers, max_r, max_pc)

	# Close connection
	conn.close()