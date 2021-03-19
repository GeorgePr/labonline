''' This script contains functions which handle connection to qemu, 
domain initialization, startup, shutdown, status report, removal, 
and a function for printing DHCP leases. '''


from shutil import copyfile
from lxml import etree
import re
import hashlib
import os
import libvirt
import time


def simpleHash(s):
	''' Returns the hash of a string '''

	result = int(hashlib.md5(s.encode('utf-8')).hexdigest(), 16)
	result = int(str(result)[:2])

	while (result > 99 or result < 49):
		if result > 99:
			result = result//2 + result//3
		if result < 49:
			result = result + result//2
	print(result)
	return result


def init_conn():
	''' Initializes the connection to qemu '''
	
	try:
		conn = libvirt.open('qemu:///system')
		return conn
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		return


def create_router(name_r, netconf_r: list):
	''' Creates a router '''

	# Find existing routers
	with open('domains_xml/domains.txt', 'r') as f:
		max_r = 0
		lines = f.read().splitlines()
		for domain in lines:
			dom_number = re.sub('[PCR]', '', domain)
			if domain.startswith('R'):
				max_r = int(dom_number)
			if name_r == domain:
				print('Domain already exists')
				return
	
	dom_number = re.sub('[PCR]', '', name_r)

	j = max_r + 1
	if name_r.startswith('R'):
		j = int(dom_number)
	else:
		j = simpleHash(name_r)

	dom_name = name_r
	print('\nDomain', dom_name, 'will be created')

	# Print domain disk location
	abs_path = os.path.dirname(__file__)
	img_dest = os.path.join(abs_path, 'images/' + dom_name + '.qcow2')

	# Create domain disk from template
	linked_dest = os.path.join(abs_path, 'images/BSDRP_linked.qcow2')
	copyfile(linked_dest, img_dest)

	# Create network for management interface
	# Use sample domain XML
	xml_file = 'net_xml/sample_nat.xml'

	# Get tree root in network XML file
	tree = etree.parse(xml_file)
	root = tree.getroot()

	# Set name in new network XML file
	attr_name = root.find('name')
	attr_name.text = 'mgmt' + dom_name.lower()

	# Set UUID in new network XML file
	b_hex = int('20', 16)
	uuid_last_mgmt = j + b_hex
	uuid_last_mgmt = '{:02x}'.format(uuid_last_mgmt)
	uuid = root.find('./uuid')
	uuid.text = '6ac5acf9-940b-41fc-87a7-1ae02acccc' + uuid_last_mgmt

	# Set bridge name in new network XML file
	bridge_name = root.find('./bridge')
	bridge_name.set('name', 'virbr' + str(j+100))

	# Set network MAC address in new network XML file
	mac_add = root.find('./mac')
	mac_add.set('mac', '52:54:00:' + uuid_last_mgmt + ':cc:00')

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
	host.set('mac', '52:54:00:' + uuid_last_mgmt + ':cc:01')
	host.set('ip', '172.22.' + str(j) + '.1')

	# Create XML for new network
	xml_dest = 'net_xml/mgmt' + dom_name.lower() + '.xml'
	tree.write(xml_dest)
	xml_open = open(xml_dest)
	xmlconfig = xml_open.read()

	# Create network from new XML file
	nat_network = init_conn().networkDefineXML(xmlconfig)

	# Set as autostart and start network
	nat_network.setAutostart(True)
	nat_network.create()
	print('Network mgmt' + dom_name.lower(), 'has been created')

	# Create domain
	# Use sample domain XML
	xml_file = 'domains_xml/sample_domain.xml'

	# Get tree root in domain XML file
	parser = etree.XMLParser(remove_blank_text=True)
	tree = etree.parse(xml_file, parser)
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
	for i, val in enumerate(netconf_r):
		devices = root.find('.devices')
		current_interface = val
		regex_match = re.match('NAT Network', current_interface)

		if regex_match: # NAT Network
			net_number = current_interface.split(regex_match[0], )
			net_number = int(net_number[1])
			interface = etree.Element('interface')
			interface.set('type', 'network')
			mac = etree.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:c' + str(net_number) + ':4d:' + k)
			source = etree.SubElement(interface, 'source')
			source.set('network', 'network' + str(net_number))
			source.set('bridge', 'virbr' + str(net_number-1))
			target = etree.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = etree.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = etree.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = etree.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'NAT':

			# Create network for NAT interface
			xml_file = 'net_xml/sample_nat.xml'
			tree = etree.parse(xml_file)
			root = tree.getroot()
			attr_name = root.find('name')
			attr_name.text = 'nat' + dom_name.lower()
			b_hex = int('a0', 16)
			uuid_last_nat = j + b_hex
			uuid_last_nat = '{:02x}'.format(uuid_last_nat)
			uuid = root.find('./uuid')
			uuid.text = '6ac5acf9-940b-41fc-87a7-1ae02adddd' + uuid_last_nat
			bridge_name = root.find('./bridge')
			bridge_name.set('name', 'virbr' + str(j+18))
			mac_add = root.find('./mac')
			mac_add.set('mac', '52:54:00:' + uuid_last_nat + ':dd:00')
			host_ip = root.find('./dns/host')
			host_ip.set('ip', '192.168.' + str(j) + '.1')
			hostname = root.find('./dns/host/hostname')
			hostname.text = dom_name
			ip = root.find('./ip')
			ip.set('address', '192.168.' + str(j) + '.200')
			host = root.find('./ip/dhcp/host')
			host.set('mac', '52:54:00:' + uuid_last_nat + ':dd:01')
			host.set('ip', '192.168.' + str(j) + '.1')
			xml_dest = 'net_xml/mgmt' + dom_name.lower() + '.xml'
			tree.write(xml_dest)
			xml_open = open(xml_dest)
			xmlconfig = xml_open.read()
			nat_network = init_conn().networkDefineXML(xmlconfig)
			nat_network.setAutostart(True)
			nat_network.create()

			# Create NAT interface
			interface = etree.Element('interface')
			interface.set('type', 'network')
			mac = etree.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:' + uuid_last_nat + ':dd:' + k)
			source = etree.SubElement(interface, 'source')
			source.set('network', 'network' + str(i+1))
			source.set('bridge', 'virbr' + str(i))
			target = etree.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = etree.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = etree.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = etree.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'hostonly':
			interface = etree.Element('interface')
			interface.set('type', 'bridge')
			mac = etree.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:d1:4d:' + k)
			source = etree.SubElement(interface, 'source')
			source.set('bridge', 'virbr4')
			target = etree.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = etree.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = etree.SubElement(interface, 'alias')
			alias.set('name', 'hostonly')
			address = etree.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'bridge':
			interface = etree.Element('interface')
			interface.set('type', 'bridge')
			mac = etree.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:e1:4d:' + k)
			source = etree.SubElement(interface, 'source')
			source.set('bridge', 'virbr8')
			target = etree.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i+4))
			model = etree.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = etree.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = etree.SubElement(interface, 'address')
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
					int_type = 10
				net_number = current_interface.split(regex_match[0], )
				net_number = int(net_number[1])
				interface = etree.Element('interface')
				interface.set('type', 'bridge')
				net_number_hex = int(hex(net_number), 16)
				net_number_hex = '{:01x}'.format(net_number_hex)
				mac = etree.SubElement(interface, 'mac')
				mac.set('address', '52:54:00:' + str(int_type)[0] + net_number_hex + ':4d:' + k)
				source = etree.SubElement(interface, 'source')
				source.set('bridge', 'virbr' + str(int_type + net_number + 8))
				target = etree.SubElement(interface, 'target')
				target.set('dev', 'vnet' + str(i))
				model = etree.SubElement(interface, 'model')
				model.set('type', 'e1000')
				alias = etree.SubElement(interface, 'alias')
				alias.set('name', 'net' + str(i))
				address = etree.SubElement(interface, 'address')
				address.set('type', 'pci')
				address.set('domain', '0x0000')
				address.set('bus', '0x00')
				address.set('slot', '0x0' + str(i+2))
				address.set('function', '0x0')
				devices.append(interface)

		i = i + 1

	# Define management interface
	interface = etree.Element('interface')
	interface.set('type', 'network')
	mac = etree.SubElement(interface, 'mac')
	mac.set('address', '52:54:00:' + uuid_last_mgmt + ':cc:01')
	source = etree.SubElement(interface, 'source')
	source.set('network', 'mgmt' + dom_name.lower())
	source.set('bridge', 'virbr' + str(j+100))
	target = etree.SubElement(interface, 'target')
	target.set('dev', 'vnet' + str(i))
	model = etree.SubElement(interface, 'model')
	model.set('type', 'virtio')
	alias = etree.SubElement(interface, 'alias')
	alias.set('name', 'net' + str(i))
	address = etree.SubElement(interface, 'address')
	address.set('type', 'pci')
	address.set('domain', '0x0000')
	address.set('bus', '0x00')
	address.set('slot', '0x0' + str(i+2))
	address.set('function', '0x0')
	devices.append(interface)

	# Create XML for new domain
	xml_dest = 'domains_xml/' + dom_name + '.xml'
	tree.write(xml_dest, pretty_print=True)

	# Create domain from new XML file
	with open(xml_dest, 'r') as xmlconfig:
		dom = init_conn().defineXML(xmlconfig.read())

	# Start domain
	dom.create()
	print('Guest', dom.name(), 'has booted\n')

	# Append new domain to domains.txt
	with open('domains_xml/domains.txt', 'a') as f:
		f.write(dom_name + '\n')


def create_pc(name_pc, netconf_pc: list):
	''' Creates a PC '''

	# Find existing PCs
	with open('domains_xml/domains.txt', 'r') as f:
		max_pc = 0
		lines = f.read().splitlines()
		for domain in lines:
			dom_number = re.sub('[PCR]', '', domain)
			if domain.startswith('PC'):
				max_pc = int(dom_number)
			if name_pc == domain:
				print('Domain already exists')
				return
	
	dom_number = re.sub('[PCR]', '', name_pc)

	j = max_pc + 1
	if name_pc.startswith('PC'):
		j = int(dom_number)
	else:
		j = simpleHash(name_pc)

	dom_name = name_pc
	print('\nDomain', dom_name, 'will be created')

	# Print domain disk location
	abs_path = os.path.dirname(__file__)
	img_dest = os.path.join(abs_path, 'images/' + dom_name + '.qcow2')

	# Create domain disk from template
	linked_dest = os.path.join(abs_path, 'images/BSDRP_PC_linked.qcow2')
	copyfile(linked_dest, img_dest)

	# Create network for management interface
	# Use sample domain XML
	xml_file = 'net_xml/sample_nat.xml'

	# Get tree root in network XML file
	tree = etree.parse(xml_file)
	root = tree.getroot()

	# Set name in new network XML file
	attr_name = root.find('name')
	attr_name.text = 'mgmt' + dom_name.lower()

	# Set UUID in new network XML file
	b_hex = int('40', 16)
	uuid_last_mgmt = j + b_hex
	uuid_last_mgmt = '{:02x}'.format(uuid_last_mgmt)
	uuid = root.find('./uuid')
	uuid.text = '6ac5acf9-940b-41fc-87a7-1ae02acccc' + uuid_last_mgmt

	# Set bridge name in new network XML file
	bridge_name = root.find('./bridge')
	bridge_name.set('name', 'virbr' + str(j+100+24))

	# Set network MAC address in new network XML file
	mac_add = root.find('./mac')
	mac_add.set('mac', '52:54:00:' + uuid_last_mgmt + ':cc:00')

	# Set host IP in new network XML file
	host_ip = root.find('./dns/host')
	host_ip.set('ip', '172.21.' + str(j) + '.1')

	# Set hostname in new network XML file
	hostname = root.find('./dns/host/hostname')
	hostname.text = dom_name

	# Set DHCP IP in new network XML file
	ip = root.find('./ip')
	ip.set('address', '172.21.' + str(j) + '.200')

	# Set host MAC and IP in new network XML file
	host = root.find('./ip/dhcp/host')
	host.set('mac', '52:54:00:' + uuid_last_mgmt + ':cc:01')
	host.set('ip', '172.21.' + str(j) + '.1')

	# Create XML for new network
	xml_dest = 'net_xml/mgmt' + dom_name.lower() + '.xml'
	tree.write(xml_dest)
	xml_open = open(xml_dest)
	xmlconfig = xml_open.read()

	# Create network from new XML file
	nat_network = init_conn().networkDefineXML(xmlconfig)

	# Set as autostart and start network
	nat_network.setAutostart(True)
	nat_network.create()
	print('Network mgmt' + dom_name.lower(), 'has been created')

	# Create domain
	# Use sample domain XML
	xml_file = 'domains_xml/sample_domain.xml'

	# Get tree root in domain XML file
	parser = etree.XMLParser(remove_blank_text=True)
	tree = etree.parse(xml_file, parser)
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
	for i, val in enumerate(netconf_pc):
		devices = root.find('.devices')
		current_interface = val
		regex_match = re.match('NAT Network', current_interface)

		if regex_match: # NAT Network
			net_number = current_interface.split(regex_match[0], )
			net_number = int(net_number[1])
			interface = etree.Element('interface')
			interface.set('type', 'network')
			mac = etree.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:c' + str(net_number) + ':5d:' + k)
			source = etree.SubElement(interface, 'source')
			source.set('network', 'network' + str(net_number))
			source.set('bridge', 'virbr' + str(net_number-1))
			target = etree.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = etree.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = etree.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = etree.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'NAT':

			# Create network for NAT interface
			xml_file = 'net_xml/sample_nat.xml'
			tree = etree.parse(xml_file)
			root = tree.getroot()
			attr_name = root.find('name')
			attr_name.text = 'nat' + dom_name.lower()
			b_hex = int('a0', 16)
			uuid_last_nat = j + b_hex
			uuid_last_nat = '{:02x}'.format(uuid_last_nat)
			uuid = root.find('./uuid')
			uuid.text = '6ac5acf9-940b-41fc-87a7-1ae02adddd' + uuid_last_nat
			bridge_name = root.find('./bridge')
			bridge_name.set('name', 'virbr' + str(j+18))
			mac_add = root.find('./mac')
			mac_add.set('mac', '52:54:00:' + uuid_last_nat + ':dd:00')
			host_ip = root.find('./dns/host')
			host_ip.set('ip', '192.168.' + str(j) + '.1')
			hostname = root.find('./dns/host/hostname')
			hostname.text = dom_name
			ip = root.find('./ip')
			ip.set('address', '192.168.' + str(j) + '.200')
			host = root.find('./ip/dhcp/host')
			host.set('mac', '52:54:00:' + uuid_last_nat + ':dd:01')
			host.set('ip', '192.168.' + str(j) + '.1')
			xml_dest = 'net_xml/mgmt' + dom_name.lower() + '.xml'
			tree.write(xml_dest)
			xml_open = open(xml_dest)
			xmlconfig = xml_open.read()
			nat_network = init_conn().networkDefineXML(xmlconfig)
			nat_network.setAutostart(True)
			nat_network.create()

			# Create NAT interface
			interface = etree.Element('interface')
			interface.set('type', 'network')
			mac = etree.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:' + uuid_last_nat + ':dd:' + k)
			source = etree.SubElement(interface, 'source')
			source.set('network', 'network' + str(i+1))
			source.set('bridge', 'virbr' + str(i))
			target = etree.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = etree.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = etree.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = etree.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'hostonly':
			interface = etree.Element('interface')
			interface.set('type', 'bridge')
			mac = etree.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:d1:5d:' + k)
			source = etree.SubElement(interface, 'source')
			source.set('bridge', 'virbr4')
			target = etree.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i))
			model = etree.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = etree.SubElement(interface, 'alias')
			alias.set('name', 'hostonly')
			address = etree.SubElement(interface, 'address')
			address.set('type', 'pci')
			address.set('domain', '0x0000')
			address.set('bus', '0x00')
			address.set('slot', '0x0' + str(i+2))
			address.set('function', '0x0')
			devices.append(interface)

		elif current_interface == 'bridge':
			interface = etree.Element('interface')
			interface.set('type', 'bridge')
			mac = etree.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:e1:4d:' + k)
			source = etree.SubElement(interface, 'source')
			source.set('bridge', 'virbr8')
			target = etree.SubElement(interface, 'target')
			target.set('dev', 'vnet' + str(i+4))
			model = etree.SubElement(interface, 'model')
			model.set('type', 'e1000')
			alias = etree.SubElement(interface, 'alias')
			alias.set('name', 'net' + str(i))
			address = etree.SubElement(interface, 'address')
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
					int_type = 10
				net_number = current_interface.split(regex_match[0], )
				net_number = int(net_number[1])
				interface = etree.Element('interface')
				interface.set('type', 'bridge')
				net_number_hex = int(hex(net_number), 16)
				net_number_hex = '{:01x}'.format(net_number_hex)
				mac = etree.SubElement(interface, 'mac')
				mac.set('address', '52:54:00:' + str(int_type)[0] + net_number_hex + ':5d:' + k)
				source = etree.SubElement(interface, 'source')
				source.set('bridge', 'virbr' + str(int_type + net_number + 8))
				target = etree.SubElement(interface, 'target')
				target.set('dev', 'vnet' + str(i))
				model = etree.SubElement(interface, 'model')
				model.set('type', 'e1000')
				alias = etree.SubElement(interface, 'alias')
				alias.set('name', 'net' + str(i))
				address = etree.SubElement(interface, 'address')
				address.set('type', 'pci')
				address.set('domain', '0x0000')
				address.set('bus', '0x00')
				address.set('slot', '0x0' + str(i+2))
				address.set('function', '0x0')
				devices.append(interface)

		i = i + 1

	# Define management interface
	interface = etree.Element('interface')
	interface.set('type', 'network')
	mac = etree.SubElement(interface, 'mac')
	mac.set('address', '52:54:00:' + uuid_last_mgmt + ':cc:01')
	source = etree.SubElement(interface, 'source')
	source.set('network', 'mgmt' + dom_name.lower())
	source.set('bridge', 'virbr' + str(j+100+24))
	target = etree.SubElement(interface, 'target')
	target.set('dev', 'vnet' + str(i))
	model = etree.SubElement(interface, 'model')
	model.set('type', 'virtio')
	alias = etree.SubElement(interface, 'alias')
	alias.set('name', 'net' + str(i))
	address = etree.SubElement(interface, 'address')
	address.set('type', 'pci')
	address.set('domain', '0x0000')
	address.set('bus', '0x00')
	address.set('slot', '0x0' + str(i+2))
	address.set('function', '0x0')
	devices.append(interface)

	# Create XML for new domain
	xml_dest = 'domains_xml/' + dom_name + '.xml'
	tree.write(xml_dest, pretty_print=True)

	# Create domain from new XML file
	with open(xml_dest, 'r') as xmlconfig:
		dom = init_conn().defineXML(xmlconfig.read())

	# Start domain
	dom.create()
	print('Guest', dom.name(), 'has booted\n')

	# Append new domain to domains.txt
	with open('domains_xml/domains.txt', 'a') as f:
		f.write(dom_name + '\n')


def start_domain(domain: str):
	''' Starts selected domain '''

	# Check if domain exists
	try:
		dom = init_conn().lookupByName(domain)
	except libvirt.libvirtError:
		print('Domain not found')
		return

	# Check if domain is shutdown
	domain_state = dom.info()[0]
	if domain_state == libvirt.VIR_DOMAIN_SHUTOFF:
		try:
			dom.create()
			print('Domain', domain, 'has booted')
		except libvirt.libvirtError:
			print('Could not start domain')
			return
	elif domain_state == libvirt.VIR_DOMAIN_RUNNING:
		print('Domain is running')


def shutdown_domain(domain: str):
	''' Shuts down selected domain '''

	# Check if domain exists
	try:
		dom = init_conn().lookupByName(domain)
	except libvirt.libvirtError:
		print('Domain not found')
		return

	# Check if domain is running
	domain_state = dom.info()[0]
	if domain_state == libvirt.VIR_DOMAIN_RUNNING:
		try:
			dom.destroy()
			print('Domain', domain, 'has been shutdown')
		except libvirt.libvirtError:
			print('Could not shutdown domain')
			return
	elif domain_state == libvirt.VIR_DOMAIN_SHUTOFF:
		print('Domain is not running')


def remove_domain(domain: str):
	''' Removes selected domain and management network '''

	# Check if domain exists
	try:
		dom = init_conn().lookupByName(domain)
	except libvirt.libvirtError:
		print('Domain not found')
		return

	# Check if domain is running
	domain_state = dom.info()[0]
	if domain_state == libvirt.VIR_DOMAIN_RUNNING:
		try:
			dom.destroy()
			print('Domain', domain, 'has been shutdown')
		except libvirt.libvirtError:
			print('Could not shutdown domain')
			return
	try:
		dom.undefine()
		abs_path = os.path.dirname(__file__)
		xml_dest = os.path.join(abs_path, 'domains_xml/' + domain + '.xml')
		os.remove(xml_dest)
		img_dest = os.path.join(abs_path, 'images/' + domain + '.qcow2')
		os.remove(img_dest)
		print('Domain', domain, 'has been removed')
	except libvirt.libvirtError:
		print('Could not remove domain')

	# Remove management network
	try:
		network = init_conn().networkLookupByName('mgmt' + domain.lower())
		network.destroy()
		network.undefine()
		abs_path = os.path.dirname(__file__)
		xml_dest = os.path.join(abs_path, 'net_xml/mgmt' + domain.lower() + '.xml')
		os.remove(xml_dest)
		print('Network mgmt' + domain.lower(), 'has been undefined')
	except libvirt.libvirtError:
		print('Could not remove network')


def domain_status(domain: str):
	''' Returns domain status '''

	# Check if domain exists
	try:
		dom = init_conn().lookupByName(domain)
	except libvirt.libvirtError:
		print('Domain not found')
		return

	# Return domain status
	domain_state = dom.info()[0]
	return domain_state


def dhcp_leases():
	''' Returns DHCP leases '''
	
	networks = init_conn().listNetworks()
	networks.sort()
	active_net_leases = {}
	for network in networks:
		net = init_conn().networkLookupByName(network)
		leases = net.DHCPLeases()
		net_leases = []
		if leases != []:
			for lease in leases:
				expiry = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(lease['expirytime']))
				mac = lease['mac']
				addr_prefix = str(lease['ipaddr']) + '/' + str(lease['prefix'])
				hostname = lease['hostname']
				dhcp_entry = expiry, mac, addr_prefix, hostname
				net_leases.append(dhcp_entry)
			active_net_leases.update({network: net_leases})
	return(active_net_leases)


def cleanup():
	''' Removes all domains and management networks '''

	# Open domains.txt file (read)
	with open('domains_xml/domains.txt', 'r') as f:
		lines = f.read().splitlines()

	if lines != []:
		for domain in lines:
			print('Removing', str(domain) + '...')
			try:
				dom = init_conn().lookupByName(str(domain))
				try:
					dom.destroy()
				except libvirt.libvirtError:
					print('Domain', str(domain), 'is not running')
				dom.undefine()
			except libvirt.libvirtError:
				print('Domain', str(domain), 'does not exist')

			# Remove management network
			try:
				network = init_conn().networkLookupByName('mgmt' + str(domain.lower()))
				network.destroy()
				network.undefine()
				print('Removing network mgmt' + str(domain.lower()) + '...')

			except libvirt.libvirtError:
				print('Could not remove network')

			# Remove network XML
			abs_path = os.path.dirname(__file__)
			xml_dest = os.path.join(abs_path, 'net_xml/mgmt' + str(domain.lower()) + '.xml')
			os.remove(xml_dest)

			# Remove domain XML and image
			xml_dest = os.path.join(abs_path, 'domains_xml/' + str(domain) + '.xml')
			os.remove(xml_dest)
			img_dest = os.path.join(abs_path, 'images/' + str(domain) + '.qcow2')
			os.remove(img_dest)
	else:
		print('No defined domains')

	# Remove contents of domains.txt
	with open('domains_xml/domains.txt', 'w+') as f:
		pass
