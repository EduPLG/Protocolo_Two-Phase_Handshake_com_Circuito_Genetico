# Implementação Completa: Two-Phase Handshake Protocol
## Resumo das Etapas 1-4

---

## 📋 Visão Geral

Este projeto implementa o **Protocolo Two-Phase Handshake** (protocolo de comunicação assíncrona confiável) em sistemas bioquímicos, progredindo de conceitos básicos a simulações realistas de redes metabólicas.

### Estrutura do Projeto

```
Protocolo_Two-Phase_Handshake/
├── main.py                          # Script principal (orquestra todas etapas)
├── requirements.txt                 # Dependências Python
├── README.md                        # Este arquivo
│
├── models/
│   └── two_phase_handshake_model.sbml    # Modelo COPASI em SBML
│
├── verilog/
│   ├── C_element.v                  # Implementação Verilog do C-Element
│   └── handshake_controler.v        # Controlador Verilog
│
└── utils/
    ├── copasi_hand_shake.py         # Etapas 1-3: COPASI simulation
    ├── PySB_hand_shake.py           # Etapa 4: Tellurium/Antimony
    ├── stage4_extensions.py         # Análises avançadas (Etapa 4+)
    ├── logger_functions.py          # Utilitários de logging
    └── __pycache__/                 # Cache Python
```

---

## 🔬 As 4 Etapas de Implementação

### **Etapa 1: Tradução Verilog → Conceitos Bioquímicos**
- **Entrada**: Descrição em Verilog do C-Element e handshake
- **Saída**: Especificação bioquímica
- **Arquivo**: `verilog/` (C_element.v, handshake_controler.v)

**Mapeamento Lógico → Bioquímico**:
```
Sinal digital (0/1)     ← →    Concentração molecular (baixa/alta)
Gate lógico AND         ← →    Reação bimolecular cooperativa
Gate lógico OR          ← →    Reação unimolecular + feedback
Mudança de estado       ← →    Transição entre steady-states
```

---

### **Etapa 2: Construção de Cascata Simples (Solo)**
- **Framework**: COPASI Basico (Python API)
- **Modelo**: Cascata linear 4-espécies
  ```
  Req_in → Req_out → Ack_in ⊣ Ack_out
  ```
- **Dinâmica**: Mass Action Law com estequiometria implícita
- **Arquivo**: `utils/copasi_hand_shake.py`

**Espécies**:
| Espécie | Função | Inicial |
|---------|--------|---------|
| Req_in | Parâmetro (sinal externo) | 0.0 |
| Req_out | Proteína requisição | 0.0 |
| Ack_in | Proteína acknowledge | 0.0 |
| Ack_out | Proteína inibidor | 1.0 |

**5 Reações**:
1. `→ Req_out` (k=2.0) - produção
2. `Req_out →` (k=5.0) - degradação
3. `Req_out → Req_out + Ack_in` (k=2.0) - cascata
4. `Ack_in →` (k=5.0) - degradação
5. `Ack_in + Ack_out → Ack_in` (k=8.0) - inibição bimolecular

---

### **Etapa 3: Simulação em 5 Fases com Continuidade de Estado**
- **Problema Resolvido**: Estados eram resetados entre fases
- **Solução**: `set_species_initial_concentration()` entre simulações
- **Resultado**: Simulação contínua de 100 segundos com 4 transições de Req_in

**Fases**:
```
Fase 1: [0-10s]   Req_in = 0   (repouso)
Fase 2: [10-30s]  Req_in = 1   (requisição)
Fase 3: [30-50s]  Req_in = 0   (reset)
Fase 4: [50-70s]  Req_in = 1   (segunda requisição)
Fase 5: [70-100s] Req_in = 0   (retorno repouso)
```

**Problemas Encontrados & Soluções**:
| Problema | Causa | Solução |
|----------|-------|---------|
| rate_law parameter ignored | basico ignora `rate_law=` | Usar estequiometria implícita |
| States reset each phase | `run_time_course()` reseta | `set_species_initial_concentration()` |
| Event assignment errors | Sintaxe de eventos incorreta | Trocar para fases manuais |

---

### **Etapa 4: Rede Metabólica com RNAs (Tellurium)**
- **Framework**: Tellurium + Antimony DSL
- **Modelo**: Rede com mRNAs + Proteínas (8 reações)
- **Cinética**: Hill functions para gates lógicos
- **Arquivo**: `utils/PySB_hand_shake.py`

**Espécies Expandidas**:
```
mRNA_Req   ──Tradução──→  Req_out   (produtor de sinal)
mRNA_Ack   ──Tradução──→  Ack_out   (inibidor)
```

**Reações Principais**:
```
R1:  → mRNA_Req;              [Hill: ativada por Req_in]
R2:  mRNA_Req → ;             [degradação exponencial]
R3:  mRNA_Req → mRNA_Req + Req_out;  [tradução catalítica]
R4:  Req_out → ;              [degradação]
R5:  → mRNA_Ack;              [Hill: ativada por Req_out]
R6:  mRNA_Ack → ;             [degradação]
R7:  mRNA_Ack → mRNA_Ack + Ack_out;  [tradução]
R8:  Ack_out → ;              [degradação]
```

**Hill Function (Função de Ativação Cooperativa)**:
$$\text{Taxa} = k \cdot \frac{[A]^n}{K^n + [A]^n}$$
- Onde $n=2$ (cooperatividade)
- Implementa comportamento "tudo ou nada" (digital)

---

## 📊 Comparação das Abordagens

| Aspecto | Etapa 3 (COPASI) | Etapa 4 (Tellurium) |
|---------|------------------|-------------------|
| **Linguagem** | Python API | Antimony DSL |
| **GUI** | Sim | Não |
| **Flexibilidade** | Média | Alta |
| **Reações** | 5 simples | 8 com biologia real |
| **Sinais Lógicos** | Concentrações | Hill functions |
| **Performance** | Rápida | Rápida |
| **Extensibilidade** | SBML | SBML/BioNetGen/PySB |

---

## 🎯 Dinâmica Esperada

### Fase 2 (Requisição):
```
Req_in = 1
    ↓ ↑↑↑ (Hill activation)
mRNA_Req sobe rapidamente
    ↓ ↓ (tradução)
Req_out sobe (sinal de saída)
    ↓ ↓↓ (ativa próstrata)
mRNA_Ack sobe
    ↓ ↓ (tradução)
Ack_out cai (inibe o inibidor anterior)
```

**Características de Protocolo Handshake**:
- ✅ Transições claras entre estados
- ✅ Continuidade de informação (estado → próxima fase)
- ✅ Replicabilidade (ciclos idênticos)
- ✅ Robustez a perturbações

---

## 🚀 Como Executar

### Instalação
```bash
# Clone o repositório
git clone https://github.com/EduPLG/Protocolo_Two-Phase_Handshake_com_Circuito_Genetico.git
cd Protocolo_Two-Phase_Handshake_com_Circuito_Genetico

# Crie ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt
```

### Executar Todas as Etapas
```bash
python main.py
```

### Executar Apenas Etapa 4
```bash
python -c "from utils.PySB_hand_shake import run_stage_4_tellurium; run_stage_4_tellurium()"
```

### Usar Análises Avançadas
```python
from utils.PySB_hand_shake import generate_tellurium_model
from utils.stage4_extensions import sensitivity_analysis, optimize_handshake_kinetics

rr = generate_tellurium_model()

# Análise de sensibilidade
results = sensitivity_analysis(rr, "k_mrna_req_prod", [1, 2, 3, 4, 5])
print(results)

# Otimizar parâmetros
optimal = optimize_handshake_kinetics(rr)
print(f"Tempo ótimo de resposta: {optimal['response_time']:.2f}s")
```

---

## 📈 Saídas Esperadas

### Gráficos COPASI (Etapa 3)
- 4 subplots: Req_in, Req_out, Ack_in, Ack_out
- Linhas vertical em t=10, 30, 50, 70 (transições)
- Concentrações em escala 0-1 (digital)

### Gráficos Tellurium (Etapa 4)
- 5 subplots: Req_in, mRNA_Req, Req_out, mRNA_Ack, Ack_out
- Dinâmica mais realista (rise/fall times)
- RNAs mostram oscilações e transientes

---

## 🧪 Validação Cruzada

**Como comparar COPASI vs Tellurium**:
```python
from utils.stage4_extensions import compare_simulators

copasi_data = run_simulation()  # Etapa 3
tellurium_data = run_stage_4_tellurium()  # Etapa 4

comparison = compare_simulators(copasi_data, tellurium_data)
print(f"RMS Error Req_out: {comparison['Req_out']['rms_error']:.4f}")
print(f"Correlação: {comparison['Req_out']['correlation']:.4f}")
```

---

## 🔧 Extensões Futuras (Etapa 5+)

1. **Stochastic Simulation**: Adicionar ruído de expressão gênica
2. **Parameter Optimization**: Usar algoritmos genéticos para encontrar kinética ótima
3. **Bifurcation Analysis**: Identificar transições de fase no espaço de parâmetros
4. **Network Robustness**: Testar resiliência a perturbações
5. **Experimental Validation**: Comparar com dados de laboratório real
6. **Hardware Implementation**: Síntese de genética sintética

---

## 📚 Referências

### Soft Ware
- **COPASI**: http://copasi.org/
- **Tellurium**: https://tellurium.readthedocs.io/
- **Antimony**: http://www.sbml.org/

### Literatura
- Laplante & Sokol, "Molecular Programming and Molecular Computation" (2005)
- Thoms et al., "Theory of Asynchronous Handshake Circuits" (2004)
- Nielsen & Chuang, "Quantum Computation and Quantum Information" - Ch. 13 (state machines)

### SBML & Standards
- Systems Biology Markup Language: http://sbml.org/
- BioNetGen: http://www.bngl.org/

---

## 📝 Autores & Licença

**Autor**: EduPLG  
**Licença**: MIT  
**Status**: Em desenvolvimento (Etapas 1-4 completas, Etapa 5 em planejamento)

---

## 🤝 Contribuindo

Sugestões e extensões são bem-vindas! Abra uma issue ou pull request no GitHub.

---

**Última atualização**: Dezembro 7, 2025  
**Status das Etapas**:
- ✅ Etapa 1: Tradução Verilog → Bioquímica
- ✅ Etapa 2: Cascata Simples (COPASI)
- ✅ Etapa 3: Simulação 5 Fases (COPASI com estado contínuo)
- ✅ Etapa 4: Rede Metabólica (Tellurium + análises)
- 🔄 Etapa 5: Otimização e Validação (em planejamento)
