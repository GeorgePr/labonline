import os
import re
import libvirt

# Script to remove and cleanup all created domains

try:
	conn = libvirt.open("qemu:///system")
except libvirt.libvirtError:
	print('Failed to connect to the hypervisor')
	sys.exit(1)


for file in sorted(os.listdir('domains_xml/')):
	if file.endswith('.xml'):
		filename = os.path.join('', file)
		number = re.findall('[0-9]', filename)
		dom_number = int("".join(number))
		print('Removing R' + str(dom_number) + '...')
		try:
			dom = conn.lookupByName('R' + str(dom_number))
			dom.destroy()
			dom.undefine()
		except:
			pass
		xml_dest = 'domains_xml/R' + str(dom_number) +'.xml'
		os.remove(xml_dest)
		img_dest = '~/images/R' + str(dom_number) + '.qcow2'
		img_dest = os.path.expanduser(img_dest)
		os.remove(img_dest)
