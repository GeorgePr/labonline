''' Main Flask routing script '''

import os
from datetime import timedelta
import json
import re
from flask import Flask, send_from_directory, render_template, url_for, request, redirect, session
import libvirt
from libvirt_domain import create_router, create_pc, start_domain, shutdown_domain, remove_domain, domain_status, dhcp_leases, cleanup


active_r = []
active_pc = []
active_net_r = []
active_net_pc = []
active_netconf_r = []
active_netconf_pc = []
status_r = []
status_pc = []


app = Flask(__name__)
app.config['SECRET_KEY'] = 'eiaj38dx09'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.permanent_session_lifetime = timedelta(days = 2)


@app.route('/favicon.ico')
def favicon():
	''' Returns favicon '''
	
	return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.route('/', methods=['POST', 'GET'])
def index():
	''' Handles index.html '''

	session.permanent = True
	session['current_page'] = request.endpoint

	active_net_r = []
	active_net_pc = []
	active_netconf_r = []
	active_netconf_pc = []
	if 'active_r' not in session  and 'active_pc' not in session:
		print('NO SESSION')
		session['active_r'] = []
		session['active_pc'] = []
		session['active_net_r'] = []
		session['active_net_pc'] = []
		session['active_netconf_r'] = []
		session['active_netconf_pc'] = []
		session['status_r'] = []
		session['status_pc'] = []
	active_net_r = session['active_net_r']
	active_net_pc = session['active_net_pc']
	print(session['active_r'], session['active_pc'])
	print(session['active_net_r'], session['active_net_pc'])
	print(session['status_r'], session['status_pc'])
	if request.method == 'POST':
		num_r = int(request.form['num_r'])
		num_pc = int(request.form['num_pc'])
		session['num_r'] = num_r
		session['num_pc'] = num_pc
		net_r = []
		net_pc = []

		for j in range(num_r):
			net_r.append(request.form['net_r' + str(j+1)])
		for j in range(num_pc):
			net_pc.append(request.form['net_pc' + str(j+1)])

		session['active_net_r'].extend(net_r)
		session['active_net_pc'].extend(net_pc)

		net_conf_data = request.form.to_dict(flat = False)
		
		j = 0
		netconf_r = [[] for i in net_r]
		for i in range(len(net_r)):
			for elem in range(int(net_r[i])):
				netconf_r[i].append(net_conf_data['interface_type'][j])
				j = j + 1

		netconf_pc = [[] for i in net_pc]
		for i in range(len(net_pc)):
			for elem in range(int(net_pc[i])):
				netconf_pc[i].append(net_conf_data['interface_type'][j])
				j = j + 1
		
		print(netconf_r, netconf_pc)

		session['netconf_r'] = netconf_r
		session['netconf_pc'] = netconf_pc
		session['active_netconf_r'].extend(netconf_r)
		session['active_netconf_pc'].extend(netconf_pc)
		print(session['active_netconf_r'], session['active_netconf_pc'])

		for key, val in enumerate(netconf_r):
			try:
				create_router(netconf_r[key])
			except libvirt.libvirtError:
				print('Domain has not been created')
				return redirect(url_for('index'))
		for key, val in enumerate(netconf_pc):
			try:
				create_pc(netconf_pc[key])
			except libvirt.libvirtError:
				print('Domain has not been created')
				return redirect(url_for('index'))
		
		with open('domains_xml/domains.txt', 'r') as file:
			for line in file.readlines():
				line = line.split('\n')[0]
				if 'R' in line and line not in session['active_r']:
					session['active_r'].append(line)
				if 'PC' in line and line not in session['active_pc']:
					session['active_pc'].append(line)
		
		return redirect(url_for('created'))
	else:
		return render_template('index.html', \
			active_r = json.dumps(session['active_r']), active_pc = json.dumps(session['active_pc']), \
			active_net_r = active_net_r, active_net_pc = active_net_pc, \
			active_netconf_r = active_netconf_r, active_netconf_pc = active_netconf_pc, \
			status_r = json.dumps(session['status_r']), status_pc = json.dumps(session['status_pc']))


@app.route('/created', methods=['POST', 'GET'])
def created():
	''' Handles created.html '''

	session['current_page'] = request.endpoint

	number_r = session['num_r']
	number_pc = session['num_pc']
	session['num_r'] = '0'
	session['num_pc'] = '0'
	session['status_r'] = []
	session['status_pc'] = []

	for i in session['active_r']:
		session['status_r'].extend(str(domain_status(i)))
	for i in session['active_pc']:
		session['status_pc'].extend(str(domain_status(i)))
	
	print(session['active_r'], session['active_pc'])
	print(session['active_net_r'], session['active_net_pc'])
	print(session['active_netconf_r'], session['active_netconf_pc'])
	print(session['status_r'], session['status_pc'])

	if session['active_r'] == [] and session['active_pc'] == []:
		return(redirect(url_for('index')))
	return render_template('created.html', \
		number_r = number_r, number_pc = number_pc, \
		active_r = json.dumps(session['active_r']), active_pc = json.dumps(session['active_pc']), \
		active_net_r = session['active_net_r'], active_net_pc = session['active_net_pc'], \
		active_netconf_r = session['active_netconf_r'], active_netconf_pc = session['active_netconf_pc'], \
		status_r = session['status_r'], status_pc = session['status_pc'])


@app.route('/domain_start', methods=['POST', 'GET'])
def domain_start():
	''' Starts selected domain '''

	domain = request.args.get('domain')
	start_domain(domain)
	if 'R' in domain:
		domain_index = session['active_r'].index(domain)
		session['status_r'][domain_index] = '1'
	if 'PC' in domain:
		domain_index = session['active_pc'].index(domain)
		session['status_pc'][domain_index] = '1'
	return redirect(url_for(session['current_page']))


@app.route('/domain_shutdown', methods=['POST', 'GET'])
def domain_shutdown():
	''' Shuts down selected domain '''

	domain = request.args.get('domain')
	shutdown_domain(domain)
	if 'R' in domain:
		domain_index = session['active_r'].index(domain)
		session['status_r'][domain_index] = '5'
	if 'PC' in domain:
		domain_index = session['active_pc'].index(domain)
		session['status_pc'][domain_index] = '5'
	return redirect(url_for(session['current_page']))


@app.route('/domain_remove', methods=['POST', 'GET'])
def domain_remove():
	''' Removes selected domain '''

	domain = request.args.get('domain')
	remove_domain(domain)
	with open('domains_xml/domains.txt', 'r') as fin:
		lines = fin.readlines()
	with open('domains_xml/domains.txt', 'w') as fout:
		for line in lines:
			if domain not in line:
				fout.write(line)
	if 'R' in domain:
		domain_index = session['active_r'].index(domain)
		if domain in session['active_r']:
			del session['active_r'][domain_index]
			del session['active_net_r'][domain_index]
			del session['active_netconf_r'][domain_index]
			del session['status_r'][domain_index]
	if 'PC' in domain:
		domain_index = session['active_pc'].index(domain)
		if domain in session['active_pc']:
			del session['active_pc'][domain_index]
			del session['active_net_pc'][domain_index]
			del session['active_netconf_pc'][domain_index]
			del session['status_pc'][domain_index]
	return redirect(url_for(session['current_page']))


@app.route('/domains_cleanup', methods=['POST', 'GET'])
def domains_cleanup():
	''' Removes all domains '''

	print('CLEANUP')
	cleanup()
	session.clear()

	active_r.clear()
	active_pc.clear()
	active_net_r.clear()
	active_net_pc.clear()
	active_netconf_r.clear()
	active_netconf_pc.clear()
	status_r.clear()
	status_pc.clear()

	return redirect(url_for('index'))


@app.route('/xterm/<domain>', methods=['POST', 'GET'])
def xterm(domain):
	''' Opens console for selected domain '''

	second_octet = '21'
	if 'R' in domain:
		second_octet = '22'
	domain_number = re.sub('[PCR]', '', domain)
	with open('domains_xml/domains.txt') as file:
		if domain in file.read():
			print('Exists')
			xterm_url = 'http://172.' + second_octet + '.' + domain_number + '.1'
			return redirect(xterm_url)
		else:
			return render_template('404.html')


@app.route('/leases', methods=['GET', 'POST'])
def leases():
	''' Lists info on DHCP leases '''

	active_net_leases = dhcp_leases()
	return render_template('leases.html', active_net_leases = active_net_leases)


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
