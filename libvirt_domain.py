''' This script contains functions which handle domain startup, shutdown and removal '''

import sys
import os
import libvirt
import time

# This file handles functions for each individual domain
# Functions: start, shutdown, remove, status

def start_domain(domain: str):
	''' Starts selected domain '''

	# Initialize connection
	try:
		conn = libvirt.open('qemu:///system')
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

	# Check if domain exists
	try:
		dom = conn.lookupByName(domain)
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

	# Close connection
	conn.close()


def shutdown_domain(domain: str):
	''' Shuts down selected domain '''

	# Initialize connection
	try:
		conn = libvirt.open('qemu:///system')
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

	# Check if domain exists
	try:
		dom = conn.lookupByName(domain)
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

	# Close connection
	conn.close()


def remove_domain(domain: str):
	''' Removes selected domain and management network '''

	# Initialize connection
	try:
		conn = libvirt.open('qemu:///system')
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

	# Check if domain exists
	try:
		dom = conn.lookupByName(domain)
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
		dom_number = domain.split('R', )
		dom_number = int(dom_number[1])
		network = conn.networkLookupByName('nat' + str(dom_number))
		network.destroy()
		network.undefine()
		abs_path = os.path.dirname(__file__)
		xml_dest = os.path.join(abs_path, 'net_xml/nat' + str(dom_number) + '.xml')
		os.remove(xml_dest)
		print('Network nat' + str(dom_number) + ' has been undefined')
	except libvirt.libvirtError:
		print('Could not remove network')

	# Close connection
	conn.close()


def domain_status(domain: str):
	''' Returns domain  status '''

	# Initialize connection
	try:
		conn = libvirt.open('qemu:///system')
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

	# Check if domain exists
	try:
		dom = conn.lookupByName(domain)
	except libvirt.libvirtError:
		print('Domain not found')
		sys.exit(1)

	# Close connection
	conn.close()

	# Return domain status
	domain_state = dom.info()[0]
	return domain_state


def dhcp_leases():
	try:
		conn = libvirt.open('qemu:///system')
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)
	
	networks = conn.listNetworks()
	networks.sort()
	active_net_leases = []
	for network in networks:
		net = conn.networkLookupByName(network)
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
	print(active_net_leases)
	return(active_net_leases)
