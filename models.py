from database import db
from datetime import datetime

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.String(255))
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='ativo') # ativo, inativo
    historico_fisico = db.Column(db.Text)
    
    # Relacionamentos
    vendas = db.relationship('Venda', backref='cliente', lazy=True)
    atendimentos = db.relationship('Atendimento', backref='cliente', lazy=True)

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco_venda = db.Column(db.Float, nullable=False)

class Servico(db.Model):
    __tablename__ = 'servicos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    duracao_min = db.Column(db.Integer, nullable=False)
    preco_base = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # avulso, pacote
    local = db.Column(db.String(50), default='Estúdio') # ex: Domicílio, Praia, Estúdio

class Pacote(db.Model):
    __tablename__ = 'pacotes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    qtd_sessoes = db.Column(db.Integer, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    validade_dias = db.Column(db.Integer, nullable=False)
    
    # Relacionamento
    servico = db.relationship('Servico', backref='pacotes_vinculados', lazy=True)
    produto = db.relationship('Produto', backref='pacotes_vinculados', lazy=True)

class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # avulso, pacote
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    pacote_id = db.Column(db.Integer, db.ForeignKey('pacotes.id'), nullable=True)
    valor_total = db.Column(db.Float, nullable=False)
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)
    status_pagamento = db.Column(db.String(20), default='pendente') # pago, pendente
    
    # Relacionamentos
    servico = db.relationship('Servico', backref='vendas_servico', lazy=True)
    produto = db.relationship('Produto', backref='vendas_produto', lazy=True)
    pacote = db.relationship('Pacote', backref='vendas_pacote', lazy=True)
    atendimentos = db.relationship('Atendimento', backref='venda', lazy=True)
    controle_sessoes = db.relationship('ControleSessao', backref='venda', uselist=False, lazy=True)
    financeiro = db.relationship('Financeiro', backref='venda_origem', lazy=True)

class Atendimento(db.Model):
    __tablename__ = 'atendimentos'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    data_atendimento = db.Column(db.DateTime, nullable=False)
    origem = db.Column(db.String(20), nullable=False) # avulso, pacote
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=True)
    status_atendimento = db.Column(db.String(20), default='agendado') # agendado, realizado, cancelado
    valor = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text)
    
    # Relacionamento
    servico = db.relationship('Servico', backref='atendimentos_servico', lazy=True)

class ControleSessao(db.Model):
    __tablename__ = 'controle_sessoes'
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    qtd_total = db.Column(db.Integer, nullable=False)
    qtd_utilizada = db.Column(db.Integer, default=0)
    qtd_restante = db.Column(db.Integer, nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_validade = db.Column(db.DateTime, nullable=False)

class Financeiro(db.Model):
    __tablename__ = 'financeiro'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False) # entrada, saida
    origem = db.Column(db.String(20), nullable=False) # venda, ajuste, outros
    categoria_receita = db.Column(db.String(20), nullable=True) # produto, sessao_avulsa, pacote
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=True)
    valor = db.Column(db.Float, nullable=False)
    forma_pagamento = db.Column(db.String(20), nullable=True) # pix, dinheiro, cartao, null pendente
    data = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente') # confirmado, pendente
