from app import app
from database import db
from models import Servico, Pacote

with app.app_context():
    # Cria as tabelas se não existirem
    db.create_all()

    # Adiciona serviços iniciais se não houver
    if not Servico.query.first():
        s1 = Servico(nome="Massagem Relaxante", duracao_min=60, preco_base=120.0, tipo="avulso")
        s2 = Servico(nome="Drenagem Linfática", duracao_min=50, preco_base=100.0, tipo="avulso")
        s3 = Servico(nome="Massagem Terapêutica", duracao_min=60, preco_base=150.0, tipo="avulso")
        db.session.add_all([s1, s2, s3])
        db.session.commit()

        # Adiciona pacotes
        p1 = Pacote(nome="Pacote 10 Drenagens", servico_id=s2.id, qtd_sessoes=10, valor_total=850.0, validade_dias=90)
        p2 = Pacote(nome="Pacote 5 Relaxantes", servico_id=s1.id, qtd_sessoes=5, valor_total=500.0, validade_dias=60)
        db.session.add_all([p1, p2])
        db.session.commit()
    
    print("Database seeded with sample services and packages.")
