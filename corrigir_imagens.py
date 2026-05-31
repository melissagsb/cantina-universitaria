# corrigir_imagens.py
from app import app
from models import db, Produto

with app.app_context():
    # Dicionário com nome do produto e URL da imagem correta
    imagens_corretas = {
        "Coxinha de Frango": "https://img.freepik.com/fotos-gratis/coxinha-de-frango-frita_2829-10663.jpg",
        "Pastel de Carne": "https://cdn.panelinha.com.br/receita/1650116377050-pastel-de-carne-moida.jpg",
        "Empada de Frango": "https://s2-receitas.glbimg.com/CaJGkpDe_0KmNXRFl2AEIVpkOHI=/0x0:1200x800/984x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_1f540e0b94d8437dbbcba1d9a5e8c4d2/internal_photos/bs/2021/n/X/SoX8WLTkOIpoZzyVZKVQ/empada-de-frango.jpg",
        "Esfiha de Queijo": "https://img.freepik.com/fotos-gratis/esfiha-de-queijo-assada_2829-10645.jpg",
        "Hambúrguer Simples": "https://img.freepik.com/fotos-gratis/hamburguer-suculento-com-ingredientes-frescos_23-2150863473.jpg",
        "X-Tudo": "https://s2-receitas.glbimg.com/8C9OvjuV0acOBZzO-6G2Y_2zW-A=/0x0:1200x800/984x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_1f540e0b94d8437dbbcba1d9a5e8c4d2/internal_photos/bs/2022/l/2/WfJDHHSCuPoZLtkbWHig/x-tudo.jpg",
        "Suco Natural de Laranja": "https://img.freepik.com/fotos-gratis/suco-de-laranja-fresco-em-um-copo_144627-16019.jpg",
        "Refrigerante Lata": "https://img.freepik.com/fotos-gratis/latas-de-refrigerante-em-uma-fileira_144627-12946.jpg",
        "Água Mineral": "https://img.freepik.com/fotos-gratis/garrafa-de-agua-mineral_144627-14967.jpg",
        "Brigadeiro": "https://img.freepik.com/fotos-gratis/brigadeiros-de-chocolate-em-um-prato_2829-10644.jpg",
        "Pudim": "https://s2-receitas.glbimg.com/FT9gTt7NnlRrK4Pi4gR9SS0qD2w=/0x0:1200x800/984x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_1f540e0b94d8437dbbcba1d9a5e8c4d2/internal_photos/bs/2021/B/Z/CfSmKvSpKOGxN4ey0DWA/pudim.jpg",
        "Combo Lanche + Suco": "https://img.freepik.com/fotos-gratis/combo-de-fast-food-hamburguer-e-batata-frita_23-2150894041.jpg",
        "Combo Coxinha + Refri": "https://img.freepik.com/fotos-gratis/combo-de-salgados-e-refrigerante_23-2150894042.jpg",
        "Café Expresso": "https://img.freepik.com/fotos-gratis/xicara-de-cafe-fresco_144627-16590.jpg",
        "Sanduíche Natural": "https://img.freepik.com/fotos-gratis/sanduiche-natural-com-queijo-e-alface_2829-10646.jpg"
    }
    
    # Atualiza cada produto
    for nome, url in imagens_corretas.items():
        produto = Produto.query.filter_by(nome=nome).first()
        if produto:
            produto.imagem_url = url
            print(f"✅ Atualizado: {nome}")
        else:
            print(f"❌ Não encontrado: {nome}")
    
    db.session.commit()
    print("\n🎉 Todas as imagens foram atualizadas!")