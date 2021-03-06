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

### Domain XML files

**Directory:** `domains_xml/`

Template XML:
- `sample_domain.xml`

Created XML files:
- `domains_xml/[PC|R]#.xml`
(# is the domain index)

### Domain images

**Directory:** `images/`

Template images:
- `BSDRP_linked.qcow2` (linked clone of `BSDRP.qcow2`)
- `FreeBSD_linked.qcow2` (linked clone of `FreeBSD.qcow2`)

Created images: 
- `[PC|R]#.qcow2`
(# is the domain index)

### Network XML files

**Directory:** `net_xml/`

Template NAT XML (management network):
- `sample_nat.xml`

Defined networks:
- `bridge.xml`
- `hostonly[1-4].xml`
- `LAN[1-5].xml`
- `network[1-4].xml`
- `WAN[1-5].xml`
