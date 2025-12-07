# 📂 ESTRUTURA DO PROJETO - Two-Phase Handshake

```
Protocolo_Two-Phase_Handshake_com_Circuito_Genetico/
│
├── 📄 README.md                          [Original - visão geral do projeto]
├── 📄 main.py                            [Script principal: orquestra Etapas 1-4]
├── 📄 requirements.txt                   [Dependências Python (copasi-basico, tellurium, etc)]
│
├── 📁 models/
│   └── two_phase_handshake_model.sbml   [Modelo COPASI em SBML (gerado Etapa 3)]
│
├── 📁 verilog/
│   ├── C_element.v                      [Implementação Verilog do C-Element]
│   └── handshake_controler.v            [Controlador Verilog do handshake]
│
├── 📁 utils/
│   ├── copasi_hand_shake.py            [Etapas 2-3: COPASI model + 5-phase simulation]
│   ├── PySB_hand_shake.py               [Etapa 4: Tellurium/Antimony model + simulation]
│   ├── stage4_extensions.py             [Etapa 4+: 6 análises avançadas]
│   ├── logger_functions.py              [Utilitários de logging e timing]
│   └── __pycache__/                     [Cache Python]
│
├── 📚 DOCUMENTAÇÃO:
│   ├── IMPLEMENTACAO_COMPLETA.md        [Visão geral das 4 etapas + roadmap]
│   ├── ETAPA_4_README.md                [Detalhes técnicos da Etapa 4]
│   ├── ETAPA_4_SUMARIO.md               [Resumo do que foi implementado]
│   └── GUIA_USO_ETAPA_4.md              [Instruções práticas + troubleshooting]
│
└── 🛠️ AMBIENTE:
    └── venv/                            [Ambiente virtual Python (criado via venv)]
```

---

## 📋 Descrição de Cada Arquivo

### 1. **main.py** (30 linhas)
**Função**: Orquestra a execução de todas as 4 etapas
**Conteúdo**:
- Importa módulos de COPASI e Tellurium
- Executa `generate_handshake_model()` (Etapa 2)
- Executa `save_model()` (Etapa 2)
- Executa `run_simulation()` (Etapa 3)
- Exibe gráficos COPASI
- Executa `run_stage_4_tellurium()` (Etapa 4)

**Como executar**: `python main.py`

---

### 2. **requirements.txt** (19 linhas)
**Função**: Lista todas as dependências Python
**Pacotes**:
```
copasi-basico>=0.85      # API Python para COPASI
tellurium>=2.2.11.1      # Simulador de Tellurium
pysb>=1.15.2             # Modelagem de proteínas
pandas>=2.2.2            # Manipulação de dados
numpy>=1.26.4            # Computação numérica
scipy>=1.13.1            # Otimização
matplotlib>=3.9.0        # Visualização
```

**Como instalar**: `pip install -r requirements.txt`

---

### 3. **utils/copasi_hand_shake.py** (333 linhas)
**Função**: Implementa Etapas 2-3 (COPASI)

**Funções principais**:

#### `generate_handshake_model()`
- Cria novo modelo COPASI
- Define 3 espécies: `Req_out`, `Ack_in`, `Ack_out`
- Define 5 reações com Mass Action Law
- Chama `define_phase_reactions()`

#### `define_phase_reactions()`
- Adiciona 5 reações à cascata
- Usa `basico.get_reactions()` para acessar e modificar parâmetros
- Padrão: `rxns.loc['R_name', 'k1'] = value`

#### `save_model(file_dir)`
- Salva modelo em `models/two_phase_handshake_model.sbml`
- Formato: SBML (padrão Systems Biology)

#### `run_simulation()`
- **Etapa 3 Principal**: Simula 5 fases com continuidade de estado
- Fase 1 (0-10s, Req_in=0): repouso
- Fase 2 (10-30s, Req_in=1): requisição + estado preservado
- Fase 3 (30-50s, Req_in=0): reset + estado preservado
- Fase 4 (50-70s, Req_in=1): segunda requisição
- Fase 5 (70-100s, Req_in=0): retorno ao repouso
- Usa `set_species_initial_concentration()` entre fases
- Retorna DataFrame consolidado (800+ pontos)

#### `show_plot(data)`
- Exibe 4 subplots (Req_in, Req_out, Ack_in, Ack_out)
- Marca transições de fase com linhas verticais
- Escalas 0-1 para representar sinais digitais

**Status**: ✅ Etapas 2-3 completas

---

### 4. **utils/PySB_hand_shake.py** (365 linhas)
**Função**: Implementa Etapa 4 (Tellurium)

**Funções principais**:

#### `generate_tellurium_model()`
- Cria modelo em Antimony DSL
- 5 espécies: `Req_in`, `mRNA_Req`, `Req_out`, `mRNA_Ack`, `Ack_out`
- 8 reações com cinética explícita
- Hill functions (n=2) para ativação cooperativa
- Retorna objeto RoadRunner

#### `run_tellurium_simulation(rr)`
- Simula 5 fases (0-100s)
- Preserva estado entre fases
- Usa `rr[species] = value` para copiar estado
- Retorna DataFrame com 800+ pontos

#### `show_tellurium_plot(data)`
- Exibe 5 subplots (Req_in, mRNA_Req, Req_out, mRNA_Ack, Ack_out)
- Dinâmica realista com rise/fall times
- Marca transições de fase

#### `run_stage_4_tellurium()`
- Orquestra todo fluxo Etapa 4
- Gera modelo → simula → plota
- Pode ser chamada standalone

**Status**: ✅ Etapa 4 completa

---

### 5. **utils/stage4_extensions.py** (400+ linhas)
**Função**: Análises avançadas da Etapa 4

**6 Funções de Análise**:

1. **`sensitivity_analysis(rr, param, range, output_species)`**
   - Varia parâmetro, mede efeito em espécie-alvo
   - Retorna DataFrame com máximos e steady-states

2. **`optimize_handshake_kinetics(rr)`**
   - Otimização L-BFGS-B para minimizar tempo de resposta
   - Varia 4 parâmetros simultaneamente
   - Retorna dict com k's ótimos

3. **`stochastic_simulation(rr, n_runs)`**
   - Simula 100+ rodadas com ruído Gaussiano
   - Mede variabilidade em tempos de resposta
   - Retorna estatísticas: média±σ, min, max

4. **`robustness_analysis(rr, perturbation_pct)`**
   - Perturba cada parâmetro ±20%
   - Calcula sensibilidade de cada parâmetro
   - Retorna DataFrame com sensibilidades

5. **`bifurcation_diagram(rr, param, range)`**
   - Constrói diagrama de bifurcação
   - Detecta transições steady-state ↔ oscilações
   - Retorna dados e número de transições

6. **`compare_simulators(copasi_data, tellurium_data)`**
   - Compara resultados COPASI vs Tellurium
   - Calcula: RMS error, correlação, max diferença
   - Valida consistência entre simuladores

**Status**: ✅ 6 extensões implementadas

---

### 6. **utils/logger_functions.py**
**Função**: Utilitários de logging e timing

**Decoradores**:
- `@_timed()`: Mede tempo de execução (bloco with)
- `@_timed_debug()`: Versão com debug logging
- `setup_logger()`: Configura logging global

**Uso**:
```python
with _timed(logger, "Executando operação X"):
    # código...
    # Saída: "Executando operação X... concluído em 0.234s"
```

---

## 📚 Arquivos de Documentação

### **IMPLEMENTACAO_COMPLETA.md** (280 linhas)
Documento integrador com:
- Visão geral das 4 etapas
- Estrutura do projeto
- Mapeamento lógico → bioquímico
- Comparação COPASI vs Tellurium
- Instruções instalação/execução
- Saídas esperadas
- Roadmap Etapa 5

### **ETAPA_4_README.md** (180 linhas)
Documentação técnica da Etapa 4:
- Objetivo e comparação com COPASI
- Arquitetura molecular diagramada
- Explicação de cada reação
- Dinâmica em 5 fases
- Vantagens de Tellurium
- Referências técnicas

### **ETAPA_4_SUMARIO.md** (200 linhas)
Sumário executivo da Etapa 4:
- O que foi criado (4 funções principais)
- Características principais (5 espécies, 8 reações)
- Problemas resolvidos
- Dados gerados
- Como usar (básico e avançado)
- Performance esperada
- Roadmap Etapa 5

### **GUIA_USO_ETAPA_4.md** (300 linhas)
Guia prático de uso:
- Instalação passo-a-passo
- Como executar (3 opções)
- Análises avançadas (6 exemplos com código)
- Troubleshooting (8 problemas comuns)
- Estrutura de dados retornados
- Personalização de modelos
- Salvando resultados (CSV, Excel, PNG)

---

## 🔧 Modelos Gerados

### **models/two_phase_handshake_model.sbml** (XML)
- Formato SBML (Systems Biology Markup Language)
- Gerado automaticamente por COPASI na Etapa 2
- Contém: 3 espécies, 5 reações, 6 parâmetros
- Pode ser aberto em COPASI, Tellurium, ou qualquer ferramenta SBML

---

## 🖥️ Arquivos Verilog (Referência)

### **verilog/C_element.v**
- Implementação Verilog do C-Element (Muller gate)
- Prototipagem de hardware do protocolo
- Não executável em Python (apenas referência)

### **verilog/handshake_controler.v**
- Controlador Verilog para two-phase handshake
- Coordena sinais Req_in/Ack_out
- Referência para tradução → bioquímica

---

## 📊 Resumo de Linhas de Código

| Arquivo | Linhas | Status |
|---------|--------|--------|
| main.py | 30 | ✅ |
| copasi_hand_shake.py | 333 | ✅ |
| PySB_hand_shake.py | 365 | ✅ |
| stage4_extensions.py | 420+ | ✅ |
| logger_functions.py | 80+ | ✅ (existente) |
| requirements.txt | 19 | ✅ |
| **Total Código** | **~1250** | **✅** |
| **Total Documentação** | **~1000** | **✅** |
| **Total Projeto** | **~2250** | **✅** |

---

## 🎯 O que Cada Etapa Gera

### Etapa 1 (Conceitual)
- Especificação bioquímica da cascata
- Mapeamento Verilog ↔ Química

### Etapa 2 (COPASI Setup)
- Modelo estruturado em COPASI
- Arquivo `two_phase_handshake_model.sbml`
- 3 espécies, 5 reações

### Etapa 3 (COPASI Simulação)
- DataFrame com 800 pontos de tempo
- Gráficos 4-subplot de dinâmica
- Validação de protocolo (5 fases funcionando)

### Etapa 4 (Tellurium)
- Modelo expandido com RNAs
- DataFrame com 800 pontos de tempo
- Gráficos 5-subplot (mais detalhado)
- 6 análises avançadas disponíveis

### Etapa 5 (Futuro)
- Otimização automática de parâmetros
- Validação experimental
- Síntese de genética sintética

---

## 🚀 Fluxo de Execução

```
main.py
  │
  ├─→ COPASI (Etapas 2-3)
  │    ├─ generate_handshake_model()
  │    │   └─ define_phase_reactions()
  │    ├─ save_model()
  │    ├─ run_simulation()
  │    │   └─ retorna DataFrame (800 pts)
  │    └─ show_plot()
  │        └─ exibe 4 gráficos
  │
  └─→ Tellurium (Etapa 4)
       ├─ generate_tellurium_model()
       │   └─ carrega Antimony DSL
       ├─ run_tellurium_simulation()
       │   └─ retorna DataFrame (800 pts)
       └─ show_tellurium_plot()
           └─ exibe 5 gráficos
```

---

## 📝 Como Adicionar Novo Arquivo

Se quiser estender o projeto:

1. **Novo utilitário**: Coloque em `utils/novo_arquivo.py`
2. **Documentação**: Crie `NOVA_ETAPA_README.md`
3. **Testes**: Crie `tests/test_novo.py`
4. **Atualize main.py**: Importe nova função

**Exemplo**:
```python
# Em main.py
from utils.novo_arquivo import nova_funcao

# Depois do código Tellurium:
resultado = nova_funcao()
```

---

## ✅ Checklist de Implementação

- [x] Etapa 1: Tradução Verilog → Bioquímica
- [x] Etapa 2: Modelo COPASI (3 espécies, 5 reações)
- [x] Etapa 3: Simulação 5 fases com continuidade
- [x] Etapa 4: Modelo Tellurium (5 espécies, 8 reações)
- [x] Etapa 4: Análises avançadas (6 funções)
- [x] Documentação completa (4 guias)
- [ ] Etapa 5: Otimização e validação experimental

---

**Última atualização**: 7 de dezembro de 2025  
**Versão**: 1.0  
**Status**: Etapas 1-4 ✅ Completas | Etapa 5 🔄 Planejamento
