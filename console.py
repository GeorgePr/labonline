#!/usr/bin/env python3
import argparse
from flask import Flask, render_template
from flask_socketio import SocketIO
import pty
import os
import subprocess
import select
import termios
import struct
import fcntl
import shlex


app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='')
app.config['TESTING'] = True
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'secret!'
app.config['FLASK_ENV'] = 'development'
app.config['child_pid'] = None
app.config['fd'] = None
app.config['cmd'] = '/bin/zsh'
socketio = SocketIO(app)


def set_winsize(fd, row, col, xpix=0, ypix=0):
    winsize = struct.pack('HHHH', row, col, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


def read_and_forward_pty_output():
    max_read_bytes = 1024 * 20
    while True:
        socketio.sleep(0.01)
        if app.config['fd']:
            timeout_sec = 0
            (data_ready, _, _) = select.select([app.config['fd']], [], [], timeout_sec)
            if data_ready:
                output = os.read(app.config['fd'], max_read_bytes).decode()
                socketio.emit('pty-output', {'output': output}, namespace='/pty')


@app.route('/')
def index():
    return render_template('console.html')


@socketio.on('pty-input', namespace='/pty')
def pty_input(data):
    if app.config['fd']:
        # print("writing to ptd: %s" % data["input"])
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
        command = ' '.join(shlex.quote(c) for c in app.config['cmd'])
        socketio.start_background_task(target=read_and_forward_pty_output)


def main():
    socketio.run(app, debug=True, port='4000', host='127.0.0.1')


if __name__ == '__main__':
    main()
