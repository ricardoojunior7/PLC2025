program TesteOtimizacao;
var
    x, y, z: integer;
    flag: boolean;
begin
    writeln('--- Inicio do Teste de Otimizacao ---');

    { 1. CONSTANT FOLDING (Aritmética) }
    { O compilador deve calcular isto tudo e gerar apenas: x := 20; }
    x := 10 + 5 * 2;
    writeln('x (esperado 20): ', x);

    { 2. ARITMÉTICA COMPLEXA & NEGATIVOS }
    { (100 / 2) + (-5) -> 50 - 5 -> 45 }
    y := (100 div 2) + (-5);
    writeln('y (esperado 45): ', y);

    { 3. COMPARAÇÕES ESTÁTICAS }
    { 10 = 10 gera 'true'. O optimizer deve substituir logo por 'true' }
    flag := 10 = 10;

    { 4. DEAD CODE ELIMINATION (IF TRUE) }
    { Como 1=1 é true, o compilador deve remover o IF e deixar apenas o writeln }
    if 1 = 1 then
        writeln('Otimizacao: Este IF desapareceu, ficou so o writeln.');

    { 5. DEAD CODE ELIMINATION (IF FALSE) }
    { Como 10=0 é false, o compilador deve APAGAR este bloco inteiro do codigo final }
    if 10 = 0 then
    begin
        writeln('ERRO: Isto nao deve aparecer no codigo assembly!');
        x := 99999;
    end;

    { 6. OTIMIZAÇÃO EM CADEIA }
    { (2*5) + (20 mod 2) -> 10 + 0 -> 10 }
    z := (2 * 5) + (20 mod 2);
    writeln('z (esperado 10): ', z);

    writeln('--- Fim ---');
end.
