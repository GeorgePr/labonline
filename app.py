from flask import Flask, render_template, url_for, request, redirect
from libvirt_create import *

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        num = request.form['nm']
        net_list = []
        for j in range(1, int(num)+1):
            k = request.form['net' + str(j)]
            net_list.append(k)
        print(net_list)
        try:
            create_domains(num, net_list)
        except:
            return redirect(url_for('index'))
        return redirect(url_for('created', number=num, net_list=net_list))
    else:
        return render_template('index.html')

@app.route('/created/<number>/<net_list>', methods=['POST', 'GET'])
def created(number, net_list):
    return render_template('created.html',number = number, net_list=net_list)
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')