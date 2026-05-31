# models.py - Cantina Universitária
# Define as tabelas do banco de dados

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Tabela de Alunos/Usuários
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    matricula = db.Column(db.String(20), unique=True)
    curso = db.Column(db.String(100))
    saldo = db.Column(db.Float, default=0.0)
    telefone = db.Column(db.String(20))
    
    pedidos = db.relationship('Pedido', backref='aluno', lazy=True)

# Tabela de Produtos (itens do cardápio)
class Produto(db.Model):
    __tablename__ = 'produtos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)
    estoque = db.Column(db.Integer, default=0)
    imagem_url = db.Column(db.String(500))
    categoria = db.Column(db.String(50))
    tipo_refeicao = db.Column(db.String(30))
    vegetariano = db.Column(db.Boolean, default=False)
    api_id = db.Column(db.Integer, nullable=True)

# Tabela de Pedidos
class Pedido(db.Model):
    __tablename__ = 'pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(10))
    status = db.Column(db.String(50), default='pendente')
    total = db.Column(db.Float, default=0.0)
    metodo_pagamento = db.Column(db.String(30), default='dinheiro')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade='all, delete-orphan')

# Tabela de Itens do Pedido
class ItemPedido(db.Model):
    __tablename__ = 'itens_pedido'
    
    id = db.Column(db.Integer, primary_key=True)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    observacao = db.Column(db.String(200))
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    
    produto = db.relationship('Produto')