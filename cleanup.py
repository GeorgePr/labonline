''' This script contains cleanup function '''

import os
import sys
import libvirt

def cleanup():
	''' Removes all domains and management networks '''
	# Initialize connection
	try:
		conn = libvirt.open("qemu:///system")
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

	# Open domains_r.txt file (read)
	domain_file = open('domains_xml/domains_r.txt', 'r')
	lines = domain_file.read().splitlines()

	if lines != []:
		for dom_number in lines:
			print('Removing R' + str(dom_number) + '...')
			try:
				dom = conn.lookupByName('R' + str(dom_number))
				try:
					dom.destroy()
				except libvirt.libvirtError:
					print('Domain R' + str(dom_number) + ' is not running')
				dom.undefine()
			except libvirt.libvirtError:
				print('Domain R' + str(dom_number) + ' does not exist')

			# Remove management network
			try:
				network = conn.networkLookupByName('nat' + str(dom_number))
				network.destroy()
				network.undefine()
				print('Removing network nat' + str(dom_number) + '...')

			except libvirt.libvirtError:
				print('Could not remove network')

			# Remove network XML
			abs_path = os.path.dirname(__file__)
			xml_dest = os.path.join(abs_path, 'net_xml/nat' + str(dom_number) + '.xml')
			os.remove(xml_dest)

			# Remove domain XML and image
			xml_dest = os.path.join(abs_path, 'domains_xml/R' + str(dom_number) + '.xml')
			os.remove(xml_dest)
			img_dest = os.path.join(abs_path, 'images/R' + str(dom_number) + '.qcow2')
			os.remove(img_dest)
	else:
		print('No defined domains')

	domain_file.close()

	# Remove contents of domains_r.txt
	domain_file = open('domains_xml/domains_r.txt', 'w+')
	domain_file.close()

	# Close connection
	conn.close()
