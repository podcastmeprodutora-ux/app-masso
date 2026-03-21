import os
from app import app
from database import db
import sqlite3

# Initialize new tables (Produto)
with app.app_context():
    db.create_all()

# Alter existing tables
db_path = os.path.join(app.instance_path, 'masso.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE clientes ADD COLUMN historico_fisico TEXT")
    except Exception as e:
        print("clientes.historico_fisico:", e)
        
    try:
        c.execute("ALTER TABLE vendas ADD COLUMN produto_id INTEGER REFERENCES produtos(id)")
    except Exception as e:
        print("vendas.produto_id:", e)
        
    try:
        c.execute("ALTER TABLE pacotes ADD COLUMN produto_id INTEGER REFERENCES produtos(id)")
    except Exception as e:
        print("pacotes.produto_id:", e)
        
    try:
        c.execute("ALTER TABLE financeiro ADD COLUMN categoria_receita VARCHAR(20)")
    except Exception as e:
        print("financeiro.categoria_receita:", e)
        
    try:
        c.execute("ALTER TABLE servicos ADD COLUMN local VARCHAR(50)")
    except Exception as e:
        print("servicos.local:", e)
        
    conn.commit()
    conn.close()
    print("Migração concluída.")
else:
    print("Banco de dados não encontrado em", db_path)
