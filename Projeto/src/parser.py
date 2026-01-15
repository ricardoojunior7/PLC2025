import ply.yacc as yacc
from lexer import tokens, find_column
import sys

# Ativa modo de depuração se necessário
DEBUG = False

# Listas globais para guardar erros e avisos de recuperação
errors = []
warnings = []

# Tabela de Precedências (Resolve Conflitos LALR)
precedence = (
    ('right', 'ELSE'), 
    ('right', 'ASSIGN'),
    ('nonassoc', 'EQUAL', 'NOTEQUAL', 'LESSTHAN', 'LESSEQUAL', 'GREATERTHAN', 'GREATEREQUAL'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'DIV', 'MOD'),
    ('right', 'NOT', 'UMINUS')
)

# Classe Node (Estrutura da AST)
class Node:
    """Representa um nó na Árvore Sintática Abstrata (AST)."""
    def __init__(self, type, children=None, leaf=None, lineno=None):
        self.type = type
        self.lineno = lineno  # Guarda a linha de origem para mensagens de erro
        
        # Garante que children é sempre uma lista válida
        if children is None:
            self.children = []
        elif isinstance(children, list):
            self.children = [c for c in children if c is not None]
        else:
            self.children = [children]
            
        self.leaf = leaf

    def __str__(self):
        return self.pretty()

    def pretty(self, level=0):
        # Exibe linha no debug se existir
        line_info = f" [L:{self.lineno}]" if self.lineno else ""
        result = " " * (level * 2) + f"{self.type}{line_info}"
        if self.leaf is not None:
            result += f": {self.leaf}"
        result += "\n"
        for child in self.children:
            if isinstance(child, Node):
                result += child.pretty(level + 1)
            else:
                result += " " * ((level + 1) * 2) + str(child) + "\n"
        return result

def p_empty(p):
    'empty :'
    p[0] = Node('Empty', [], None)

# Estrutura do Programa (Suporte Flexível)
def p_program(p):
    '''program : PROGRAM ID SEMICOLON program_block DOT'''
    p[0] = Node('Program', [p[4]], p[2], lineno=p.lineno(1))

# Regras flexíveis para os blocos
def p_program_block_vars_funcs(p):
    '''program_block : declarations function_declarations compound_statement'''
    # Caso Standard: VAR -> FUNÇÕES
    p[0] = Node('Block', [p[2], p[1], p[3]])

def p_program_block_funcs_vars(p):
    '''program_block : function_declarations declarations compound_statement'''
    # Caso Exemplo 5: FUNÇÕES -> VAR
    p[0] = Node('Block', [p[1], p[2], p[3]])

def p_program_block_vars_only(p):
    '''program_block : declarations compound_statement'''
    # Apenas VAR
    p[0] = Node('Block', [Node('FunctionDeclarations', []), p[1], p[2]])

def p_program_block_funcs_only(p):
    '''program_block : function_declarations compound_statement'''
    # Apenas FUNÇÕES
    p[0] = Node('Block', [p[1], Node('Declarations', []), p[2]])

def p_program_block_simple(p):
    '''program_block : compound_statement'''
    # Apenas CORPO
    p[0] = Node('Block', [Node('FunctionDeclarations', []), Node('Declarations', []), p[1]])


# Declarações
def p_declarations(p):
    '''declarations : VAR declaration_list
                    | empty'''
    if len(p) == 3:
        p[0] = Node('Declarations', p[2], lineno=p.lineno(1))
    else:
        p[0] = Node('Declarations', [])

def p_declaration_list(p):
    '''declaration_list : declaration_list declaration
                        | declaration'''
    if len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    else:
        p[0] = [p[1]]

def p_declaration(p):
    '''declaration : id_list COLON type SEMICOLON'''
    p[0] = Node('Declaration', [p[1], p[3]], None, lineno=p.lineno(2))

# Recuperação de Erros nas Declarações
def p_declaration_error(p):
    '''declaration : error SEMICOLON'''
    # Guarda o aviso para mostrar na tabela amarela
    msg = "Declaração inválida ignorada (VAR). Retomando no ';'."
    warnings.append({'lineno': p.lineno(1), 'msg': msg})
    
    p[0] = None 
    p.parser.errok() # Reinicia o parser usando a instância correta

def p_id_list(p):
    '''id_list : id_list COMMA ID
               | ID'''
    if len(p) == 4:
        new_id = Node('ID', [], p[3], lineno=p.lineno(3))
        p[1].children.append(new_id)
        p[0] = p[1]
    else:
        first_id = Node('ID', [], p[1], lineno=p.lineno(1))
        p[0] = Node('IDList', [first_id])

def p_type(p):
    '''type : INTEGER
            | BOOLEAN
            | STRING
            | array_type'''
    if isinstance(p[1], Node): 
        p[0] = p[1]
    else: 
        p[0] = Node('BasicType', [], p[1].lower(), lineno=p.lineno(1))

def p_array_type(p):
    '''array_type : ARRAY LBRACKET INTEGER_CONST DOTDOT INTEGER_CONST RBRACKET OF type'''
    p[0] = Node('ArrayType', [p[8]], (p[3], p[5]), lineno=p.lineno(1))


# Subprogramas
def p_function_declarations(p):
    '''function_declarations : function_declarations function_declaration
                             | function_declarations procedure_declaration
                             | function_declaration
                             | procedure_declaration'''
    if len(p) == 3:
        p[1].children.append(p[2])
        p[0] = p[1]
    else:
        p[0] = Node('FunctionDeclarations', [p[1]])

def p_function_declaration(p):
    '''function_declaration : FUNCTION ID formal_parameters COLON type SEMICOLON block SEMICOLON'''
    p[0] = Node('FunctionDeclaration', [p[3], p[5], p[7]], p[2], lineno=p.lineno(1))

def p_procedure_declaration(p):
    '''procedure_declaration : PROCEDURE ID formal_parameters SEMICOLON block SEMICOLON'''
    p[0] = Node('ProcedureDeclaration', [p[3], Node('Empty', []), p[5]], p[2], lineno=p.lineno(1))

def p_block(p):
    '''block : declarations compound_statement'''
    p[0] = Node('Block', [Node('FunctionDeclarations', []), p[1], p[2]])

def p_formal_parameters(p):
    '''formal_parameters : LPAREN parameter_list RPAREN
                         | empty'''
    if len(p) == 4:
        p[0] = Node('FormalParameters', p[2])
    else:
        p[0] = Node('FormalParameters', [])

def p_parameter_list(p):
    '''parameter_list : parameter_list SEMICOLON parameter
                      | parameter'''
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    else:
        p[0] = [p[1]]

def p_parameter(p):
    '''parameter : id_list COLON type'''
    p[0] = Node('Parameter', [p[1], p[3]], None, lineno=p.lineno(2))

# Comandos (Statements) e Recuperação de Erro
def p_compound_statement(p):
    '''compound_statement : BEGIN statement_list END'''
    p[0] = Node('CompoundStatement', p[2], lineno=p.lineno(1))

def p_statement_list(p):
    '''statement_list : statement_list SEMICOLON statement
                      | statement'''
    if len(p) == 4:
        if p[3]: 
            p[1].append(p[3])
        p[0] = p[1]
    else:
        p[0] = [p[1]] if p[1] else []

def p_statement(p):
    '''statement : assignment_statement
                 | if_statement
                 | while_statement
                 | for_statement
                 | procedure_call
                 | compound_statement
                 | read_statement
                 | write_statement
                 | empty'''
    p[0] = p[1]

# Recuperação de erro no bloco de instruções
def p_statement_error(p):
    '''statement : error SEMICOLON'''
    # Guarda o aviso para mostrar na tabela amarela
    msg = "Instrução inválida ignorada. Retomando no ';'."
    warnings.append({'lineno': p.lineno(1), 'msg': msg})
    
    p[0] = None 
    p.parser.errok() # Reinicia o parser usando a instância correta

def p_assignment_statement(p):
    '''assignment_statement : variable ASSIGN expression'''
    p[0] = Node('AssignmentStatement', [p[1], p[3]], None, lineno=p.lineno(2))

def p_if_statement(p):
    '''if_statement : IF expression THEN statement
                    | IF expression THEN statement ELSE statement'''
    if len(p) == 5:
        p[0] = Node('IfStatement', [p[2], p[4]], None, lineno=p.lineno(1))
    else:
        p[0] = Node('IfStatement', [p[2], p[4], p[6]], None, lineno=p.lineno(1))

def p_while_statement(p):
    '''while_statement : WHILE expression DO statement'''
    p[0] = Node('WhileStatement', [p[2], p[4]], None, lineno=p.lineno(1))

def p_for_statement(p):
    '''for_statement : FOR ID ASSIGN expression TO expression DO statement
                     | FOR ID ASSIGN expression DOWNTO expression DO statement'''
    direction = p[5] 
    var_node = Node('VariableAccess', [], p[2], lineno=p.lineno(2))
    p[0] = Node('ForStatement', [var_node, p[4], p[6], p[8]], direction, lineno=p.lineno(1))

# I/O e Chamadas
def p_read_statement(p):
    '''read_statement : READ LPAREN variable_list RPAREN
                      | READLN LPAREN variable_list RPAREN'''
    p[0] = Node('ReadStatement', p[3], p[1].upper(), lineno=p.lineno(1))

def p_write_statement(p):
    '''write_statement : WRITE LPAREN expression_list RPAREN
                       | WRITELN LPAREN expression_list RPAREN'''
    p[0] = Node('WriteStatement', p[3], p[1].upper(), lineno=p.lineno(1))

def p_procedure_call(p):
    '''procedure_call : ID LPAREN expression_list RPAREN
                      | ID LPAREN RPAREN'''
    if len(p) == 5:
        p[0] = Node('ProcedureCall', [Node('ArgList', p[3])], p[1], lineno=p.lineno(1))
    else:
        p[0] = Node('ProcedureCall', [], p[1], lineno=p.lineno(1))

# Listas auxiliares
def p_variable_list(p):
    '''variable_list : variable_list COMMA variable
                      | variable'''
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    else:
        p[0] = [p[1]]

def p_expression_list(p):
    '''expression_list : expression_list COMMA expression
                       | expression'''
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    else:
        p[0] = [p[1]]

# Expressões
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression DIV expression
                  | expression MOD expression
                  | expression OR expression
                  | expression AND expression
                  | expression EQUAL expression
                  | expression NOTEQUAL expression
                  | expression LESSTHAN expression
                  | expression GREATERTHAN expression
                  | expression LESSEQUAL expression
                  | expression GREATEREQUAL expression'''
    p[0] = Node('BinaryOp', [p[1], p[3]], p[2].upper(), lineno=p.lineno(2))

def p_expression_unary(p):
    '''expression : NOT expression
                  | MINUS expression %prec UMINUS'''
    token = p[1].upper() if p[1] == 'not' else 'MINUS'
    p[0] = Node('UnaryOp', [p[2]], token, lineno=p.lineno(1))

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_simple(p):
    '''expression : variable
                  | INTEGER_CONST
                  | REAL_CONST
                  | STRING_CONST
                  | function_call
                  | TRUE
                  | FALSE'''
    
    if isinstance(p[1], Node):
        p[0] = p[1]
    else:
        token_type = p.slice[1].type
        
        if token_type == 'STRING_CONST':
            p[0] = Node('StringConstant', [], p[1], lineno=p.lineno(1))
        elif token_type == 'INTEGER_CONST':
            p[0] = Node('IntegerConstant', [], p[1], lineno=p.lineno(1))
        elif token_type == 'REAL_CONST':
            p[0] = Node('RealConstant', [], p[1], lineno=p.lineno(1))
        elif token_type in ['TRUE', 'FALSE']:
            p[0] = Node('BooleanConstant', [], p[1], lineno=p.lineno(1))
        else:
            p[0] = Node('NumericConst', [], p[1], lineno=p.lineno(1))

def p_function_call(p):
    '''function_call : ID LPAREN expression_list RPAREN
                     | ID LPAREN RPAREN'''
    if len(p) == 5:
        p[0] = Node('FunctionCall', [Node('ArgList', p[3])], p[1], lineno=p.lineno(1))
    else:
        p[0] = Node('FunctionCall', [], p[1], lineno=p.lineno(1))

def p_variable(p):
    '''variable : ID
                | ID LBRACKET expression RBRACKET'''
    if len(p) == 2:
        p[0] = Node('VariableAccess', [], p[1], lineno=p.lineno(1))
    else:
        p[0] = Node('ArrayAccess', [p[3]], p[1], lineno=p.lineno(1))


# Tratamento de Erros Globais
def p_error(p):
    if p:
        # Calcular a coluna exata usando a função do lexer
        col = find_column(p.lexer.lexdata, p)
        
        error_msg = f"Token inesperado '{p.value}'"
        dica = ""
        if p.type == 'SEMICOLON':
            dica = "Dica: Pode ter esquecido um 'end' ou ter um ';' a mais."
        elif p.value == 'var':
            dica = "Dica: Verifique a ordem das declarações (Program -> Function -> Var -> Begin)."
        
        errors.append({
            'lineno': p.lineno,
            'col': col,
            'token': p.value,
            'msg': error_msg,
            'dica': dica
        })
    else:
        errors.append({
            'lineno': 'FIM',
            'col': '?',
            'token': 'EOF',
            'msg': "Fim de arquivo inesperado. (Falta 'end.'?)",
            'dica': ""
        })

# Criação do Parser
parser = yacc.yacc(debug=DEBUG, start='program')

# Função Wrapper para o main.py chamar
def parse(data):
    global errors, warnings
    errors.clear() # Limpa erros anteriores
    warnings.clear() # Limpa avisos anteriores
    result = parser.parse(data)
    # Retorna 3 valores: AST, Erros Fatais e Avisos de Recuperação
    return result, errors, warnings