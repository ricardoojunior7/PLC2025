program TesteSemantico;
var
    x, resultado: integer;
    x: boolean;        { ERRO 1: Variável 'x' redeclarada no mesmo escopo }
    texto: string;
    flag: boolean;
    lista: array[1..5] of integer;

function Soma(a, b: integer): integer;
begin
    Soma := a + b;
end;

begin
    { ERRO 2: Variável não declarada }
    naoExiste := 10;

    { ERRO 3: Incompatibilidade de tipos (String := Integer) }
    texto := 123;

    { ERRO 4: Operação matemática com String }
    resultado := 10 + 'texto';

    { ERRO 5: Condição do IF não é booleana }
    if 100 then
        writeln('Isto não devia passar');

    { ERRO 6: Chamada de função com número errado de argumentos }
    resultado := Soma(10);

    { ERRO 7: Chamada de função com tipos errados (esperava int, recebeu bool) }
    resultado := Soma(10, true);

    { ERRO 8: Indexar variável que não é array }
    resultado[1] := 5;

    { ERRO 9: Índice de array inválido (tipo incorreto) }
    flag := true;
    lista[flag] := 50;

    { ERRO 10: Tentar chamar uma variável como se fosse procedimento }
    x(10);
end.
