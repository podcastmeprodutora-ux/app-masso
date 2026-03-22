import os
from flask import Flask, render_template, request, jsonify
from database import db, init_db
from models import Cliente, Produto, Servico, Pacote, Venda, Atendimento, ControleSessao, Financeiro
from datetime import datetime, timedelta
from flask_basicauth import BasicAuth

app = Flask(__name__)

# Configuração de Autenticação
app.config['BASIC_AUTH_USERNAME'] = 'mlopes'
app.config['BASIC_AUTH_PASSWORD'] = 'LuaGorda5@s'
app.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(app)

# --- CONFIGURAÇÃO DO BANCO DE DADOS DINÂMICO ---
# Ele tenta pegar a chave do Render. Se não existir, usa o sqlite local.
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///masso.db'
# -----------------------------------------------

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super_secret_key'

init_db(app)

from api import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

# -----------------
# INTERFACE ROUTES
# -----------------

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/clientes')
def clientes():
    return render_template('clientes.html')

@app.route('/agenda')
def agenda():
    return render_template('agenda.html')

@app.route('/financeiro')
def financeiro():
    return render_template('financeiro.html')

@app.route('/servicos')
def servicos():
    return render_template('servicos.html')


# (API dashboard via blueprint)

if __name__ == '__main__':
    app.run(debug=False, port=5000)
