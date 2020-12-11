''' This script contains functions which handle domain startup, shutdown and removal '''

import sys
import os
import libvirt

# This file handles functions for each individual domain
# Functions: start, shutdown, remove

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
	''' Removes selected domain '''

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
		xml_dest = os.path.join(abs_path, 'images/' + domain + '.xml')
		os.remove(xml_dest)
		img_dest = os.path.join(abs_path, 'images/' + domain + '.qcow2')
		os.remove(img_dest)
		print('Domain ' + domain + ' has been removed')
	except libvirt.libvirtError:
		print('Could not remove domain')

	# Close connection
	conn.close()
