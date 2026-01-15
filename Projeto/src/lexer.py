import ply.lex as lex

# Palavras Reservadas 
reserved = {
    'program': 'PROGRAM',
    'begin': 'BEGIN',
    'end': 'END',
    'var': 'VAR',
    'integer': 'INTEGER',
    'boolean': 'BOOLEAN',
    'string': 'STRING',
    'array': 'ARRAY',
    'of': 'OF',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'for': 'FOR',
    'to': 'TO',
    'downto': 'DOWNTO',
    'function': 'FUNCTION',
    'procedure': 'PROCEDURE',
    'read': 'READ',
    'write': 'WRITE',
    'writeln': 'WRITELN',
    'readln': 'READLN',
    'true': 'TRUE',
    'false': 'FALSE',
    'div': 'DIV',
    'mod': 'MOD',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
}

# Tokens 
tokens = [
    # Identificadores e Literais
    'ID', 'INTEGER_CONST', 'REAL_CONST', 'STRING_CONST',

    # Operadores e Pontuação
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'ASSIGN', 'EQUAL', 'NOTEQUAL',
    'LESSTHAN', 'GREATERTHAN', 'LESSEQUAL', 'GREATEREQUAL',
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET',
    'COMMA', 'SEMICOLON', 'COLON', 'DOT', 'DOTDOT',
] + list(reserved.values())

# Expressões Regulares Simples
t_PLUS        = r'\+'
t_MINUS       = r'-'
t_TIMES       = r'\*'
t_DIVIDE      = r'\/'
t_ASSIGN      = r':='
t_EQUAL       = r'='
t_NOTEQUAL    = r'<>'
t_LESSTHAN    = r'<'
t_GREATERTHAN = r'>'
t_LESSEQUAL   = r'<='
t_GREATEREQUAL = r'>='
t_LPAREN      = r'\('
t_RPAREN      = r'\)'
t_LBRACKET    = r'\['
t_RBRACKET    = r'\]'
t_COMMA       = r','
t_SEMICOLON   = r';'
t_COLON       = r':'
t_DOTDOT      = r'\.\.'
t_DOT         = r'\.'

# Regras com Ações

# Identificadores e Palavras Reservadas
# Esta regra deve vir antes de padrões mais genéricos se houver sobreposição.
def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    t.value = t.value.lower() # Normaliza para minúsculas (Pascal é case-insensitive)
    # Verifica se é uma palavra reservada no dicionário. 
    # Se existir, o tipo torna-se a palavra reservada (ex: PROGRAM), senão ID.
    t.type = reserved.get(t.value, 'ID') 
    return t

# Constantes Reais (Suporte a notação científica e ponto flutuante)
# Deve ser definido ANTES de INTEGER para capturar a parte fracionária primeiro
def t_REAL_CONST(t):
    r'\d+(\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+' 
    t.value = float(t.value)
    return t

# Constantes Inteiras
def t_INTEGER_CONST(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Constantes String (Pascal Standard)
# Aceita strings entre aspas simples. Duas aspas simples ('') representam uma aspa na string.
def t_STRING_CONST(t):
    r"'([^']|'')*'"
    # Remove as aspas de fora e substitui '' por '
    t.value = t.value[1:-1].replace("''", "'") 
    return t

# Comentários (Ignorados)
# Suporta tanto { ... } quanto (* ... *)
def t_COMMENT(t):
    r'(\{[^}]*\})|(\(\*.*?\*\))'
    pass

# Contagem de linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Ignorar espaços e tabs
t_ignore = ' \t'

# Função auxiliar para calcular a coluna do token (útil para debugar)
def find_column(input_text, token):
    line_start = input_text.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

# Tratamento dos Erros
def t_error(t):
    col = find_column(t.lexer.lexdata, t)
    # Em vez de print, guardamos o erro na lista do lexer
    t.lexer.errors.append({
        'lineno': t.lexer.lineno,
        'col': col,
        'value': t.value[0]
    })
    t.lexer.skip(1)


# Construção do Lexer
lexer = lex.lex()

# Guardar erros 
lexer.errors = [] 

def test_lexer(data):
    """
    Função utilitária para imprimir os tokens encontrados numa string.
    """
    lexer.input(data)
    print(f"{'TOKEN TYPE':<20} {'VALUE':<20} {'LINE':<5} {'COL':<5}")
    print("-" * 50)
    while True:
        tok = lexer.token()
        if not tok:
            break
        col = find_column(data, tok)
        print(f"{tok.type:<20} {str(tok.value):<20} {tok.lineno:<5} {col:<5}")
