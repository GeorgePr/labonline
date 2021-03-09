''' This script contains cleanup function '''

import os
import libvirt
from libvirt_domain import init_conn

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
				network = init_conn().networkLookupByName('nat' + str(domain.lower()))
				network.destroy()
				network.undefine()
				print('Removing network nat' + str(domain.lower()) + '...')

			except libvirt.libvirtError:
				print('Could not remove network')

			# Remove network XML
			abs_path = os.path.dirname(__file__)
			xml_dest = os.path.join(abs_path, 'net_xml/nat' + str(domain.lower()) + '.xml')
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
