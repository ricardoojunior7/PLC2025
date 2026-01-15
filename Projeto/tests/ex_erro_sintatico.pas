program TesteSintatico;
var
    x, y: integer { ERRO 1: Falta o ponto e vírgula aqui }
    z: integer;
begin
    x := 10;

    { ERRO 2: Atribuição malformada (falta o lado direito) }
    y := ;

    { ERRO 3: IF sem THEN }
    if x > 5
        y := 20;

    { ERRO 4: Parênteses não balanceados }
    x := (10 + 5 * 2;

    { ERRO 5: Palavra reservada no sítio errado (VAR dentro do BEGIN) }
          var k: integer;

    { ERRO 6: FOR com sintaxe errada (falta o DO) }
          for x := 1 to 10
          writeln(x);

          writeln('Fim');
    { ERRO 7: Falta o 'end.' final (o ficheiro acaba abruptamente) }
