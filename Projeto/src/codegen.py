class CodeGenerator:
    """
    Módulo final do compilador: Traduz a AST para instruções da VM (EWVM).
    Responsabilidades:
    1. Gerir alocação de endereços (Globais vs Locais).
    2. Traduzir controlo de fluxo (If/While) para Saltos e Labels.
    3. Gerar instruções de pilha (PUSH, STORE, OP).
    """
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.code = []
        self.label_counter = 0
        self.variable_offsets = {} # Mapa: Nome -> Endereço (Offset)
        self.current_offset = 0 # Próximo endereço livre no escopo atual
        self.procedure_starts = {} # Mapa: Nome Função -> Label de Início (ex: "soma" -> "L5")

    def generate(self, ast):
        self.visit(ast)
        return self.code

    def emit(self, instruction):
        self.code.append(instruction)

    def create_label(self):
        """Gera uma etiqueta única (L0, L1...) para usar em JUMP/JZ."""
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    # Padrão Visitor
    def visit(self, node):
        if not node: return
        method_name = f'generate_{node.type}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for child in node.children:
            self.visit(child)

    # Helpers de Contexto e Memória
    def _is_local(self):
        """
        Deteta se estamos a gerar código para dentro de uma função.
        Lógica: Se a variável especial '$return' existe no mapa de offsets, 
        é porque estamos no escopo de uma função.
        """
        return '$return' in self.variable_offsets

    def _emit_var_addr(self, offset):
        """
        Gera instruções para colocar o endereço de memória de uma variável na pilha.
        Usa FP (Frame Pointer) para locais/params e GP (Global Pointer) para globais.
        """
        if offset < 0 or self._is_local():
            self.emit("PUSHFP") 
        else:
            self.emit("PUSHGP")
        self.emit(f"PUSHI {offset}")
        self.emit("PADD") # Soma Base + Offset para obter o endereço final

    # Estrutura do Programa
    def generate_Program(self, node):
        self.emit("PUSHI 0") # Espaço para valor de retorno do programa (não usado, mas padrão)
        self.emit("PUSHI 0") # Espaço para argumentos de linha de comando
        self.emit("START")
        self.visit(node.children[0]) # Visita o bloco principal
        self.emit("STOP")

    def generate_Block(self, node):
        # Estratégia: 
        # 1. Alocar globais.
        # 2. Saltar por cima das funções (para não as executar linearmente).
        # 3. Definir as funções.
        # 4. Executar o corpo principal (Main).
        
        self.visit(node.children[1]) # Processa Declarações Globais (aloca espaço)
        
        lbl_main = self.create_label()
        self.emit(f"JUMP {lbl_main}")
        
        self.visit(node.children[0]) # Gera código das Funções/Procedimentos
        
        self.emit(f"{lbl_main}:") # Início do Main
        self.visit(node.children[2]) # Gera código do corpo principal

    def generate_Declarations(self, node):
        """Calcula espaço total necessário para variáveis e reserva na pilha (PUSHN)."""
        total_space = 0
        if node.children:
            decls = node.children if isinstance(node.children, list) else []
            for decl in decls:
                 if decl.type == 'Declaration':
                     total_space += self.process_declaration(decl)
        
        if total_space > 0:
            self.emit(f"PUSHN {total_space}")

    def process_declaration(self, node):
        """Regista offsets das variáveis e calcula tamanho (suporta arrays)."""
        id_list = node.children[0]
        type_node = node.children[1]
        
        # Calcula tamanho do tipo (1 para simples, N para arrays)
        size = 1 
        if type_node.type == 'ArrayType':
             r_min, r_max = type_node.leaf
             size = (r_max - r_min) + 1

        ids = id_list.children if id_list.type == 'IDList' else [id_list]
        
        # Atribui offset a cada variável declarada
        for id_node in ids:
            var_name = id_node.leaf
            self.variable_offsets[var_name] = self.current_offset
            self.current_offset += size
            
        return size * len(ids) # Retorna espaço total usado nesta declaração

    # Subprogramas
    def generate_FunctionDeclarations(self, node):
        for child in node.children:
            self.visit(child)

    def generate_ProcedureDeclaration(self, node):
        self._generate_subprogram(node, is_function=False)

    def generate_FunctionDeclaration(self, node):
        self._generate_subprogram(node, is_function=True)

    def _generate_subprogram(self, node, is_function):
        name = node.leaf
        params = node.children[0]
        body = node.children[2]

        # Cria e emite Label de entrada da função
        lbl = self.create_label()
        self.procedure_starts[name] = lbl
        self.emit(f"{lbl}:")

        # Context Switch
        # Salva offsets do escopo anterior (global ou pai)
        old_offset = self.current_offset
        old_vars = self.variable_offsets.copy()
        self.variable_offsets = {} 

        # Mapear PARÂMETROS (Offsets Negativos)
        # Na pilha: [Arg1, Arg2, ... , FP, PC]
        # O último argumento empilhado está logo antes do FP, ou seja, offset -1 (dependendo da VM)
        flat_params = []
        if params.children:
             for param in params.children:
                 id_list = param.children[0]
                 ids = id_list.children if id_list.type == 'IDList' else [id_list]
                 for id_node in ids:
                     flat_params.append(id_node.leaf)
        
        p_offset = -1
        # Percorre reverso para mapear corretamente (ArgN em -1, ArgN-1 em -2...)
        for param_name in reversed(flat_params):
            self.variable_offsets[param_name] = p_offset
            p_offset -= 1

        # Variáveis LOCAIS (Offsets Positivos)
        self.current_offset = 0 
        if is_function:
            # Variável mágica para o valor de retorno (offset 0)
            self.variable_offsets['$return'] = self.current_offset
            self.variable_offsets[name] = self.current_offset 
            self.current_offset += 1
            self.emit("PUSHI 0") # Inicializa retorno com 0

        self.visit(body) # Gera o código do corpo da função

        # Epílogo
        if is_function:
            # Coloca o valor de retorno no topo da pilha antes de sair
            self.emit(f"PUSHL {self.variable_offsets['$return']}")

        self.emit("RETURN")
        
        # Restaura contexto anterior
        self.current_offset = old_offset
        self.variable_offsets = old_vars

    # Estruturas de Controlo
    def generate_CompoundStatement(self, node):
        for child in node.children:
            self.visit(child)

    def generate_IfStatement(self, node):
        lbl_else = self.create_label()
        lbl_end = self.create_label()
        
        self.visit(node.children[0]) # Gera código da condição
        self.emit(f"JZ {lbl_else}")  # Se 0 (falso), salta para o Else
        
        self.visit(node.children[1]) # Bloco Then
        self.emit(f"JUMP {lbl_end}") # Salta por cima do Else
        
        self.emit(f"{lbl_else}:")
        if len(node.children) > 2:
            self.visit(node.children[2]) # Bloco Else
            
        self.emit(f"{lbl_end}:")

    def generate_WhileStatement(self, node):
        lbl_start = self.create_label()
        lbl_end = self.create_label()
        
        self.emit(f"{lbl_start}:")
        self.visit(node.children[0]) # Condição
        self.emit(f"JZ {lbl_end}")   # Se falso, sai do loop
        
        self.visit(node.children[1]) # Corpo
        self.emit(f"JUMP {lbl_start}") # Volta ao início
        
        self.emit(f"{lbl_end}:")

    def generate_ForStatement(self, node):
        # Inicialização
        var_node = node.children[0]
        name = var_node.leaf
        offset = self.variable_offsets.get(name)
        direction = node.leaf # 'to' ou 'downto'
        
        # Determina se é variável local ou global
        is_stack = self._is_local() or offset < 0
        instr_store = f"STOREL {offset}" if is_stack else f"STOREG {offset}"
        instr_push = f"PUSHL {offset}" if is_stack else f"PUSHG {offset}"

        self.visit(node.children[1]) # Valor inicial
        self.emit(instr_store)

        # Teste e Corpo
        lbl_loop = self.create_label()
        lbl_end = self.create_label()

        self.emit(f"{lbl_loop}:")
        self.emit(instr_push)        # Carrega variável de controlo
        self.visit(node.children[2]) # Carrega limite
        
        # Comparação (<= para to, >= para downto)
        if direction == 'to': self.emit("INFEQ")
        else: self.emit("SUPEQ")
        self.emit(f"JZ {lbl_end}") # Se condição falhar, sai

        self.visit(node.children[3]) # Executa corpo

        # Atualização (Passo)
        self.emit(instr_push)
        self.emit("PUSHI 1")
        if direction == 'to': self.emit("ADD")
        else: self.emit("SUB")
        self.emit(instr_store)
        
        self.emit(f"JUMP {lbl_loop}")
        self.emit(f"{lbl_end}:")

    # Acessos (Arrays e Strings)
    def generate_ArrayAccess(self, node):
        name = node.leaf
        info = self.symbol_table.lookup(name)
        
        # Caso Especial: Strings (Usa CHARAT em vez de LOAD)
        if info and info.get('type') == 'string':
            offset = self.variable_offsets.get(name)
            if self._is_local() or offset < 0:
                self.emit(f"PUSHL {offset}")
            else:
                self.emit(f"PUSHG {offset}")
            
            # Índice (ajuste 1-based do Pascal)
            self.visit(node.children[0])
            self.emit("PUSHI 1")
            self.emit("SUB")
            
            self.emit("CHARAT") 
            return

        # Arrays Normais: Calcula endereço e carrega valor
        self._calc_array_addr(node)
        self.emit("LOAD 0") 

    def _calc_array_addr(self, node):
        """Calcula o endereço de memória absoluto de um elemento do array."""
        name = node.leaf
        offset = self.variable_offsets.get(name)
        self._emit_var_addr(offset) # Coloca endereço base na pilha
        
        self.visit(node.children[0]) # Coloca índice na pilha
        
        # Ajuste do limite inferior (ex: array[10..20], índice 10 vira offset 0)
        info = self.symbol_table.lookup(name)
        if info and isinstance(info.get('type'), dict):
             r_min = info['type']['range'][0]
             if r_min != 0:
                 self.emit(f"PUSHI {r_min}")
                 self.emit("SUB")
        
        self.emit("PADD") # Endereço Final = Base + (Índice - LimiteInferior)

    # Operações e Atribuições
    def generate_AssignmentStatement(self, node):
        var_node = node.children[0]
        expr = node.children[1]

        if var_node.type == 'ArrayAccess':
            # Atribuição a Array: array[i] := expr
            self._calc_array_addr(var_node) # Calcula destino
            self.visit(expr)                # Calcula valor
            self.emit("STORE 0")            # Guarda valor no endereço
        else:
            # Atribuição Simples: var := expr
            self.visit(expr)
            name = var_node.leaf
            off = self.variable_offsets.get(name)
            if self._is_local() or off < 0:
                self.emit(f"STOREL {off}")
            else:
                self.emit(f"STOREG {off}")

    def generate_ReadStatement(self, node):
        for var in node.children:
            if var.type == 'ArrayAccess':
                self._calc_array_addr(var) # Prepara endereço se for array
            
            self.emit("READ") # Lê input do utilizador
            
            # Converte para inteiro se necessário (simplificação)
            var_name = var.leaf
            info = self.symbol_table.lookup(var_name)
            is_int = True
            if info:
                t = info['type']
                if isinstance(t, dict) and t.get('kind') == 'array':
                    if t.get('elem_type') != 'integer': is_int = False
                elif t == 'string': is_int = False
            
            if is_int: self.emit("ATOI") # ASCII to Integer

            if var.type == 'ArrayAccess':
                self.emit("STORE 0")
            else:
                off = self.variable_offsets.get(var_name)
                if self._is_local() or off < 0:
                    self.emit(f"STOREL {off}")
                else:
                    self.emit(f"STOREG {off}")

    def generate_VariableAccess(self, node):
        name = node.leaf
        offset = self.variable_offsets.get(name)
        if offset is not None:
            if self._is_local() or offset < 0:
                self.emit(f"PUSHL {offset}")
            else:
                self.emit(f"PUSHG {offset}")

    def generate_WriteStatement(self, node):
        for expr in node.children:
            self.visit(expr)
            # Decide se escreve String ou Inteiro
            if expr.type == 'StringConstant': self.emit("WRITES")
            else: self.emit("WRITEI")

    def generate_FunctionCall(self, node):
        name = node.leaf
        if name.lower() == 'length':
            if node.children:
                self.visit(node.children[0].children[0]) # Visita argumento
            self.emit("STRLEN")
            return

        # Avalia argumentos e coloca na pilha
        if node.children:
            for arg in node.children[0].children:
                self.visit(arg)
        
        # Salta para a função
        lbl = self.procedure_starts.get(name)
        if lbl:
            self.emit(f"PUSHA {lbl}")
            self.emit("CALL")

    def generate_BinaryOp(self, node):
        left = node.children[0]
        right = node.children[1]
        
        # Otimização: Comparação direta com Char literal em Strings
        # Ex: str[i] = 'a'
        if (node.leaf == '=' or node.leaf == '<>') and \
           right.type == 'StringConstant' and len(right.leaf) == 1:
                self.visit(left)
                self.emit(f"PUSHI {ord(right.leaf)}") # Converte char para int
                if node.leaf == '=': self.emit("EQUAL")
                else: 
                    self.emit("EQUAL")
                    self.emit("NOT")
                return

        self.visit(left)
        self.visit(right)
        ops = {'+':'ADD', '-':'SUB', '*':'MUL', 'DIV':'DIV', 'MOD':'MOD', 
               '=':'EQUAL', '<':'INF', '>':'SUP', '<=': 'INFEQ', '>=':'SUPEQ', 
               'AND':'AND', 'OR':'OR'}
        if node.leaf in ops: self.emit(ops[node.leaf])
        elif node.leaf == '<>': 
            self.emit("EQUAL")
            self.emit("NOT")

    def generate_UnaryOp(self, node):
        self.visit(node.children[0])
        if node.leaf == 'NOT': self.emit("NOT")
        elif node.leaf == 'MINUS': 
            self.emit("PUSHI -1")
            self.emit("MUL")

    # Literais
    def generate_IntegerConstant(self, node): self.emit(f"PUSHI {node.leaf}")
    def generate_NumericConst(self, node): self.emit(f"PUSHI {node.leaf}")
    def generate_BooleanConstant(self, node): 
        val = 1 if str(node.leaf).lower() == 'true' else 0
        self.emit(f"PUSHI {val}")
    def generate_StringConstant(self, node): self.emit(f'PUSHS "{node.leaf}"')