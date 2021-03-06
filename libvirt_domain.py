''' This script contains functions which handle connection to qemu, 
domain initialization, startup, shutdown, status report, removal, 
and a function for printing DHCP leases. '''

from shutil import copyfile
from lxml import etree
import re
import sys
import os
import libvirt
import time

def init_conn():
	''' Initializes the connection to qemu '''
	try:
		conn = libvirt.open('qemu:///system')
		return conn
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

def create_router(netconf: list):
	''' Creates a domain '''

	# Find and print existing domains
	dom_number = 0
	print('Defined domains:')
	with open('domains_xml/domains.txt', 'r') as f:
		dom_numbers = []
		max_r = 0
		lines = f.read().splitlines()
		for domain in lines:
			dom_number = int(re.sub('[PCR]', '', domain))
			if 'R' in domain:
				max_r = dom_number
			dom_numbers.append(dom_number)
		print(dom_numbers, max_r)
	
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
	tree = etree.parse(xml_file)
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
	nat_network = init_conn().networkDefineXML(xmlconfig)

	# Set as autostart and start network
	nat_network.setAutostart(True)
	nat_network.create()
	print('Network nat' + dom_name.lower() + ' has been created\n', file = sys.stderr)

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
	for i, val in enumerate(netconf):
		devices = root.find('.devices')
		current_interface = val

		if current_interface == 'NAT':
			interface = etree.Element('interface')
			interface.set('type', 'network')
			mac = etree.SubElement(interface, 'mac')
			mac.set('address', '52:54:00:c' + str(i+1) + ':4d:' + k)
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
			mac.set('address', '52:54:00:d' + str(i+1) + ':4d:' + k)
			source = etree.SubElement(interface, 'source')
			source.set('bridge', 'virbr' + str(i+4))
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
					int_type = 5
				net_number = current_interface.split(regex_match[0], )
				net_number = int(net_number[1])
				interface = etree.Element('interface')
				interface.set('type', 'bridge')
				f_hex = int('f0', 16)
				uuid_last = int_type + net_number + f_hex
				uuid_last = '{:02x}'.format(uuid_last)
				mac = etree.SubElement(interface, 'mac')
				mac.set('address', '52:54:00:' + uuid_last + ':4d:' + k)
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
	mac.set('address', '52:54:00:' + uuid_last_mgmt + ':4d:01')
	source = etree.SubElement(interface, 'source')
	source.set('network', 'nat' + dom_name.lower())
	source.set('bridge', 'virbr' + str(j+18))
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
	print('Guest ' + dom.name() + ' has booted\n', file = sys.stderr)

	# Append new domain to domains.txt
	with open('domains_xml/domains.txt', 'a') as f:
		f.write(dom_name + '\n')

	# Find and print existing domains (again)
	print('Defined domains:')
	with open('domains_xml/domains.txt', 'r') as f:
		dom_numbers = []
		max_r = 0
		lines = f.read().splitlines()
		for domain in lines:
			dom_number = int(re.sub('[PCR]', '', domain))
			if 'R' in domain:
				max_r = dom_number
			dom_numbers.append(dom_number)


def start_domain(domain: str):
	''' Starts selected domain '''

	# Check if domain exists
	try:
		dom = init_conn().lookupByName(domain)
	except libvirt.libvirtError:
		print('Domain not found')
		sys.exit(1)

	# Check if domain is shutdown
	domain_state = dom.info()[0]
	if domain_state == libvirt.VIR_DOMAIN_SHUTOFF:
		try:
			dom.create()
			print('Domain ' + domain + ' has booted')
		except libvirt.libvirtError:
			print('Could not start domain')
			sys.exit(1)
	elif domain_state == libvirt.VIR_DOMAIN_RUNNING:
		print('Domain is running')


def shutdown_domain(domain: str):
	''' Shuts down selected domain '''

	# Check if domain exists
	try:
		dom = init_conn().lookupByName(domain)
	except libvirt.libvirtError:
		print('Domain not found')
		sys.exit(1)

	# Check if domain is running
	domain_state = dom.info()[0]
	if domain_state == libvirt.VIR_DOMAIN_RUNNING:
		try:
			dom.destroy()
			print('Domain ' + domain + ' has been shutdown')
		except libvirt.libvirtError:
			print('Could not shutdown domain')
			sys.exit(1)
	elif domain_state == libvirt.VIR_DOMAIN_SHUTOFF:
		print('Domain is not running')


def remove_domain(domain: str):
	''' Removes selected domain and management network '''

	# Check if domain exists
	try:
		dom = init_conn().lookupByName(domain)
	except libvirt.libvirtError:
		print('Domain not found')
		sys.exit(1)

	# Check if domain is running
	domain_state = dom.info()[0]
	if domain_state == libvirt.VIR_DOMAIN_RUNNING:
		try:
			dom.destroy()
			print('Domain ' + domain + ' has been shutdown')
		except libvirt.libvirtError:
			print('Could not shutdown domain')
			sys.exit(1)
	try:
		dom.undefine()
		abs_path = os.path.dirname(__file__)
		xml_dest = os.path.join(abs_path, 'domains_xml/' + domain + '.xml')
		os.remove(xml_dest)
		img_dest = os.path.join(abs_path, 'images/' + domain + '.qcow2')
		os.remove(img_dest)
		print('Domain ' + domain + ' has been removed')
	except libvirt.libvirtError:
		print('Could not remove domain')

	# Remove management network
	try:
		network = init_conn().networkLookupByName('nat' + domain.lower())
		network.destroy()
		network.undefine()
		abs_path = os.path.dirname(__file__)
		xml_dest = os.path.join(abs_path, 'net_xml/nat' + domain.lower() + '.xml')
		os.remove(xml_dest)
		print('Network nat' + domain.lower() + ' has been undefined')
	except libvirt.libvirtError:
		print('Could not remove network')


def domain_status(domain: str):
	''' Returns domain status '''

	# Check if domain exists
	try:
		dom = init_conn().lookupByName(domain)
	except libvirt.libvirtError:
		print('Domain not found')
		sys.exit(1)

	# Return domain status
	domain_state = dom.info()[0]
	return domain_state


def dhcp_leases():
	''' Returns DHCP leases '''
	
	networks = init_conn().listNetworks()
	networks.sort()
	active_net_leases = []
	for network in networks:
		net = init_conn().networkLookupByName(network)
		leases = net.DHCPLeases()
		if leases != []:
			active_net_leases.append(network)
			for lease in leases:
				expiry = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(lease['expirytime']))
				mac = lease['mac']
				addr_prefix = str(lease['ipaddr']) + '/' + str(lease['prefix'])
				hostname = lease['hostname']
				dhcp_entry = expiry + ' ' + mac + ' ' + addr_prefix + ' ' + hostname
				active_net_leases.append(dhcp_entry)
	return(active_net_leases)
