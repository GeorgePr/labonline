# LabOnLine


## Ubuntu


**Dependencies**

`sudo apt install python3-pip python3-venv libvirt-daemon-system libvirt-clients virt-viewer virt-manager ebtables bridge-utils qemu-kvm`

`sudo adduser $USER kvm`

[Reboot]

`sudo -H pip3 install -r requirements_dev.txt`


## Build and Install


## Usage

**python3 libvirt_python.py**

If no domains exist, the script will create R1.

If n other domains exist, the script will create R(n+1).

After domain is created, the user can select a domain to remove by inserting the domain index and then pressing d.


**python3 cleanup.py**

Reads defined domain indices in domains.txt file to find existing domains.
Then it removes all existing domains and removes the contents of domains.txt file.


## Directories

Template image: `~/images/BSDRP.qcow2`

Created images: `~/images/R#.qcow2`   (# is the domain index)

XML sample: `sample_domain.xml`

Domain XML files: `domains_xml/`
