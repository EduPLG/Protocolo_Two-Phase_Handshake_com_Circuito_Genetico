// Módulo principal do controlador de handshake
module handshake_controller (
 input Req_in,
 input Ack_in,
 output Req_out,
 output Ack_out
);
  // Declara um "fio" interno para conectar o C-Element à saída
 wire c_element_output;


 // 1. Cria uma instância do nosso C-Element
 //    Conecta 'Req_in' na porta 'A' do C-Element
 //    Conecta 'Ack_out' na porta 'B' do C-Element
 //    Recebe a saída do C-Element no nosso fio 'c_element_output'
 C_Element my_c_gate (
   .A(Req_in),
   .B(Ack_out),
   .Q(c_element_output)
 );
  // 2. A saída do C-Element é a nossa Requisição de saída
 assign Req_out = c_element_output;
  // 3. O Acknowledge de saída é o Acknowledge de entrada invertido (porta NOT)
 assign Ack_out = ~Ack_in;


endmodule
