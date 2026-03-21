from flask import Blueprint, request, jsonify
from database import db
from models import Cliente, Produto, Servico, Pacote, Venda, Atendimento, ControleSessao, Financeiro
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)

@api_bp.route('/dashboard', methods=['GET'])
def api_dashboard():
    hoje = datetime.utcnow().date()
    primeiro_dia_mes = hoje.replace(day=1)
    
    faturamento_mes = db.session.query(db.func.sum(Financeiro.valor)).filter(
        Financeiro.tipo == 'entrada', Financeiro.status == 'confirmado',
        db.func.date(Financeiro.data) >= primeiro_dia_mes
    ).scalar() or 0.0
    
    # Próximos atendimentos (de hoje em diante, não realizados, máx 10)
    proximos = db.session.query(
        Atendimento, Cliente, Servico
    ).join(Cliente, Atendimento.cliente_id == Cliente.id)\
     .join(Servico, Atendimento.servico_id == Servico.id)\
     .filter(
         db.func.date(Atendimento.data_atendimento) >= hoje,
         Atendimento.status_atendimento != 'realizado'
     )\
     .order_by(Atendimento.data_atendimento.asc())\
     .limit(10).all()

    lista_proximos = []
    for a, c, s in proximos:
        lista_proximos.append({
            'id': a.id,
            'data': a.data_atendimento.strftime('%d/%m/%y'),
            'hora': a.data_atendimento.strftime('%H:%M'),
            'cliente_nome': c.nome,
            'servico_nome': s.nome,
            'origem': a.origem,
            'status': a.status_atendimento,
            'is_hoje': a.data_atendimento.date() == hoje
        })
    
    clientes_devendo = db.session.query(Cliente)\
        .join(Venda, Venda.cliente_id == Cliente.id)\
        .join(Financeiro, Financeiro.venda_id == Venda.id)\
        .filter(
            Financeiro.status == 'pendente',
            Financeiro.tipo == 'entrada'
        ).distinct().count()
    
    return jsonify({
        'faturamento_mes': faturamento_mes,
        'proximos_atendimentos': lista_proximos,
        'clientes_devendo': clientes_devendo
    })

@api_bp.route('/clientes', methods=['GET', 'POST'])
def obj_clientes():
    if request.method == 'POST':
        data = request.json
        c = Cliente(
            nome=data.get('nome'), telefone=data.get('telefone'),
            email=data.get('email'), endereco=data.get('endereco'),
            observacoes=data.get('observacoes')
        )
        db.session.add(c)
        db.session.commit()
        return jsonify({'id': c.id}), 201
    
    filtro = request.args.get('filtro')
    query = db.session.query(Cliente)
    
    if filtro == 'com_sessoes':
        query = query.join(Venda).join(ControleSessao).filter(ControleSessao.qtd_restante > 0).distinct()
    elif filtro == 'devendo':
        # Filtro corrigido para verificar finaceiro e vendas
        query = query.join(Venda).filter(Venda.status_pagamento == 'pendente').distinct()
        
    clientes = query.all()
    res = []
    for c in clientes:
        res.append({
            'id': c.id, 'nome': c.nome, 'telefone': c.telefone, 'email': c.email,
            'endereco': c.endereco,
            'status': c.status, 'data_cadastro': c.data_cadastro.strftime('%d/%m/%y'),
            'historico_fisico': c.historico_fisico
        })
    return jsonify(res)

@api_bp.route('/clientes/<int:id>', methods=['PUT', 'DELETE'])
def obj_cliente_detail(id):
    c = Cliente.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        c.nome = data.get('nome', c.nome)
        c.telefone = data.get('telefone', c.telefone)
        c.email = data.get('email', c.email)
        c.endereco = data.get('endereco', c.endereco)
        c.observacoes = data.get('observacoes', c.observacoes)
        if 'status' in data:
            c.status = data['status']
        db.session.commit()
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        c.status = 'inativo'
        db.session.commit()
        return jsonify({'success': True})

@api_bp.route('/clientes/<int:id>/historico', methods=['GET', 'PUT'])
def cliente_historico(id):
    c = Cliente.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        c.historico_fisico = data.get('historico_fisico')
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'historico_fisico': c.historico_fisico})

@api_bp.route('/servicos', methods=['GET', 'POST'])
def obj_servicos():
    if request.method == 'POST':
        data = request.json
        s = Servico(
            nome=data.get('nome'), duracao_min=int(data.get('duracao_min')),
            preco_base=float(data.get('preco_base')), tipo=data.get('tipo', 'avulso'),
            local=data.get('local', 'Estúdio')
        )
        db.session.add(s)
        db.session.commit()
        return jsonify({'id': s.id}), 201
    res = [{'id': s.id, 'nome': s.nome, 'preco_base': s.preco_base, 'tipo': s.tipo, 'duracao_min': s.duracao_min, 'local': s.local} for s in Servico.query.all()]
    return jsonify(res)

@api_bp.route('/servicos/<int:id>', methods=['PUT', 'DELETE'])
def obj_servicos_detail(id):
    s = Servico.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        s.nome = data.get('nome', s.nome)
        if data.get('duracao_min'): s.duracao_min = int(data.get('duracao_min'))
        if data.get('preco_base'): s.preco_base = float(data.get('preco_base'))
        s.local = data.get('local', s.local)
        db.session.commit()
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        try:
            db.session.delete(s)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Este serviço já foi utilizado em pacotes ou vendas e não pode ser apagado definitivamente.'}), 400
        return jsonify({'success': True})

@api_bp.route('/produtos', methods=['GET', 'POST'])
def obj_produtos():
    if request.method == 'POST':
        data = request.json
        p = Produto(
            nome=data.get('nome'),
            preco_venda=float(data.get('preco_venda'))
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({'id': p.id}), 201
    res = [{'id': p.id, 'nome': p.nome, 'preco_venda': p.preco_venda} for p in Produto.query.all()]
    return jsonify(res)

@api_bp.route('/pacotes', methods=['GET', 'POST'])
def obj_pacotes():
    if request.method == 'POST':
        data = request.json
        p = Pacote(
            nome=data.get('nome'),
            servico_id=int(data.get('servico_id')) if data.get('servico_id') else None,
            qtd_sessoes=int(data.get('qtd_sessoes')), valor_total=float(data.get('valor_total')),
            validade_dias=int(data.get('validade_dias'))
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({'id': p.id}), 201
    
    res = []
    for p in Pacote.query.all():
        nome_item = p.servico.nome if p.servico else (p.produto.nome if p.produto else 'Item')
        res.append({
            'id': p.id, 'nome': p.nome,
            'servico_id': p.servico_id, 'produto_id': p.produto_id, 'servico_nome': nome_item,
            'qtd_sessoes': p.qtd_sessoes, 'valor_total': p.valor_total, 'validade_dias': p.validade_dias
        })
    return jsonify(res)

@api_bp.route('/pacotes/<int:id>', methods=['PUT', 'DELETE'])
def obj_pacotes_detail(id):
    p = Pacote.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        p.nome = data.get('nome', p.nome)
        if data.get('servico_id'): p.servico_id = int(data.get('servico_id'))
        if data.get('qtd_sessoes'): p.qtd_sessoes = int(data.get('qtd_sessoes'))
        if data.get('valor_total'): p.valor_total = float(data.get('valor_total'))
        if data.get('validade_dias'): p.validade_dias = int(data.get('validade_dias'))
        db.session.commit()
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        try:
            db.session.delete(p)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Não é possível excluir este pacote pois ele já possui vínculos ou vendas atreladas.'}), 400
        return jsonify({'success': True})

@api_bp.route('/vendas', methods=['GET', 'POST'])
def obj_vendas():
    if request.method == 'POST':
        data = request.json
        tipo = data.get('tipo')
        valor_total = float(data.get('valor_total'))
        status_pagamento = data.get('status_pagamento', 'pendente')
        
        v = Venda(
            cliente_id=int(data.get('cliente_id')),
            tipo=tipo,
            servico_id=int(data.get('servico_id')) if data.get('servico_id') else None,
            pacote_id=int(data.get('pacote_id')) if data.get('pacote_id') else None,
            valor_total=valor_total,
            status_pagamento=status_pagamento
        )
        db.session.add(v)
        db.session.flush() # Para pegar o v.id

        cs = None
        if tipo == 'pacote' and v.pacote_id:
            pacote = Pacote.query.get(v.pacote_id)
            if pacote:
                cs = ControleSessao(
                    venda_id=v.id,
                    qtd_total=pacote.qtd_sessoes,
                    qtd_utilizada=0,
                    qtd_restante=pacote.qtd_sessoes,
                    data_inicio=datetime.utcnow(),
                    data_validade=datetime.utcnow() + timedelta(days=pacote.validade_dias)
                )
                db.session.add(cs)
        
        # Automação 3: Registro no financeiro
        categoria_receita = 'sessao_avulsa'
        if tipo == 'pacote':
            categoria_receita = 'pacote'
        elif tipo == 'produto':
            categoria_receita = 'produto'

        fin = Financeiro(
            tipo='entrada',
            origem='venda',
            categoria_receita=categoria_receita,
            venda_id=v.id,
            valor=valor_total,
            forma_pagamento=data.get('forma_pagamento'),
            status='confirmado' if status_pagamento == 'pago' else 'pendente'
        )
        db.session.add(fin)
        
        # Automação 4: Se tiver data de agendamento, cria o Atendimento Base
        data_agendamento_str = data.get('data_agendamento')
        if data_agendamento_str:
            data_agendamento = datetime.fromisoformat(data_agendamento_str)
            status_atend = 'realizado' if data_agendamento < datetime.utcnow() else 'agendado'
                
            if tipo == 'avulso':
                atend = Atendimento(
                    cliente_id=v.cliente_id,
                    servico_id=v.servico_id,
                    data_atendimento=data_agendamento,
                    origem='avulso',
                    venda_id=v.id,
                    status_atendimento=status_atend,
                    valor=v.valor_total
                )
                db.session.add(atend)
            elif tipo == 'pacote' and cs:
                atend = Atendimento(
                    cliente_id=v.cliente_id,
                    servico_id=pacote.servico_id,
                    data_atendimento=data_agendamento,
                    origem='pacote',
                    venda_id=v.id,
                    status_atendimento=status_atend,
                    valor=0.0
                )
                db.session.add(atend)
                
                # Deduz 1 sessão imediatamente se já for realizado hoje
                if status_atend == 'realizado':
                    cs.qtd_utilizada += 1
                    cs.qtd_restante -= 1

        db.session.commit()
        return jsonify({'id': v.id}), 201

@api_bp.route('/clientes/<int:id>/pacotes_ativos', methods=['GET'])
def cliente_pacotes_ativos(id):
    cs_list = ControleSessao.query.join(Venda).filter(
        Venda.cliente_id == id,
        ControleSessao.qtd_restante > 0
    ).all()
    res = []
    for c in cs_list:
        servico_id = c.venda.pacote.servico_id if c.venda.pacote else None
        res.append({
            'venda_id': c.venda_id,
            'pacote_nome': c.venda.pacote.nome if c.venda.pacote else 'N/A',
            'qtd_restante': c.qtd_restante,
            'servico_id': servico_id
        })
    return jsonify(res)

    vendas = Venda.query.all()
    res = []
    for v in vendas:
        item = 'Item'
        if v.tipo == 'pacote' and v.pacote:
            item = v.pacote.nome
        elif v.tipo == 'avulso' and v.servico:
            item = v.servico.nome
        elif v.tipo == 'produto' and v.produto:
            item = v.produto.nome
            
        res.append({
            'id': v.id, 'cliente_nome': v.cliente.nome, 'tipo': v.tipo, 'item': item,
            'valor_total': v.valor_total, 'data_venda': v.data_venda.strftime('%d/%m/%y %H:%M'),
            'status_pagamento': v.status_pagamento
        })
    return jsonify(res)

@api_bp.route('/atendimentos', methods=['GET', 'POST'])
def obj_atendimentos():
    if request.method == 'POST':
        data = request.json
        origem = data.get('origem')
        venda_id = data.get('venda_id')
        status = data.get('status_atendimento', 'agendado')

        date_str = data.get('data_atendimento')
        if 'T' in date_str: # handle datetime local 2026-03-21T10:00
            data_atendimento = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        else:
            data_atendimento = datetime.strptime(date_str, '%Y-%m-%d %H:%M')

        a = Atendimento(
            cliente_id=int(data.get('cliente_id')),
            servico_id=int(data.get('servico_id')),
            data_atendimento=data_atendimento,
            origem=origem,
            venda_id=int(venda_id) if venda_id else None,
            status_atendimento=status,
            valor=float(data.get('valor', 0.0)),
            observacoes=data.get('observacoes')
        )
        db.session.add(a)

        # Automação 2 se for realizado na criacao
        if status == 'realizado' and origem == 'pacote' and venda_id:
            cs = ControleSessao.query.filter_by(venda_id=venda_id).first()
            if cs and cs.qtd_restante > 0:
                cs.qtd_utilizada += 1
                cs.qtd_restante -= 1

        db.session.commit()
        return jsonify({'id': a.id}), 201
    
    filtro = request.args.get('filtro')
    query = Atendimento.query
    if filtro == 'hoje':
        query = query.filter(db.func.date(Atendimento.data_atendimento) == datetime.utcnow().date())
    elif filtro == 'pendente':
        query = query.filter(Atendimento.status_atendimento != 'realizado')
    elif filtro == 'realizado':
        query = query.filter(Atendimento.status_atendimento == 'realizado')
    elif filtro == 'realizados_nao_pagos':
        query = query.join(Venda).filter(Atendimento.status_atendimento == 'realizado', Venda.status_pagamento == 'pendente')

    # Ordenação
    ordenar = request.args.get('ordenar', 'data_desc')
    if ordenar == 'data_asc':
        query = query.order_by(Atendimento.data_atendimento.asc())
    elif ordenar == 'cliente_asc':
        query = query.join(Cliente, Atendimento.cliente_id == Cliente.id).order_by(Cliente.nome.asc())
    elif ordenar == 'cliente_desc':
        query = query.join(Cliente, Atendimento.cliente_id == Cliente.id).order_by(Cliente.nome.desc())
    elif ordenar == 'servico_asc':
        query = query.join(Servico, Atendimento.servico_id == Servico.id).order_by(Servico.nome.asc())
    elif ordenar == 'servico_desc':
        query = query.join(Servico, Atendimento.servico_id == Servico.id).order_by(Servico.nome.desc())
    else:
        query = query.order_by(Atendimento.data_atendimento.desc())

    atendimentos = query.all()
    hoje = datetime.utcnow().date()
    res = []
    for a in atendimentos:
        res.append({
            'id': a.id, 'cliente_nome': a.cliente.nome, 'servico_nome': a.servico.nome,
            'data_atendimento': a.data_atendimento.strftime('%d/%m/%y %H:%M'),
            'data_raw': a.data_atendimento.strftime('%d/%m/%y'),
            'hora': a.data_atendimento.strftime('%H:%M'),
            'origem': a.origem, 'status_atendimento': a.status_atendimento,
            'venda_status': a.venda.status_pagamento if a.venda else None,
            'is_hoje': a.data_atendimento.date() == hoje
        })
    return jsonify(res)

@api_bp.route('/atendimentos/<int:id>/realizar', methods=['POST'])
def realizar_atendimento(id):
    a = Atendimento.query.get_or_404(id)
    if a.status_atendimento == 'realizado':
        return jsonify({'error': 'Ja realizado'}), 400
        
    a.status_atendimento = 'realizado'
    # Automação 2
    if a.origem == 'pacote' and a.venda_id:
        cs = ControleSessao.query.filter_by(venda_id=a.venda_id).first()
        if cs and cs.qtd_restante > 0:
            cs.qtd_utilizada += 1
            cs.qtd_restante -= 1
            
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/controle_sessoes', methods=['GET'])
def obj_controle():
    cs = ControleSessao.query.all()
    res = []
    for c in cs:
        servico_id = c.venda.pacote.servico_id if c.venda.pacote else None
        res.append({
            'id': c.id, 'cliente_id': c.venda.cliente_id, 'servico_id': servico_id, 'venda_id': c.venda_id,
            'cliente_nome': c.venda.cliente.nome, 'pacote_nome': c.venda.pacote.nome if c.venda.pacote else 'N/A',
            'qtd_total': c.qtd_total, 'qtd_utilizada': c.qtd_utilizada, 'qtd_restante': c.qtd_restante,
            'data_validade': c.data_validade.strftime('%d/%m/%y')
        })
    return jsonify(res)

@api_bp.route('/controle_sessoes/<int:id>/baixar_sessao', methods=['POST'])
def baixar_sessao(id):
    cs = ControleSessao.query.get_or_404(id)
    if cs.qtd_restante <= 0:
        return jsonify({'error': 'Não há sessões restantes neste pacote.'}), 400
        
    cs.qtd_utilizada += 1
    cs.qtd_restante -= 1
    
    # Criar registro em Atendimentos para manter o histórico
    v = Venda.query.get(cs.venda_id)
    if v and v.pacote and v.pacote.servico_id:
        a = Atendimento(
            cliente_id=v.cliente_id,
            servico_id=v.pacote.servico_id,
            data_atendimento=datetime.utcnow(),
            origem='pacote',
            venda_id=v.id,
            status_atendimento='realizado',
            valor=0.0,
            observacoes='Sessão registrada via Controle Rápido'
        )
        db.session.add(a)

    db.session.commit()
    return jsonify({'success': True, 'qtd_restante': cs.qtd_restante, 'qtd_utilizada': cs.qtd_utilizada})

@api_bp.route('/financeiro', methods=['GET', 'POST'])
def obj_financeiro():
    if request.method == 'POST':
        # Para registros manuais (ajustes/outros), pois vendas eh automatizado
        pass
    
    query = Financeiro.query

    # Filtro por status (já existente)
    if request.args.get('status'):
        query = query.filter_by(status=request.args.get('status'))

    # Filtro por busca (nome do cliente)
    busca = request.args.get('busca', '').strip()
    if busca:
        query = query.join(Venda, Financeiro.venda_id == Venda.id).join(Cliente, Venda.cliente_id == Cliente.id).filter(Cliente.nome.ilike(f'%{busca}%'))

    # Filtro por período
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Financeiro.data >= dt_inicio)
        except ValueError:
            pass
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Financeiro.data < dt_fim)
        except ValueError:
            pass

    # Filtro por origem
    if request.args.get('origem'):
        query = query.filter_by(origem=request.args.get('origem'))

    # Filtro por forma de pagamento
    if request.args.get('forma_pagamento'):
        query = query.filter_by(forma_pagamento=request.args.get('forma_pagamento'))

    # Filtro por categoria
    if request.args.get('categoria'):
        query = query.filter_by(categoria_receita=request.args.get('categoria'))

    fin = query.order_by(Financeiro.data.desc()).all()

    # Calcular resumo a partir dos registros filtrados
    total_confirmado = sum(f.valor for f in fin if f.status == 'confirmado')
    total_pendente = sum(f.valor for f in fin if f.status == 'pendente')

    res = []
    for f in fin:
        res.append({
            'id': f.id, 'tipo': f.tipo, 'origem': f.origem, 'categoria_receita': f.categoria_receita, 'valor': f.valor,
            'forma_pagamento': f.forma_pagamento, 'status': f.status,
            'data': f.data.strftime('%d/%m/%y %H:%M'),
            'cliente_nome': f.venda_origem.cliente.nome if f.venda_origem else None
        })
    return jsonify({
        'registros': res,
        'resumo': {
            'total_confirmado': total_confirmado,
            'total_pendente': total_pendente,
            'quantidade': len(res)
        }
    })

@api_bp.route('/financeiro/<int:id>/pagar', methods=['POST'])
def pagar_financeiro(id):
    f = Financeiro.query.get_or_404(id)
    f.status = 'confirmado'
    f.forma_pagamento = request.json.get('forma_pagamento', f.forma_pagamento)
    
    if f.venda_id:
        v = Venda.query.get(f.venda_id)
        if v:
            v.status_pagamento = 'pago'
            
    db.session.commit()
    return jsonify({'success': True})
