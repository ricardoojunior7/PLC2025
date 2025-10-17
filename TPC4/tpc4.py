import json
import ply.lex as lex
from datetime import date

STOCK = "stock.json"

tokens = (
    'LISTAR',
    'MOEDA',
    'SELECIONAR',
    'SAIR',
    'CODIGO',
    'VALOR' 
)

t_LISTAR = r'LISTAR'
t_MOEDA = r'MOEDA'
t_SELECIONAR = r'SELECIONAR'
t_SAIR = r'SAIR'
t_CODIGO = r'A\d{2}'
t_VALOR = r'((2e)|(1e)|(50c)|(20c)|(10c)|(5c)|(2c)|(1c))+'

t_ignore = " \t\n"

def t_error(t):
    print(f"maq: Token inválido -> '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

def carregar_stock():
    try:
        with open(STOCK,"r",encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("maquina: Ficheiro de stock não encontrado")
        return []

def guardar_stock(stock):
    with open(STOCK,"w", encoding="utf-8") as f:
        json.dump(stock, f, ensure_ascii=False, indent=4)
        
def listar(stock):
    print("maq:")
    print(f"{'cod':<6} | {'nome':<20} | {'quant':<8} | {'preço'}")
    print("-" * 50)
    for item in stock:
        print(f"{item['cod']:<6} | {item['nome']:<20} | {item['quant']:<8} | {item['preco']}€")

def procurar_produto(stock, cod):
    for item in stock:
        if item["cod"].upper() == cod.upper():
            return item
    return None

def processar_moedas(valores, saldo):
    for v in valores:
        if v.endswith("e"):
            saldo += float(v[:-1])
        elif v.endswith("c"):
            saldo += float(v[:-1]) * 0.01
    return round(saldo, 2)

def calcular_troco(valor):
    moedas = [2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
    troco = []
    for m in moedas:
        qtd = int(valor // m)
        if qtd > 0:
            troco.append((qtd, m))
            valor = round(valor - qtd * m, 2)
    return troco

def interpretar_comando(stock, linha, saldo):
    lexer.input(linha)
    tokens_lidos = list(lexer)

    if not tokens_lidos:
        print("maq: Comando inválido.")
        return saldo

    primeiro = tokens_lidos[0].type

    if primeiro == "LISTAR":
        listar(stock)

    elif primeiro == "MOEDA":
        valores = [t.value for t in tokens_lidos if t.type == "VALOR"]
        saldo = processar_moedas(valores, saldo)
        print(f"maq: Saldo = {int(saldo)}e{int((saldo % 1) * 100)}c")

    elif primeiro == "SELECIONAR":
        codigos = [t.value for t in tokens_lidos if t.type == "CODIGO"]
        if not codigos:
            print("maq: Código não fornecido.")
            return saldo
        cod = codigos[0]
        produto = procurar_produto(stock, cod)
        if not produto:
            print("maq: Produto inexistente.")
        elif produto["quant"] == 0:
            print("maq: Produto esgotado.")
        elif saldo < produto["preco"]:
            falta = round(produto["preco"] - saldo, 2)
            print(f"maq: Saldo insuficiente. Falta {falta:.2f}€.")
        else:
            produto["quant"] -= 1
            saldo = round(saldo - produto["preco"], 2)
            print(f'maq: Pode retirar o produto "{produto["nome"]}".')
            print(f"maq: Saldo = {int(saldo)}e{int((saldo % 1) * 100)}c")

    elif primeiro == "SAIR":
        troco = calcular_troco(saldo)
        if troco:
            troco_str = ", ".join([
                f"{q}x {int(m*100)}c" if m < 1 else f"{q}x {int(m)}e"
                for q, m in troco
            ])
            print(f"maq: Pode retirar o troco: {troco_str}.")
        print("maq: Até à próxima!")
        guardar_stock(stock)
        exit(0)

    elif primeiro == "ADICIONAR":
        elementos = linha.split()
        if len(elementos) < 5:
            print("Uso: ADICIONAR <cod> <nome> <quant> <preço>")
            return saldo
        _, cod, nome, quant, preco = elementos
        quant = int(quant)
        preco = float(preco)
        prod = procurar_produto(stock, cod)
        if prod:
            prod["quant"] += quant
        else:
            stock.append({"cod": cod, "nome": nome, "quant": quant, "preco": preco})
        print(f"maq: Produto {cod} adicionado/atualizado.")

    else:
        print("maq: Comando não reconhecido.")

    return saldo


def main():
    stock = carregar_stock()
    saldo = 0.0
    print(f"maq: {date.today()}")
    print("maq: Estou disponível para receber o seu pedido.")

    while True:
        linha = input(">> ").strip()
        saldo = interpretar_comando(stock, linha, saldo)

if __name__ == "__main__":
    main()