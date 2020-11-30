from flask import Flask, send_from_directory, render_template, url_for, request, redirect, session
from datetime import timedelta
from libvirt_create import *
from libvirt_domain import *
from cleanup import *

app = Flask(__name__)
app.secret_key = 'isaofj'
app.permanent_session_lifetime = timedelta(days = 1)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


active_domains = []
active_net_list = []
net_list_conf = []
active_net_list_conf = []


@app.route('/', methods=['POST', 'GET'])
def index():
    session.permanent = True
    session['current_page'] = request.endpoint
    active_net_list = []
    active_net_list_conf = []
    print('INDEX')
    if 'active_domains' not in session and 'active_net_list' not in session:
        print('NO SESSION')
        session['active_domains'] = active_domains
        session['active_net_list'] = active_net_list
        session['active_net_list_conf'] = active_net_list_conf
    print('SESSION active_domains')
    print(session['active_domains'])
    print('active_net_list')
    active_net_list = session['active_net_list']
    print(session['active_net_list'])
    if request.method == 'POST':
        print('INDEX POST SUBMIT')
        print('REQUEST FORM DATA')
        num = request.form['nm']
        session['num'] = num
        net_list = []
        for j in range(1, int(num)+1):
            k = request.form['net' + str(j)]
            net_list.append(k)
        session['net_list'] = net_list
        print('net_list')
        print(net_list)
        session['active_net_list'].extend(net_list)

        net_conf_data = request.form
        net_conf_data = net_conf_data.to_dict(flat = False)

        index = 0
        net_list_conf = [[] for i in range(len(net_list))]

        for i in range(len(net_list)):
            for elem in range(int(net_list[i])):
                print(net_conf_data['interface_type'][index])
                net_list_conf[i].append(net_conf_data['interface_type'][index])
                index = index + 1

        session['net_list_conf'] = net_list_conf
        print('SESSION net_list_conf')
        print(session['net_list_conf'])
        session['active_net_list_conf'].extend(net_list_conf)
        print('SESSION active_net_list_conf')
        print(session['active_net_list_conf'])
        try:
            create_domains(num, net_list, net_list_conf)
        except:
            print('Domains have not been created')
            return redirect(url_for('index'))
        with open('domains_xml/domains.txt') as f:
            for line in f.readlines():
                line = line.split('\n')
                if line != '\n' and line[0] not in session['active_domains']:
                    session['active_domains'].append(line[0])
        print('SESSION active_domains')
        print(session['active_domains'])
        return redirect(url_for('created'))
    else:
        print('INDEX GET')
        return render_template('index.html', active_domains = active_domains, active_net_list = active_net_list, \
            active_net_list_conf = active_net_list_conf)


@app.route('/created', methods=['POST', 'GET'])
def created():
    session['current_page'] = request.endpoint
    print('CREATED GET')
    number = session['num']
    session['num'] = '0'
    active_net_list = session['active_net_list']
    print('SESSION active_net_list')
    print(session['active_net_list'])
    print('SESSION active_domains')
    print(session['active_domains'])
    active_net_list_conf = session['active_net_list_conf']
    return render_template('created.html', number = number, active_net_list = active_net_list, \
        active_net_list_conf = active_net_list_conf, active_domains = active_domains)


@app.route('/xterm/<domain>', methods=['POST', 'GET'])
def xterm(domain):
    print('XTERM POST')
    inp = domain.split('r', )
    inp = int(inp[1])
    print(str(inp))
    with open('domains_xml/domains.txt') as f:
        if str(inp) in f.read():
            print('Exists')
            return render_template('console.html', domain = domain)
        else:
            return render_template('404.html')
            


@app.route('/domain_start', methods=['POST', 'GET'])
def domain_start():
    domain = request.args.get('domain')
    start_domain(domain)
    return redirect(url_for(session['current_page']))


@app.route('/domain_shutdown', methods=['POST', 'GET'])
def domain_shutdown():
    domain = request.args.get('domain')
    shutdown_domain(domain)
    return redirect(url_for(session['current_page']))


@app.route('/domain_remove', methods=['POST', 'GET'])
def domain_remove():
    domain = request.args.get('domain')
    remove_domain(domain)
    domain_number = domain.split('R', )
    domain_number = str(domain_number[1])
    with open('domains_xml/domains.txt', 'r') as fin:
        lines = fin.readlines()
    with open('domains_xml/domains.txt', 'w') as fout:
        for line in lines:
            if domain_number not in line:
                fout.write(line)
    
    print('REMOVE IF')
    domain_index = session['active_domains'].index(domain_number)
    if domain_number in session['active_domains']:
        del session['active_domains'][domain_index]
        print(session['active_domains'])
        del session['active_net_list'][domain_index]
        del session['active_net_list_conf'][domain_index]

    active_domains = session['active_domains']
    print(session['active_domains'])
    print(session['active_net_list'])
    active_net_list = session['active_net_list']
    print(session['active_net_list_conf'])
    active_net_list_conf = session['active_net_list_conf']
    return redirect(url_for(session['current_page']))


@app.route('/domains_cleanup', methods=['POST', 'GET'])
def domains_cleanup():
    print('CLEANUP')
    cleanup()
    session.clear()
    active_domains.clear()
    active_net_list.clear()
    active_net_list_conf.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')