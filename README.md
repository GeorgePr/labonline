# LabOnLine

## Build and Install

**Ubuntu**

`sudo apt install python3-pip python3-virtualenv libvirt-daemon-system libvirt-clients libvirt-dev virt-viewer virt-manager ebtables bridge-utils qemu-kvm`

`sudo adduser $USER kvm`

[Reboot]

[Optional] Create a virtual environment:
`python3 -m venv .env`
`source .env/bin/activate`

Install the app with `pip3 install -e .`
Run the network initialization script `./network_init.sh`

## Usage

The webserver is started with the command `python3 waitress_server.py`.
The app runs on `localhost:5000` by default.

The user is prompted to select the number of routers and PCs to create.
After pressing the "Load" button, the user can enter the number of
interfaces per VM, as well as the type of connection for each interface.
The app supports the following network modes:

- NAT [pending]
- NAT network
- Bridged [pending]
- Host-Only
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
- `BSDRP_PC_linked.qcow2` (linked clone of `BSDRP.qcow2`)

Created images: 
- `[PC|R]#.qcow2`
(# is the domain index)

### Network XML files

**Directory:** `net_xml/`

Template NAT XML (Management & NAT):
- `sample_nat.xml`

Defined networks:
- `network[1-4].xml` (NAT networks)
- `bridge.xml`
- `hostonly.xml`
- `LAN[1-10].xml`
- `WAN[1-10].xml`

| Network IP & MAC addresses:                       |                                                   |
| ------------------------------------------------- | ------------------------------------------------- |
| LAN[1-10]                                         |                                                   |
| 52 : 54 : 00 : 0[[1-10].hex] : [4-5]d : [xy.hex]  | 10 . 10 . [1-10] . [xy]                           |
| WAN[1-10]                                         |                                                   |
| 52 : 54 : 00 : 1[[1-10].hex] : [4-5]d : [xy.hex]  | 10 . 11 . [1-10] . [xy]                           |
| Management (NAT)                                  |                                                   |
| 52 : 54 : 00 : [[20-40].hex+xy.hex] : cc : 01     | 172 . [21-22] . [xy] . 1                          |
| NAT Network [1-4]                                 |                                                   |
| 52 : 54 : 00 : c[1-4] : [4-5]d : [xy.hex]         | 10 . 0 . [1-4] . [xy]                             |
| Host-Only                                         |                                                   |
| 52 : 54 : 00 : d1 : 4d : [xy]                     | 172 . 16 . 1 . [xy]                               |


[xy] device number [1-24] for R, [25-48] for PC
[20|40] 20 for R, 40 for PC
[21|22] 21 for PC, 22 for R
