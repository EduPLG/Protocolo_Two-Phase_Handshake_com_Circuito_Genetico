# Etapa 4: Simulação de Redes Metabólicas e Regulatórias

## Objetivo
Implementar o protocolo Two-Phase Handshake usando **Tellurium + Antimony** para representar RNAs como portadores de sinais lógicos em redes metabólicas.

## Diferenças da Etapa 3 (COPASI)

| Aspecto | COPASI (Etapa 3) | Tellurium (Etapa 4) |
|---------|------------------|-------------------|
| **Linguagem** | GUI + Python API | Antimony (DSL) |
| **Definição de Reações** | Estequiometria implícita | Lei da Ação de Massa explícita |
| **Espécies** | Proteínas apenas | mRNAs + Proteínas |
| **Sinais Lógicos** | Concentrações (0-1) | Hill functions para gates lógicos |
| **Flexibilidade** | Limitada por SBML | Código texto puro (fácil modificação) |

## Arquitetura Molecular

```
┌─────────────────────────────────────────┐
│     Entrada: Req_in (sinal externo)     │
│     (0 = inativo, 1 = ativo)            │
└────────────────┬────────────────────────┘
                 │
                 ▼
         ┌───────────────────┐
         │  Transcrição DNA  │ ─────► mRNA_Req
         │  (ativada por     │
         │   Req_in)         │
         └───────────────────┘
                 │
         ┌───────┴──────────┐
         │  Tradução        │
         ▼                  ▼
      Degradação     Req_out (Proteína)
    mRNA_Req          │
                      │
                      ▼
              ┌─────────────────┐
              │  Transcrição    │
              │  mRNA_Ack       │
              │  (ativada por   │
              │   Req_out)      │
              └─────────────────┘
                      │
              ┌───────┴──────────┐
              │  Tradução        │
              ▼                  ▼
           Degradação     Ack_out (Proteína)
         mRNA_Ack              │
                               │
                      Feedback Negativo
                         (inibição)
```

## Implementação em Antimony

### Parâmetros
```
Req_in = 0.0                # Sinal externo (variável, muda entre fases)
k_mrna_req_prod = 3.0       # Taxa de transcrição de mRNA_Req
k_req_out_transl = 2.0      # Taxa de tradução de Req_out
k_ack_in_prod = 2.5         # Taxa de produção de mRNA_Ack
```

### Reações Principais

**R1: Produção de mRNA_Req** (ativada por Req_in via Hill function)
```
-> mRNA_Req; k_mrna_req_prod * Req_in^2 / (0.25 + Req_in^2)
```
- Usa função de Hill com cooperatividade (n=2)
- Maior sensibilidade ao sinal Req_in

**R3: Tradução mRNA_Req → Req_out** (padrão catalítico)
```
mRNA_Req -> mRNA_Req + Req_out; k_req_out_transl * mRNA_Req
```
- mRNA é regenerado (catalisador)
- Req_out é produzido proporcionalmente

**R5: Produção de mRNA_Ack** (ativada por Req_out)
```
-> mRNA_Ack; k_mrna_ack_prod * Req_out^2 / (K_req^2 + Req_out^2)
```
- Segunda cascata lógica
- Amplifica sinal de Req_out

## Dinâmica em 5 Fases

### Fase 1 (t=0-10s): Req_in = 0
- Sistema em repouso
- mRNA_Req ≈ 0, Req_out ≈ 0
- mRNA_Ack ≈ 0, Ack_out ≈ 1.0

### Fase 2 (t=10-30s): Req_in = 1 (REQUISIÇÃO)
- Req_in sobe para 1.0
- mRNA_Req sobe rapidamente (produção Hill)
- Req_out sobe (tradução)
- mRNA_Ack ativado por Req_out
- Ack_out começa a cair

### Fase 3 (t=30-50s): Req_in = 0 (RESET)
- Req_in volta para 0
- mRNA_Req degrada rapidamente
- Req_out degrada
- mRNA_Ack cai
- Ack_out recupera valor alto

### Fase 4 (t=50-70s): Req_in = 1 (SEGUNDA REQUISIÇÃO)
- Ciclo se repete
- Confirmação de protocolo

### Fase 5 (t=70-100s): Req_in = 0 (RETORNO REPOUSO)
- Sistema retorna ao estado basal
- Pronto para próxima transação

## Vantagens do Tellurium

1. **Antimony é pseudocódigo**: Simples de entender e modificar
2. **Reações explícitas**: Cada termo tem significado biológico claro
3. **Hill functions**: Suportam comportamento cooperativo e lógico
4. **Interoperabilidade**: Pode exportar para SBML, BioNetGen, PySB
5. **Compatibilidade com COPASI**: Pode importar/exportar modelos

## Comparação COPASI vs Tellurium

### COPASI (Etapa 3)
✅ Interface GUI intuitiva
✅ Análise de bifurcação avançada
❌ Rate laws não foram aplicadas via parâmetro
❌ Eventos tiveram dificuldade com parâmetros

### Tellurium (Etapa 4)
✅ Hill functions nativas
✅ Sintaxe clara e flexível
✅ Fácil adicionar complexidade
❌ Sem GUI (código puro)
❌ Curva de aprendizado maior

## Próximas Extensões (Etapa 5)

1. **Análise de Sensibilidade**: Variar k's e K's para encontrar ganhos ótimos
2. **Dinâmica Estocástica**: Simular flutuações de moléculas
3. **Redes Booleanas**: Formalizar como circuitos lógicos digitais
4. **Comparação Experimental**: Validar contra dados de laboratório
5. **Síntese de Circuitos**: Encontrar combinações de parâmetros ótimas

## Referências
- Tellurium: https://tellurium.readthedocs.io/
- Antimony: http://www.sbml.org/
- COPASI Integration: https://basico.readthedocs.io/
