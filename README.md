# LabOnLine


## Ubuntu


**Dependencies**

`sudo apt install python3-pip python3-virtualenv libvirt-daemon-system libvirt-clients libvirt-dev virt-viewer virt-manager ebtables bridge-utils qemu-kvm`

`sudo adduser $USER kvm`

[Reboot]

`sudo -H pip3 install -r requirements_dev.txt`


## Build and Install


## Usage

**python3 libvirt_python.py**

The user can specify the number of domains to be created in first argument.

After domains are created, the user can select a domain to remove by inserting the domain index and then pressing d.

Each domain is named R[n], has IP address 192.168.122.[n], MAC address 52:54:00:ce:4d:[hex(n)] and hostname r[n], where [n] is the domain index.

**python3 cleanup.py**

Reads defined domain indices in domains.txt file to find existing domains.
Then it removes all existing domains and removes the contents of domains.txt file.


## Directories

Template image: `images/BSDRP_linked.qcow2` (linked clone of `images/BSDRP.qcow2`)

Created images: `images/R#.qcow2`   (# is the domain index)

XML sample: `sample_domain.xml`

Domain XML files: `domains_xml/`
