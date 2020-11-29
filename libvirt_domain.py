import libvirt
import sys
import subprocess
import xml.etree.ElementTree as ET
import re
import os
from shutil import copyfile

# This file handles functions for each individual domain
# Functions: start, shutdown, remove

def start_domain(domain: str):

    # Initialize connection
    
    try:
        conn = libvirt.open('qemu:///system')
    except libvirt.libvirtError:
        print('Failed to connect to the hypervisor')
        sys.exit(1)
    
    # Check if domain exists

    try:
        dom = conn.lookupByName(domain)
    except libvirt.libvirtError:
        print('Domain not found')
        sys.exit(1)
    
    # Check if domain is shutdown

    domain_state = dom.info()[0]
    if domain_state == libvirt.VIR_DOMAIN_SHUTOFF:
        try:
            dom.create()
            print('Domain ' + domain + ' has booted')
        except libvirt.libvirtError:
            print('Could not start domain')
            sys.exit(1)
    elif domain_state == libvirt.VIR_DOMAIN_RUNNING:
        print('Domain is running')

    # Close connection
    conn.close()

def shutdown_domain(domain: str):

    # Initialize connection
    try:
        conn = libvirt.open('qemu:///system')
    except libvirt.libvirtError:
        print('Failed to connect to the hypervisor')
        sys.exit(1)
    
    # Check if domain exists

    try:
        dom = conn.lookupByName(domain)
    except libvirt.libvirtError:
        print('Domain not found')
        sys.exit(1)
    
    # Check if domain is running

    domain_state = dom.info()[0]
    if domain_state == libvirt.VIR_DOMAIN_RUNNING:
        try:
            dom.destroy()
            print('Domain ' + domain + ' has been shutdown')
        except libvirt.libvirtError:
            print('Could not shutdown domain')
            sys.exit(1)
    elif domain_state == libvirt.VIR_DOMAIN_SHUTOFF:
        print('Domain is not running')

    # Close connection
    conn.close()
