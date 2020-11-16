from flask import Flask, render_template, url_for, request, redirect
import libvirt_create

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        num = request.form['nm']
        print(num)
        create_domains(num)
        return redirect(url_for('num', nm=num))
    else:
        return render_template('index.html')

@app.route('/<nm>')
def num(nm):
    return f'<h1>{nm}</h1>'

if __name__ == '__main__':
    app.run(debug=True)