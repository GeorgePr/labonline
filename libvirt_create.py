''' This file contains a function which creates a specified number of domains '''

from shutil import copyfile
import os
import xml.etree.ElementTree as ET
import sys
import re
import libvirt


def create_domains(domains_input: str, net_list: list, net_list_conf: list):
	'''Creates the number of domains specified by the argument'''

	# Initialize connection
	try:
		conn = libvirt.open('qemu:///system')
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
	if domains_input == '1':
		print(domains_input + ' domain will be created')
	else:
		print(domains_input + ' domains will be created')
	domains_input = int(domains_input)

	for j in range(dom_number, dom_number + domains_input):
		dom_name = 'R' + str(j)
		print('\nDomain', dom_name, 'will be created')

		# Print domain disk location
		abs_path = os.path.dirname(__file__)
		img_dest = os.path.join(abs_path, 'images/R' + str(j) + '.qcow2')
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
		attr_name.text = 'nat' + str(j)

		# Set UUID in new network XML file
		uuid = root.find('./uuid')
		uuid.text = '6ac5acf9-940b-41fc-87a7-1ae02af8ccb' + str(j)

		# Set bridge name in new network XML file
		bridge_name = root.find('./bridge')
		bridge_name.set('name', 'virbr' + str(j+18))

		# Set network MAC address in new network XML file
		mac_add = root.find('./mac')
		mac_add.set('mac', '52:54:00:b' + str(j) + ':4d:00')

		# Set host IP in new network XML file
		host_ip = root.find('./dns/host')
		host_ip.set('ip', '172.22.' + str(j) + '.1')

		# Set hostname in new network XML file
		hostname = root.find('./dns/host/hostname')
		hostname.text = 'R' + str(j)

		# Set DHCP IP in new network XML file
		ip = root.find('./ip')
		ip.set('address', '172.22.' + str(j) + '.200')

		# Set host MAC and IP in new network XML file
		host = root.find('./ip/dhcp/host')
		host.set('mac', '52:54:00:b' + str(j) + ':4d:01')
		host.set('ip', '172.22.' + str(j) + '.1')

		# Create XML for new network
		xml_dest = 'net_xml/nat' + str(j) + '.xml'
		tree.write(xml_dest)
		xml_open = open(xml_dest)
		xmlconfig = xml_open.read()

		# Create network from new XML file
		nat_network = conn.networkDefineXML(xmlconfig)

		# Set as autostart and start network
		nat_network.setAutostart(True)
		nat_network.create()
		print('Network nat' + str(j) + ' has been created\n', file = sys.stderr)



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

		i = 0

		# Create new NIC in XML if applicable
		for i in range(int(net_list[j-dom_number])):
			devices = root.find('.devices')
			current_interface = net_list_conf[j-dom_number][i]

			if current_interface == 'nat':
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
					mac = ET.SubElement(interface, 'mac')
					mac.set('address', '52:54:00:f' + str(int_type + net_number) + ':4d:' + k)
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
		mac.set('address', '52:54:00:b' + str(j) + ':4d:01')
		source = ET.SubElement(interface, 'source')
		source.set('network', 'nat' + str(j))
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
