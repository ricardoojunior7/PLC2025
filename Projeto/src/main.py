#!/usr/bin/env python3
import sys
import os
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.theme import Theme
from rich import box

# Importações dos módulos do compilador
from lexer import lexer, test_lexer
from parser import parser, parse
from semantic import SemanticAnalyzer
from codegen import CodeGenerator
from optimizer import Optimizer

# Configuração do Tema Visual (Cores)
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "step": "bold blue",
})
console = Console(theme=custom_theme)

def print_banner():
    """Limpa o ecrã e mostra o logótipo do compilador."""
    os.system('cls' if os.name == 'nt' else 'clear')
    title = r"""[bold magenta]
   ____                      _ _           _            
  / ___|___  _ __ ___  _ __ (_) | __ _  __| | ___  _ __ 
 | |   / _ \| '_ ` _ \| '_ \| | |/ _` |/ _` |/ _ \| '__|
 | |__| (_) | | | | | | |_) | | | (_| | (_| | (_) | |   
  \____\___/|_| |_| |_| .__/|_|_|\__,_|\__,_|\___/|_|   
                      |_|                               
    
    [white]             Pascal Standard → EWVM [/]
    [/bold magenta]"""
    console.print(Panel(title, border_style="magenta", expand=False))

def show_source_preview(code, filename):
    """Mostra o código fonte Pascal com cores (syntax highlighting)."""
    display_name = os.path.basename(filename)
    syntax = Syntax(code, "pascal", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"📄 [bold]{display_name}[/]", border_style="blue", expand=False))

def run_lexical_check(code):
    """Executa o Lexer para encontrar caracteres inválidos."""
    lexer.errors = [] 
    lexer.input(code)
    for _ in lexer: 
        pass 
    
    if lexer.errors:
        error_lines = []
        for err in lexer.errors:
            msg = f"• Linha {err['lineno']}, Coluna {err['col']}: Caractere inválido '[bold yellow]{err['value']}[/]'"
            error_lines.append(msg)
            
        error_text = "\n".join(error_lines)
        console.print(Panel(error_text, title="❌ [error]Erros Léxicos[/]", border_style="red"))
        return True 
    return False 

def compile_file(file_path, options):
    """Função principal que coordena todas as fases da compilação."""
    try:
        with open(file_path, 'r') as f:
            source_code = f.read()

        print_banner()
        
        if options.verbose:
            show_source_preview(source_code, file_path)
        else:
            console.print(f"📂 [bold]Ficheiro:[/bold] [cyan]{file_path}[/cyan]\n")

        # Fase Léxica
        console.print("  [step]⚙️ Executando Lexer...[/]")
        if options.tokens_only:
            console.rule("[bold blue]Análise Léxica (Tokens)[/]")
            test_lexer(source_code)
            return

        if run_lexical_check(source_code):
            console.print("[error]❌ Compilação abortada devido a erros léxicos.[/]\n")
            return

        #  Iniciar o Processo de Compilação
        with console.status("[bold green]A compilar...[/]", spinner="dots"):
            
            # Fase de Parsing
            console.print("  [step]⚙️ Executando Parser...[/]")
            
            ast, syntax_errors, recovery_warnings = parse(source_code)

            # Mostrar Erros Fatais
            # É a informação mais importante para o utilizador corrigir
            if syntax_errors:
                error_lines = []
                for err in syntax_errors:
                    msg = f"• Linha {err['lineno']}, Coluna {err['col']}: {err['msg']}"
                    if err['dica']:
                        msg += f" [dim italic]({err['dica']})[/]"
                    error_lines.append(msg)
                
                error_text = "\n".join(error_lines)
                console.print(Panel(error_text, title="❌ [error]Erros Sintáticos[/]", border_style="red"))

            # Recuperação
            # Informação complementar sobre o que o compilador decidiu ignorar
            if recovery_warnings:
                rec_lines = []
                for warn in recovery_warnings:
                    msg = f"• Linha {warn['lineno']}: {warn['msg']}"
                    rec_lines.append(msg)
                
                warn_text = "\n".join(rec_lines)   
                console.print(Panel(
                    warn_text, 
                    title="⚠️ [warning]Recuperação dos Erros Sintáticos[/]", # Título ligeiramente mais descritivo
                    border_style="yellow",
                    box=box.ROUNDED
                ))
                
            if syntax_errors:
                if not ast:
                    console.print("[error]❌ Compilação abortada devido a erros sintáticos.[/]\n")
                    return
                else:
                    console.print("[warning]⚠️ O parser recuperou de erros, mas a compilação pode estar instável.[/]\n")

            if not ast and not syntax_errors:
                console.print("[error]❌ Erro Crítico: Falha desconhecida no Parser.[/]")
                return
            
            if options.ast_only:
                console.print(ast)
                return

            # Fase Semântica
            console.print("  [step]🧠 Verificando Semântica...[/]")
            analyzer = SemanticAnalyzer()
            is_valid, errors, warnings = analyzer.analyze(ast)

        # Mostrar Resultados Semânticos
        if warnings:
            console.print(Panel("\n".join(warnings), title="⚠️ Avisos", border_style="yellow"))
        
        if not is_valid:
            error_text = "\n".join([f"• {err}" for err in errors])
            console.print(Panel(error_text, title="❌ [error]Erros Semânticos[/]", border_style="red"))
            console.print("[error]❌ Compilação abortada devido a erros semânticos.[/]\n")
            return
        else:
            console.print("     ✅[success] Semântica Válida[/]")

        # Fase de Otimização
        if not options.no_opt:
            with console.status("[bold magenta]A otimizar código...[/]", spinner="bouncingBall"):
                opt = Optimizer()
                ast = opt.optimize(ast)
                if opt.optimizations_count > 0:
                    console.print(f"     ⚡[bold yellow] Otimização:[/][success] {opt.optimizations_count} Simplificações[/]")

        # Fase da Geração de Código
        output_file = ""
        if not options.no_code:
            with console.status("[bold cyan]A gerar Assembly EWVM...[/]", spinner="earth"):
                generator = CodeGenerator(analyzer.global_scope) 
                code = generator.generate(ast)
                
                output_file = options.output
                if not output_file:
                    output_dir = "../outputs"
                    
                    os.makedirs(output_dir, exist_ok=True)
                    
                    base_name = os.path.basename(file_path)
                    
                    name_only = os.path.splitext(base_name)[0]
                    # Simplificação da construção do caminho
                    output_file = os.path.join(output_dir, name_only + '.ewvm')
                
                with open(output_file, 'w') as f:
                    for instruction in code:
                        f.write(f"{instruction}\n")
            
            console.print(f"     ✅[success] Código Gerado com Sucesso![/]")
            console.print("\n")
            
            # Visualização do Código Gerado
            try:
                with open(output_file, 'r') as f:
                    ewvm_content = f.read()
                
                assembly_view = Syntax(ewvm_content, "nasm", theme="monokai", line_numbers=True, word_wrap=True)
                
                # Pegar apenas o nome do ficheiro para o título
                display_name = os.path.basename(output_file)

                code_panel = Panel(
                    assembly_view,
                    title=f"📄 [bold]{display_name}[/]", 
                    border_style="white",
                    box=box.ROUNDED,
                    padding=(1, 2),
                    expand=False
                )
                console.print(code_panel)
                print("\n")
            except Exception:
                console.print("[warning]⚠️  Não foi possível ler o ficheiro gerado para pré-visualização.[/]")

    except FileNotFoundError:
        console.print(f"[error]❌ Erro: O arquivo '{file_path}' não foi encontrado.[/]")
    except Exception as e:
        console.print(Panel(f"{e}", title="❌ Erro Inesperado", border_style="red"))
        if options.verbose:
            import traceback
            traceback.print_exc()

def main():
    parser_args = argparse.ArgumentParser(
        description='Compilador Pascal Standard',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser_args.add_argument('source', help='Caminho do arquivo fonte (.pas)')
    parser_args.add_argument('-o', '--output', help='Nome do arquivo de saída (.ewvm)')
    
    group_debug = parser_args.add_argument_group('Debug e Visualização')
    group_debug.add_argument('-t', '--tokens-only', action='store_true', help='Mostra apenas os tokens (Lexer)')
    group_debug.add_argument('-a', '--ast-only', action='store_true', help='Mostra apenas a AST (Parser)')
    group_debug.add_argument('-v', '--verbose', action='store_true', help='Modo verboso (mostra código fonte e stack traces)')
    
    group_config = parser_args.add_argument_group('Configurações')
    group_config.add_argument('--no-code', action='store_true', help='Não gerar código final')
    group_config.add_argument('--no-opt', action='store_true', help='Desativar otimizações')
    
    if len(sys.argv) == 1:
        parser_args.print_help()
        sys.exit(1)
        
    args = parser_args.parse_args()
    
    compile_file(args.source, args)

if __name__ == "__main__":
    main()