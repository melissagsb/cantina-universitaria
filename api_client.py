# api_client.py - Importa cardápio da API

import requests
from models import Produto, db

FAKE_STORE_URL = "https://fakestoreapi.com/products"

# Cardápio da Cantina
CARDAPIO_CANTINA = [
    {"nome": "Coxinha de Frango", "categoria": "salgado", "preco_base": 6.50},
    {"nome": "Pastel de Carne", "categoria": "salgado", "preco_base": 5.50},
    {"nome": "Empada de Frango", "categoria": "salgado", "preco_base": 5.00},
    {"nome": "Esfiha de Queijo", "categoria": "salgado", "preco_base": 4.50},
    {"nome": "Hambúrguer Simples", "categoria": "lanche", "preco_base": 12.00},
    {"nome": "X-Tudo", "categoria": "lanche", "preco_base": 18.00},
    {"nome": "Suco Natural de Laranja", "categoria": "bebida", "preco_base": 5.00},
    {"nome": "Refrigerante Lata", "categoria": "bebida", "preco_base": 4.50},
    {"nome": "Água Mineral", "categoria": "bebida", "preco_base": 2.50},
    {"nome": "Brigadeiro", "categoria": "doce", "preco_base": 3.00},
    {"nome": "Pudim", "categoria": "doce", "preco_base": 6.00},
    {"nome": "Combo Lanche + Suco", "categoria": "combo", "preco_base": 15.00},
    {"nome": "Combo Coxinha + Refri", "categoria": "combo", "preco_base": 10.00},
    {"nome": "Café Expresso", "categoria": "bebida", "preco_base": 3.00},
    {"nome": "Sanduíche Natural", "categoria": "salgado", "preco_base": 8.00, "vegetariano": True},
]

def buscar_produtos_da_api():
    try:
        resposta = requests.get(FAKE_STORE_URL)
        if resposta.status_code == 200:
            return resposta.json()
        return None
    except Exception as e:
        print(f"Erro: {e}")
        return None

def importar_cardapio_para_banco():
    produtos_api = buscar_produtos_da_api()
    contador = 0
    
    for i, item_cardapio in enumerate(CARDAPIO_CANTINA):
        existe = Produto.query.filter_by(nome=item_cardapio['nome']).first()
        
        if not existe:
            imagem_url = None
            if produtos_api and i < len(produtos_api):
                imagem_url = produtos_api[i]['image']
            
            if item_cardapio['categoria'] in ['salgado', 'lanche']:
                tipo_refeicao = 'almoço'
            elif item_cardapio['categoria'] == 'doce':
                tipo_refeicao = 'lanche da tarde'
            else:
                tipo_refeicao = 'geral'
            
            novo_produto = Produto(
                nome=item_cardapio['nome'],
                descricao=f"Delicioso {item_cardapio['nome']} preparado com amor!",
                preco=item_cardapio['preco_base'],
                imagem_url=imagem_url,
                categoria=item_cardapio['categoria'],
                tipo_refeicao=tipo_refeicao,
                vegetariano=item_cardapio.get('vegetariano', False),
                estoque=50,
                api_id=i
            )
            db.session.add(novo_produto)
            contador += 1
    
    db.session.commit()
    return contador