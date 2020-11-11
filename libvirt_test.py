import libvirt

conn = libvirt.open("qemu:///system")
names = conn.listDefinedDomains()
print(names)

