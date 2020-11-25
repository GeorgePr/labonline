from flask import Flask, send_from_directory, render_template, url_for, request, redirect, session
from libvirt_create import *

app = Flask(__name__)
app.secret_key = "isaofj"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

active_domains = []
active_net_list = []

@app.route('/', methods=['POST', 'GET'])
def index():
    active_net_list = []
    if 'active_domains' not in session and 'active_net_list' not in session:
        print('NO SESSION')
        session['active_domains'] = active_domains
        session['active_net_list'] = active_net_list
    with open('domains_xml/domains.txt') as f:
        session['active_domains'].clear()
        for line in f.read():
            if line != '\n':
                session['active_domains'].append(line)
    print(session['active_domains'])
    active_net_list = session['active_net_list']
    print(session['active_net_list'])
    if request.method == 'POST':
        print('INDEX POST')
        num = request.form['nm']
        session['num'] = num
        net_list = []
        for j in range(1, int(num)+1):
            k = request.form['net' + str(j)]
            net_list.append(k)
        session['net_list'] = net_list
        print(net_list)
        session['active_net_list'].extend(net_list)
        try:
            create_domains(num, net_list)
        except:
            print('Domains have not been created')
            return redirect(url_for('index'))
        return redirect(url_for('created'))
    else:
        print('INDEX GET')
        return render_template('index.html', active_domains = active_domains, active_net_list = active_net_list)


@app.route('/created', methods=['POST', 'GET'])
def created():
    if request.method == 'POST':
        print('CREATED POST')
        domain = request.form['hid']
        domain = 'r' + str(domain)
        print(domain)
        return redirect(url_for('xterm', domain = domain))
    else:
        print('CREATED GET')
        number = session['num']
        session['num'] = '0'
        net_list = session['net_list']
        active_domains = session['active_domains']
        print(active_domains)
        file_list = []
        with open('domains_xml/domains.txt') as f:
            for line in f.read():
                if line != '\n':
                    file_list.append(line)
        print(file_list)
        new_domains = list(sorted(set(file_list) - set(active_domains)))
        print('Number')
        print(number)
        print('net_list')
        print(net_list)
        print('active_net_list')
        print(session['active_net_list'])
        active_net_list = session['active_net_list']
        print('new_domains')
        print(new_domains)
        return render_template('created.html', number = number, file_list = file_list, active_net_list = active_net_list, active_domains = active_domains, new_domains = new_domains, net_list = net_list)


@app.route('/xterm/<domain>', methods=['POST', 'GET'])
def xterm(domain):
    inp = domain.split('r', )
    inp = int(inp[1])
    print(str(inp))
    with open('domains_xml/domains.txt') as f:
        if str(inp) in f.read():
            print('Exists')
            return render_template('console.html', domain = domain)
        else:
            return render_template('404.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')