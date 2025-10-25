import ply.lex as lex 

tokens = (
    'INT',
    'SOMA',
    'SUB',
    'DIV',
    'MULT',
    'PA',
    'PF'
)

t_SOMA = r"\+"
t_SUB = r"-"
t_DIV = r"/"
t_MULT = r"\*"
t_PA = r"\("
t_PF = r"\)"
t_ignore = '\t\n'

def t_INT(t):
    r"\d+"
    t.value = int(t.value)
    return t

def t_error(t):
    print(f"Caractere inválido. '{t.value[0]}'")
    t.lexer.skip(1)
    
lexer = lex.lex()

lista_tokens =[]
prox_elem = None
pos = 0

def parserError(simb):
    print(f"Erro sintático: token inesperado: {simb}")
    exit(1)

def rec_term(tipo):
    global prox_simb, pos
    if prox_simb.type == tipo:
        print(f"{prox_simb}")
        pos += 1
        prox_simb = lista_tokens[pos]
    else:
        parserError(prox_simb)

def rec_Exp():
    print("Reconheci P1: Exp -> Conta Exp2")
    rec_Conta()
    rec_Exp2()

def rec_Exp2():
    global prox_simb
    if prox_simb.type in ('SOMA', 'SUB', 'MULT', 'DIV'):
        rec_Op()
        rec_Conta()
        rec_Exp2()
        print("Reconheci P2: Exp2 -> Op Conta Exp2")
    elif prox_simb.type in ('PF', 'EOF'):
        print("Reconheci P3: Exp2 -> ε")
    else:
        parserError(prox_simb)

def rec_Conta():
    global prox_simb
    if prox_simb.type == 'INT':
        rec_term('INT')
        print("Reconheci P4: Conta -> int")
    elif prox_simb.type == 'PA':
        rec_term('PA')
        rec_Exp()
        rec_term('PF')
        print("Reconheci P5: Conta -> '(' Exp ')'")
    else:
        parserError(prox_simb)

def rec_Op():
    global prox_simb
    if prox_simb.type == 'SOMA':
        rec_term('SOMA')
        print("Reconheci P6: Op -> '+'")
    elif prox_simb.type == 'SUB':
        rec_term('SUB')
        print("Reconheci P7: Op -> '-'")
    elif prox_simb.type == 'MULT':
        rec_term('MULT')
        print("Reconheci P8: Op -> '*'")
    elif prox_simb.type == 'DIV':
        rec_term('DIV')
        print("Reconheci P9: Op -> '/'")
    else:
        parserError(prox_simb)

def rec_Parser(data):
    global prox_simb, lista_tokens, pos
    lexer.input(data)
    lista_tokens = list(lexer)
    lista_tokens.append(lex.LexToken())
    lista_tokens[-1].type = 'EOF'
    lista_tokens[-1].value = ''
    pos = 0
    prox_simb = lista_tokens[pos]
    rec_Exp()
    if prox_simb.type == 'EOF':
        print("\n'That's all folks!' - José Carlos Ramalho")
    else:
        parserError(prox_simb)

if __name__ == "__main__":
    data = [
        "5 + 6",
        "(7 - 2) * (8 / 3)"
    ]
    
    for exp in data:
        print(f"\n{exp}")
        rec_Parser(exp)