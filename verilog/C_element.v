// Módulo para o C-Element (com memória)
module C_Element (
 input A,
 input B,
 output reg Q  // 'reg' significa que este valor é armazenado
);


 // "sempre que A ou B mudarem..."
 always @(A or B)
 begin
   if (A == 1 && B == 1)
     Q <= 1; // Se ambos são 1, a saída vira 1
   else if (A == 0 && B == 0)
     Q <= 0; // Se ambos são 0, a saída vira 0
   // Se forem diferentes (ex: A=1, B=0), não faça nada.
   // Q mantém seu valor anterior (isso é a memória!)
 end
endmodule
