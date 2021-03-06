# LabOnLine


## Ubuntu


**Dependencies**

`sudo apt install python3-pip python3-virtualenv libvirt-daemon-system libvirt-clients libvirt-dev virt-viewer virt-manager ebtables bridge-utils qemu-kvm`

`sudo adduser $USER kvm`

[Reboot]

`sudo -H pip3 install -r requirements_dev.txt`


## Build and Install

`./network_init.sh` initializes the networks which are used by the app.


## Usage

The webserver is started with the command `python3 waitress_server.py`.
The app runs on `localhost:5000` by default.

The user is prompted to select the number of routers and PCs to create.
After pressing the "Load" button, the user can enter the number of
interfaces per VM, as well as the type of connection for each interface.
The app supports the following network modes:

- NAT
- NAT network
- Bridged
- Internal Network

After selecting the desired network modes, VMs are initialized by pressing
"Submit".

Once the VMs are created, the user can perform the following actions per VM:
- Start VM (if it is not running)
- Shutdown VM (if it is running)
- Open console (in new tab)
- Remove VM
- View DHCP leases for all VMs

The user can also remove all VMs at once.


## Directories

Template image: `images/BSDRP_linked.qcow2` (linked clone of `images/BSDRP.qcow2`)
                `images/FreeBSD_linked.qcow2` (linked clone of `images/FreeBSD.qcow2`)

Created images: `images/R#.qcow2`, `images/PC#.qcow2`   (# is the domain index)

XML sample: `sample_domain.xml`

Domain XML files: `domains_xml/`
