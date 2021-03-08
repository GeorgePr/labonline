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
		for dom_name in lines:
			print('Removing ', str(dom_name) + '...')
			try:
				dom = init_conn().lookupByName(str(dom_name))
				try:
					dom.destroy()
				except libvirt.libvirtError:
					print('Domain', str(dom_name), 'is not running')
				dom.undefine()
			except libvirt.libvirtError:
				print('Domain', str(dom_name), 'does not exist')

			# Remove management network
			try:
				network = init_conn().networkLookupByName('nat' + str(dom_name.lower()))
				network.destroy()
				network.undefine()
				print('Removing network nat' + str(dom_name.lower()) + '...')

			except libvirt.libvirtError:
				print('Could not remove network')

			# Remove network XML
			abs_path = os.path.dirname(__file__)
			xml_dest = os.path.join(abs_path, 'net_xml/nat' + str(dom_name.lower()) + '.xml')
			os.remove(xml_dest)

			# Remove domain XML and image
			xml_dest = os.path.join(abs_path, 'domains_xml/' + str(dom_name) + '.xml')
			os.remove(xml_dest)
			img_dest = os.path.join(abs_path, 'images/' + str(dom_name) + '.qcow2')
			os.remove(img_dest)
	else:
		print('No defined domains')

	# Remove contents of domains.txt
	with open('domains_xml/domains.txt', 'w+') as f:
		pass
