# app.py - Cantina Universitária (Parte 1: Configuração)

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario, Produto, Pedido, ItemPedido
from api_client import importar_cardapio_para_banco
from datetime import datetime

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = 'cantina-secret-key-troque-depois'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cantina.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
@app.route('/cardapio')
def listar_cardapio():
    categoria = request.args.get('categoria', 'todos')
    vegetariano = request.args.get('vegetariano', '')
    
    query = Produto.query.filter(Produto.estoque > 0)
    
    if categoria != 'todos':
        query = query.filter_by(categoria=categoria)
    if vegetariano == 'sim':
        query = query.filter_by(vegetariano=True)
    
    produtos = query.all()
    
    categorias = {
        'salgado': [p for p in produtos if p.categoria == 'salgado'],
        'lanche': [p for p in produtos if p.categoria == 'lanche'],
        'bebida': [p for p in produtos if p.categoria == 'bebida'],
        'doce': [p for p in produtos if p.categoria == 'doce'],
        'combo': [p for p in produtos if p.categoria == 'combo'],
    }
    
    carrinho = session.get('carrinho', {})
    total_itens = sum(carrinho.values())
    
    hora_atual = datetime.now().hour
    if 6 <= hora_atual < 10:
        mensagem_horario = "☕ Bom dia! Café da manhã servido até as 10h"
    elif 10 <= hora_atual < 14:
        mensagem_horario = "🍽️ Horário de almoço! Pratos quentes disponíveis"
    elif 14 <= hora_atual < 18:
        mensagem_horario = "🥪 Lanche da tarde - Salgados e doces"
    else:
        mensagem_horario = "🕒 Cantina fechada no momento. Pedidos para amanhã!"
    
    return render_template('cardapio.html', 
                         categorias=categorias,
                         total_itens=total_itens,
                         mensagem_horario=mensagem_horario,
                         categoria_atual=categoria,
                         vegetariano_ativo=vegetariano)

# ==================== CARRINHO ====================

@app.route('/adicionar-carrinho/<int:produto_id>')
def adicionar_carrinho(produto_id):
    carrinho = session.get('carrinho', {})
    produto_id_str = str(produto_id)
    
    if produto_id_str in carrinho:
        carrinho[produto_id_str] += 1
    else:
        carrinho[produto_id_str] = 1
    
    session['carrinho'] = carrinho
    produto = Produto.query.get(produto_id)
    flash(f'{produto.nome} adicionado ao pedido!', 'success')
    return redirect(request.referrer or url_for('listar_cardapio'))

@app.route('/carrinho')
def ver_carrinho():
    carrinho = session.get('carrinho', {})
    itens_carrinho = []
    total = 0.0
    
    for produto_id_str, quantidade in carrinho.items():
        produto = Produto.query.get(int(produto_id_str))
        if produto:
            subtotal = produto.preco * quantidade
            total += subtotal
            itens_carrinho.append({
                'produto': produto,
                'quantidade': quantidade,
                'subtotal': subtotal
            })
    
    return render_template('carrinho.html', itens=itens_carrinho, total=total)

@app.route('/remover-carrinho/<int:produto_id>')
def remover_carrinho(produto_id):
    carrinho = session.get('carrinho', {})
    produto_id_str = str(produto_id)
    
    if produto_id_str in carrinho:
        del carrinho[produto_id_str]
        session['carrinho'] = carrinho
        flash('Item removido do pedido', 'info')
    
    return redirect(url_for('ver_carrinho'))

# ==================== FINALIZAR PEDIDO ====================

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    carrinho = session.get('carrinho', {})
    
    # Calcula o total do carrinho para mostrar no formulário
    total = 0.0
    for produto_id_str, quantidade in carrinho.items():
        produto = Produto.query.get(int(produto_id_str))
        if produto:
            total += produto.preco * quantidade
    
    if not carrinho:
        flash('Seu pedido está vazio!', 'warning')
        return redirect(url_for('listar_cardapio'))
    
    if request.method == 'POST':
        total_pedido = 0.0
        itens_validos = []
        
        for produto_id_str, quantidade in carrinho.items():
            produto = Produto.query.get(int(produto_id_str))
            if produto and produto.estoque >= quantidade:
                subtotal = produto.preco * quantidade
                total_pedido += subtotal
                # Pega observação específica do produto
                obs = request.form.get(f'obs_{produto_id_str}', '')
                itens_validos.append((produto, quantidade, subtotal, obs))
            else:
                flash(f'Estoque insuficiente para {produto.nome}', 'danger')
                return redirect(url_for('ver_carrinho'))
        
        metodo_pagamento = request.form.get('metodo_pagamento', 'dinheiro')
        
        # Verifica pagamento com saldo
        if metodo_pagamento == 'saldo' and current_user.saldo < total_pedido:
            flash(f'Saldo insuficiente! Você tem R$ {current_user.saldo:.2f}', 'danger')
            return redirect(url_for('ver_carrinho'))
        
        # Cria o pedido
        pedido = Pedido(
            data=datetime.now().strftime('%Y-%m-%d'),
            hora=datetime.now().strftime('%H:%M'),
            status='pendente',
            total=total_pedido,
            metodo_pagamento=metodo_pagamento,
            usuario_id=current_user.id
        )
        db.session.add(pedido)
        db.session.flush()
        
        # Cria os itens e atualiza estoque
        for produto, quantidade, subtotal, observacao in itens_validos:
            item = ItemPedido(
                quantidade=quantidade,
                preco_unitario=produto.preco,
                observacao=observacao if observacao else None,
                pedido_id=pedido.id,
                produto_id=produto.id
            )
            db.session.add(item)
            produto.estoque -= quantidade
        
        # Debita saldo se for o caso
        if metodo_pagamento == 'saldo':
            current_user.saldo -= total_pedido
        
        db.session.commit()
        session.pop('carrinho', None)
        
        flash(f'Pedido #{pedido.id} confirmado! Total: R$ {total_pedido:.2f}', 'success')
        flash('Seu pedido está sendo preparado. Retire na cantina em 15 minutos.', 'info')
        return redirect(url_for('meus_pedidos'))
    
    # GET: mostra o formulário com o total
    return render_template('checkout_cantina.html', total=total)

# ==================== LOGIN E CADASTRO ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('listar_cardapio'))
    
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            flash(f'Bem-vindo à Cantina, {usuario.nome}!', 'success')
            return redirect(url_for('listar_cardapio'))
        else:
            flash('Email ou senha incorretos', 'danger')
    
    return render_template('login_cantina.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        if Usuario.query.filter_by(email=request.form['email']).first():
            flash('Email já cadastrado', 'danger')
            return redirect(url_for('cadastro'))
        
        if Usuario.query.filter_by(matricula=request.form['matricula']).first():
            flash('Matrícula já cadastrada', 'danger')
            return redirect(url_for('cadastro'))
        
        usuario = Usuario(
            nome=request.form['nome'],
            email=request.form['email'],
            matricula=request.form['matricula'],
            curso=request.form['curso'],
            senha=generate_password_hash(request.form['senha']),
            saldo=50.0,
            telefone=request.form.get('telefone', '')
        )
        db.session.add(usuario)
        db.session.commit()
        
        flash('Cadastro realizado! Ganhe R$ 50,00 de bônus na cantina!', 'success')
        return redirect(url_for('login'))
    
    return render_template('cadastro_cantina.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema', 'info')
    return redirect(url_for('listar_cardapio'))

# ==================== ADMIN ====================

@app.route('/admin/produto/novo', methods=['GET', 'POST'])
@login_required
def criar_produto():
    if current_user.email != 'admin@cantina.com':
        flash('Apenas administradores podem gerenciar o cardápio', 'danger')
        return redirect(url_for('listar_cardapio'))
    
    if request.method == 'POST':
        produto = Produto(
            nome=request.form['nome'],
            descricao=request.form['descricao'],
            preco=float(request.form['preco']),
            estoque=int(request.form['estoque']),
            imagem_url=request.form['imagem_url'],
            categoria=request.form['categoria'],
            tipo_refeicao=request.form['tipo_refeicao'],
            vegetariano='vegetariano' in request.form
        )
        db.session.add(produto)
        db.session.commit()
        flash(f'{produto.nome} adicionado ao cardápio!', 'success')
        return redirect(url_for('listar_cardapio'))
    
    return render_template('produto_criar_cantina.html')

# ==================== EDITAR PRODUTO ====================

@app.route('/admin/produto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    # Verifica se é admin
    if current_user.email != 'admin@cantina.com':
        flash('Apenas administradores podem editar produtos', 'danger')
        return redirect(url_for('listar_cardapio'))
    
    produto = Produto.query.get_or_404(id)
    
    if request.method == 'POST':
        produto.nome = request.form['nome']
        produto.descricao = request.form['descricao']
        produto.preco = float(request.form['preco'])
        produto.estoque = int(request.form['estoque'])
        produto.imagem_url = request.form['imagem_url']
        produto.categoria = request.form['categoria']
        produto.tipo_refeicao = request.form['tipo_refeicao']
        produto.vegetariano = 'vegetariano' in request.form
        
        db.session.commit()
        flash(f'{produto.nome} atualizado com sucesso!', 'success')
        return redirect(url_for('listar_cardapio'))
    
    return render_template('produto_editar_cantina.html', produto=produto)


# ==================== DELETAR PRODUTO ====================

@app.route('/admin/produto/deletar/<int:id>')
@login_required
def deletar_produto(id):
    # Verifica se é admin
    if current_user.email != 'admin@cantina.com':
        flash('Apenas administradores podem deletar produtos', 'danger')
        return redirect(url_for('listar_cardapio'))
    
    produto = Produto.query.get_or_404(id)
    nome = produto.nome
    db.session.delete(produto)
    db.session.commit()
    flash(f'{nome} removido do cardápio!', 'success')
    return redirect(url_for('listar_cardapio'))

@app.route('/importar-cardapio')
@login_required
def importar_cardapio():
    if current_user.email != 'admin@cantina.com':
        flash('Sem permissão', 'danger')
        return redirect(url_for('listar_cardapio'))
    
    quantidade = importar_cardapio_para_banco()
    flash(f'{quantidade} itens importados para o cardápio!', 'success')
    return redirect(url_for('listar_cardapio'))

# ==================== MEUS PEDIDOS (HISTÓRICO) ====================

@app.route('/meus-pedidos')
@login_required
def meus_pedidos():
    """Mostra o histórico de pedidos do usuário"""
    pedidos = Pedido.query.filter_by(usuario_id=current_user.id).order_by(Pedido.id.desc()).all()
    return render_template('pedidos_cantina.html', pedidos=pedidos)


# ==================== RODAR APLICAÇÃO ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        if Usuario.query.count() == 0:
            admin = Usuario(
                nome='Administrador Cantina',
                email='admin@cantina.com',
                matricula='999999',
                curso='Administração',
                senha=generate_password_hash('admin123'),
                saldo=0,
                telefone='999999999'
            )
            aluno = Usuario(
                nome='Aluno Teste',
                email='aluno@faculdade.com',
                matricula='2024001',
                curso='Ciência da Computação',
                senha=generate_password_hash('123456'),
                saldo=50.0,
                telefone='888888888'
            )
            db.session.add_all([admin, aluno])
            db.session.commit()
            print("=" * 50)
            print("✅ USUÁRIOS CRIADOS:")
            print(f"   Admin: admin@cantina.com / admin123")
            print(f"   Aluno: aluno@faculdade.com / 123456")
            print(f"   Saldo do aluno: R$ 50,00")
            print("=" * 50)
        
        if Produto.query.count() == 0:
            qtd = importar_cardapio_para_banco()
            print(f"✅ Cardápio importado: {qtd} itens")
    
    app.run(debug=True)