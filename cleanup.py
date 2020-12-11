import os
import sys
import libvirt

# Script to remove and cleanup all created domains

# Initialize connection


def cleanup():
	try:
		conn = libvirt.open("qemu:///system")
	except libvirt.libvirtError:
		print('Failed to connect to the hypervisor')
		sys.exit(1)

	# Open domains.txt file and remove all domains

	domain_file = open('domains_xml/domains.txt', 'r')

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
					pass
				dom.undefine()
			except libvirt.libvirtError:
				print('Domain R' + str(dom_number) + ' does not exist')
				pass
			abs_path = os.path.dirname(__file__)
			xml_dest = os.path.join(abs_path, 'domains_xml/R' + str(dom_number) + '.xml')
			os.remove(xml_dest)
			img_dest = os.path.join(abs_path, 'images/R' + str(dom_number) + '.qcow2')
			os.remove(img_dest)
	else:
		print('No defined domains')

	domain_file.close()

	# Remove contents of domains.txt

	domain_file = open('domains_xml/domains.txt', 'w+')
	domain_file.close()

	# Close connection

	conn.close()
