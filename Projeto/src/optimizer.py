from parser import Node

class Optimizer:
    """
    Realiza otimizações na AST antes da geração de código.
    Estratégia: Constant Folding e Dead Code Elimination.
    """
    def __init__(self):
        self.optimizations_count = 0

    def optimize(self, node):
        if not node or not isinstance(node, Node):
            return node

        # Otimizar filhos primeiro (Bottom-Up / Pós-Ordem)
        # Isto é crucial: garante que (2+3)+4 vira 5+4 e depois 9 numa só passagem recursiva.
        for i, child in enumerate(node.children):
            node.children[i] = self.optimize(child)

        # Tentar simplificar o nó atual com base nos filhos já otimizados
        if node.type == 'BinaryOp':
            return self.fold_binary_op(node)
        elif node.type == 'UnaryOp':
            return self.fold_unary_op(node)
        elif node.type == 'IfStatement':
            return self.fold_if_statement(node)

        return node

    def fold_binary_op(self, node):
        """Tenta resolver operações binárias estáticas (ex: 3 + 4 -> 7)"""
        left = node.children[0]
        right = node.children[1]
        op = node.leaf

        # Só otimiza se ambos os operandos forem constantes inteiras
        if left.type == 'IntegerConstant' and right.type == 'IntegerConstant':
            v1 = left.leaf
            v2 = right.leaf
            res = None

            try:
                if op == '+': res = v1 + v2
                elif op == '-': res = v1 - v2
                elif op == '*': res = v1 * v2
                elif op == 'DIV': res = v1 // v2 # Divisão inteira
                elif op == 'MOD': res = v1 % v2
                # Otimização extra: Resolve comparação estática (ex: if 1=1)
                elif op == '=': 
                    self.optimizations_count += 1
                    # Transforma a operação num nó booleano fixo
                    return Node('BooleanConstant', [], 'true' if v1 == v2 else 'false', lineno=node.lineno)
            except ZeroDivisionError:
                return node # Se houver divisão por zero, deixa para o runtime ou ignora

            if res is not None:
                self.optimizations_count += 1
                # Substitui a operação inteira pelo resultado
                return Node('IntegerConstant', [], res, lineno=node.lineno)

        return node

    def fold_unary_op(self, node):
        """Simplifica unários (ex: -5 estático)"""
        child = node.children[0]
        op = node.leaf

        if child.type == 'IntegerConstant' and op == 'MINUS':
            self.optimizations_count += 1
            return Node('IntegerConstant', [], -child.leaf, lineno=node.lineno)
        
        return node

    def fold_if_statement(self, node):
        """Eliminação de Código Morto em IFs"""
        cond = node.children[0]
        
        # Só otimiza se a condição for uma constante booleana conhecida
        if cond.type == 'BooleanConstant':
            val = str(cond.leaf).lower()
            
            if val == 'true':
                self.optimizations_count += 1
                # Se é sempre True, substitui o IF inteiro pelo conteúdo do THEN
                return node.children[1] 
            elif val == 'false':
                self.optimizations_count += 1
                # Se é sempre False, substitui pelo ELSE (se existir) ou remove tudo
                if len(node.children) > 2:
                    return node.children[2] 
                else:
                    return Node('Empty', [], lineno=node.lineno)
                    
        return node