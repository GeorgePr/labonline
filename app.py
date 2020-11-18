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
            print('net' + str(j))
            net_list.append(k)
        print(net_list)
        try:
            create_domains(num)
        except:
            return render_template('index.html')
        return redirect(url_for('created', number=num))
    else:
        return render_template('index.html')

@app.route('/created/<number>', methods=['POST', 'GET'])
def created(number):
    return render_template('created.html',number = number)


if __name__ == '__main__':
    app.run(debug=True)