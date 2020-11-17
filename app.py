from flask import Flask, render_template, url_for, request, redirect
from libvirt_create import *

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html')

@app.route('/nextpage', methods=['POST', 'GET'])
def nextpage():
    if request.method == 'POST':
        num = request.form['nm']
        create_domains(num)
        return render_template('nextpage.html')
    else:
        return render_template('index.html')    

if __name__ == '__main__':
    app.run(debug=True)