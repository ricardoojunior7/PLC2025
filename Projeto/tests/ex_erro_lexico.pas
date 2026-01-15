program TesteLexico;
var
    preco: integer;
    email: string;
begin
    { ERRO 1: Identificador a começar por número (o lexer vai ler '1' como int e 'var' como ID) }
    1variavel := 10;

    { ERRO 2: Caracteres especiais inválidos no Pascal Standard }
    preco := 50$;   { O '$' não é válido }
    preco := 100?;  { O '?' não é válido }

    { ERRO 3: Utilização de arroba fora de contextos permitidos }
    email := usuario@dominio;

    { ERRO 4: Caracteres de controle ou desconhecidos }
    writeln('Teste #');  { Isto passa porque está numa string }
#tag := 1;           { O '#' fora de string deve dar erro }

    writeln('Fim dos erros léxicos');
end.
