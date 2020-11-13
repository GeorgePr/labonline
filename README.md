# LabOnLine


## Ubuntu


**Dependencies**

sudo apt install libvirt-daemon-system libvirt-clients virt-viewer virt-manager ebtables bridge-utils qemu-kvm

sudo -H pip3 install -r requirements_dev.txt


## Build and Install


## Usage

python3 libvirt_python.py

If no domains exist, the script will create R1.

If n other domains exist, the script will create R(n+1).

After domain is created, the user can input domain index.

Selected domain can be removed by pressing d.


python3 cleanup.py

Reads files in the domains_xml directory to find existing domains.
Then it removes all existing domains.


## Directories

Template image: ~/images/BSDRP.qcow2
Created images: ~/images/R#.qcow2   (# is the domain index)
XML sample: sample_domain.xml
Domain XML files: domains_xml/
