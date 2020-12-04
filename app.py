from flask import Flask, send_from_directory, render_template, url_for, request, redirect, session
from datetime import timedelta
from libvirt_create import *
from libvirt_domain import *
from cleanup import *
import subprocess
from consolecallback import reset_term, error_handler, Console, check_console, stdin_callback, stream_callback, lifecycle_callback

app = Flask(__name__)
app.secret_key = 'isaofj'
app.permanent_session_lifetime = timedelta(days = 1)

name = 'R1'


##########################################

import argparse
from flask_socketio import SocketIO
import pty
import os
import select
import termios
import struct
import fcntl
import shlex

import eventlet


app.config['TESTING'] = True
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'secret!'
app.config['FLASK_ENV'] = 'development'
app.config['child_pid'] = None
app.config['fd'] = None
app.config['cmd'] = '/bin/zsh'
socketio = SocketIO(app, async_mode='threading')

async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)


import eventlet
eventlet.monkey_patch(os=True, select=True, socket=True, thread=False, time=True)

##########################################



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


@app.route('/xterm/<domain>', methods=['POST', 'GET'])
def xterm(domain):
    print('XTERM POST')
    inp = domain.split('R', )
    inp = int(inp[1])
    print(str(inp))
    with open('domains_xml/domains.txt') as f:
        if str(inp) in f.read():
            print('Exists')
            #data = console(domain)

            return render_template('console.html', domain = domain, data = console(domain))
        else:
            return render_template('404.html')

def console(domain):
    max_read_bytes = 1024 * 20
    while True:
        socketio.sleep(0.01)
        timeout_sec = 0
        #command = 'ls -al'
        command = 'virsh console ' + str(domain)
        command = command.replace('\n', '')
        print(app.config['fd'])
        subp = subprocess.Popen(command.split(), stdout=app.config['fd'])
        output = subp.communicate()
        socketio.emit('pty-output', output, namespace='/pty')
        return output


##########################################


def main():
    socketio.run(app, debug=True, port='5000', host='127.0.0.1')


def read_and_forward_pty_output():
    max_read_bytes = 1024 * 20
    while True:
        socketio.sleep(0.01)
        if app.config['fd']:
            timeout_sec = 0
            (data_ready, _, _) = select.select([app.config['fd']], [], [], timeout_sec)
            if data_ready:
                output = os.read(app.config['fd'], max_read_bytes).decode()
                socketio.emit('pty-output', data_ready, namespace='/pty')


def set_winsize(fd, row, col, xpix=0, ypix=0):
    winsize = struct.pack('HHHH', row, col, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


@socketio.on('pty-input', namespace='/pty')
def pty_input(data):
    if app.config['fd']:
        os.write(app.config['fd'], data['input'].encode())


@socketio.on('resize', namespace='/pty')
def resize(data):
    if app.config['fd']:
        set_winsize(app.config['fd'], data['rows'], data['cols'])


@socketio.on('connect', namespace='/pty')
def connect():
    if app.config['child_pid']:
        # already started child process, don't start another
        return

    # create child process attached to a pty we can read from and write to
    (child_pid, fd) = pty.fork()
    if child_pid == 0:
        # this is the child process fork.
        # anything printed here will show up in the pty, including the output
        # of this subprocess
        subprocess.run(app.config['cmd'])
    else:
        # this is the parent process fork.
        # store child fd and pid
        app.config['fd'] = fd
        app.config['child_pid'] = child_pid
        set_winsize(fd, 50, 50)
        cmd = ' '.join(shlex.quote(c) for c in app.config['cmd'])
        socketio.start_background_task(target=read_and_forward_pty_output)




##########################################




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
