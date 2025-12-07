# 🛠️ GUIA DE USO E TROUBLESHOOTING - Etapa 4

## Instalação Rápida

### 1. Clonar repositório
```bash
git clone https://github.com/EduPLG/Protocolo_Two-Phase_Handshake_com_Circuito_Genetico.git
cd Protocolo_Two-Phase_Handshake_com_Circuito_Genetico
```

### 2. Criar e ativar ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

**Pacotes principais**:
- `copasi-basico>=0.85` - API Python para COPASI
- `tellurium>=2.2.11.1` - Simulador de sistemas biológicos
- `pysb>=1.15.2` - Modelagem de síntese proteica
- `pandas>=2.2.2` - Manipulação de dados
- `numpy>=1.26.4` - Computação numérica
- `scipy>=1.13.1` - Otimização e algoritmos
- `matplotlib>=3.9.0` - Visualização

---

## Executar Projeto

### Opção 1: Executar Tudo (Etapas 1-4)
```bash
python main.py
```

Saída esperada:
```
19:07:13 INFO     utils.copasi_hand_shake: Modelo criado com sucesso!
19:07:13 INFO     utils.copasi_hand_shake: ✓ R1 (Req_out produção): k=2.0
...
19:07:13 INFO     utils.copasi_hand_shake: ✅ Simulação 5 fases: 800 pontos
================================================================================
Iniciando Etapa 4: Simulação com Tellurium
================================================================================
19:07:14 INFO     utils.PySB_hand_shake: Criando modelo Tellurium com Antimony
19:07:14 INFO     utils.PySB_hand_shake: ✓ Modelo Tellurium criado com sucesso!
19:07:14 INFO     utils.PySB_hand_shake: ✓ Fase 1 (t=0-10, Req_in=0): Req_out=0.0000, Ack_out=1.0000
...
✅ Etapa 4 concluída com sucesso!
```

### Opção 2: Executar Apenas Etapa 4
```bash
python -c "from utils.PySB_hand_shake import run_stage_4_tellurium; run_stage_4_tellurium()"
```

### Opção 3: Usar em Script Customizado
```python
from utils.PySB_hand_shake import generate_tellurium_model, run_tellurium_simulation, show_tellurium_plot

# Gera modelo
rr = generate_tellurium_model()

# Executa simulação
data = run_tellurium_simulation(rr)

# Exibe gráficos
show_tellurium_plot(data)

# Acessa dados brutos
print(data.head())
print(f"Tempo final: {data.index.max():.1f}s")
```

---

## Análises Avançadas

### Análise 1: Sensibilidade Paramétrica
```python
from utils.stage4_extensions import sensitivity_analysis
from utils.PySB_hand_shake import generate_tellurium_model
import numpy as np

rr = generate_tellurium_model()

# Varia k_mrna_req_prod de 1 a 5
k_range = np.linspace(1.0, 5.0, 20)
results = sensitivity_analysis(rr, "k_mrna_req_prod", k_range, "Req_out")

print(results)
results.to_csv("sensitivity_k_mrna_req.csv", index=False)
```

### Análise 2: Otimização de Parâmetros
```python
from utils.stage4_extensions import optimize_handshake_kinetics

rr = generate_tellurium_model()
optimal = optimize_handshake_kinetics(rr)

print(f"Parâmetros ótimos:")
print(f"  k_mrna_req_prod: {optimal['k_mrna_req_prod']:.3f}")
print(f"  k_req_out_transl: {optimal['k_req_out_transl']:.3f}")
print(f"  k_mrna_req_deg: {optimal['k_mrna_req_deg']:.3f}")
print(f"  k_req_out_deg: {optimal['k_req_out_deg']:.3f}")
print(f"Tempo de resposta ótimo: {optimal['response_time']:.2f}s")
```

### Análise 3: Simulação Estocástica
```python
from utils.stage4_extensions import stochastic_simulation

rr = generate_tellurium_model()
results = stochastic_simulation(rr, n_runs=100)

print(f"Tempo de resposta médio: {results['mean_response_time']:.2f} ± {results['std_response_time']:.2f}s")
print(f"Range: [{results['min_response_time']:.2f}, {results['max_response_time']:.2f}]s")
```

### Análise 4: Análise de Robustez
```python
from utils.stage4_extensions import robustness_analysis

rr = generate_tellurium_model()
robust = robustness_analysis(rr, perturbation_pct=20)

print(robust[['parameter', 'nominal_response_time', 'sensitivity']])
robust.to_csv("robustness_analysis.csv", index=False)
```

### Análise 5: Diagrama de Bifurcação
```python
from utils.stage4_extensions import bifurcation_diagram
import numpy as np

rr = generate_tellurium_model()
k_range = np.linspace(1.0, 10.0, 50)
bifurca = bifurcation_diagram(rr, "k_mrna_req_prod", k_range)

print(f"Parâmetro: {bifurca['parameter']}")
print(f"Pontos de transição: {bifurca['transitions']}")
print(bifurca['data'])
```

### Análise 6: Comparação COPASI vs Tellurium
```python
from utils.copasi_hand_shake import run_simulation as copasi_sim
from utils.PySB_hand_shake import run_stage_4_tellurium as tellurium_sim
from utils.stage4_extensions import compare_simulators

copasi_data = copasi_sim()
tellurium_data = tellurium_sim()

comparison = compare_simulators(copasi_data, tellurium_data)

print("Comparação COPASI vs Tellurium:")
for species, metrics in comparison.items():
    print(f"\n{species}:")
    print(f"  RMS Error: {metrics['rms_error']:.6f}")
    print(f"  Correlação: {metrics['correlation']:.4f}")
    print(f"  Max Diferença: {metrics['max_difference']:.6f}")
```

---

## Troubleshooting

### ❌ Erro: "ModuleNotFoundError: No module named 'tellurium'"
**Solução**:
```bash
pip install tellurium --upgrade
```

### ❌ Erro: "ModuleNotFoundError: No module named 'basico'"
**Solução**:
```bash
pip install copasi-basico --upgrade
```

### ❌ Erro: "AttributeError: module 'basico' has no attribute 'set_parameter'"
**Solução**: Use a forma correta:
```python
rr['parameter_name'] = value  # Para Tellurium
basico.set_parameter("name", value)  # Para COPASI se disponível
```

### ❌ Gráficos não aparecem (Jupyter/IDE)
**Solução**: Adicione antes de chamar `show_tellurium_plot()`:
```python
import matplotlib
matplotlib.use('TkAgg')  # ou 'Qt5Agg'
import matplotlib.pyplot as plt
plt.ion()  # Modo interativo
```

### ❌ Simulação muito lenta
**Solução**: Reduza número de pontos:
```python
# Em run_tellurium_simulation, mude:
result1 = rr.simulate(0, 10, 50)  # De 100 para 50 pontos
```

### ❌ "Cannot access attribute" ao otimizar
**Solução**: Certifique-se de que parâmetro existe:
```python
print(rr.getGlobalParameterIds())  # Lista parâmetros disponíveis
```

### ❌ Dados incompletos ou NaN
**Solução**: Verifique condições iniciais:
```python
print(f"Req_out inicial: {rr['Req_out']}")
print(f"Ack_out inicial: {rr['Ack_out']}")
rr.resetToOrigin()  # Reseta para valor inicial
```

---

## Estrutura de Dados Retornados

### DataFrame da Simulação
```python
data = run_tellurium_simulation(rr)

# data.head():
       Req_in  mRNA_Req  Req_out  mRNA_Ack  Ack_out
0.000    0.0      0.0      0.0       0.0      1.0
0.125    0.0      0.1      0.0       0.0      0.99
0.250    0.0      0.2      0.0       0.0      0.98
...

# Acesso:
data['Req_out']          # Coluna como Series
data.loc[5.0]            # Linha em t=5.0
data.iloc[0]             # Primeira linha
data[10:30]              # Slice temporal
```

### Saída de Otimização
```python
optimal = optimize_handshake_kinetics(rr)

optimal = {
    'k_mrna_req_prod': 2.45,      # k1
    'k_req_out_transl': 1.87,     # k2
    'k_mrna_req_deg': 1.23,       # k3
    'k_req_out_deg': 0.54,        # k4
    'response_time': 3.21          # Tempo até 50% em segundos
}
```

### Saída de Sensibilidade
```python
sensitivity_results = sensitivity_analysis(rr, "k_mrna_req_prod", [1,2,3,4,5])

#   parameter  Req_out_max  Req_out_steady_state
#   1.0        0.2          0.15
#   2.0        0.4          0.30
#   3.0        0.6          0.45
#   4.0        0.8          0.60
#   5.0        1.0          0.75
```

---

## Personalização de Modelos

### Modificar Reações
Edite `utils/PySB_hand_shake.py`, função `generate_tellurium_model()`:

```python
# Adicionar reação nova:
J9: Req_out + Ack_out -> ; k_cross_react * Req_out * Ack_out;

# Modificar Hill function:
# De: k * X^2 / (K^2 + X^2)
# Para: k * X^3 / (K^3 + X^3)  // Maior cooperatividade
```

### Modificar Parâmetros Iniciais
```python
rr['Req_out'] = 0.5  # Começar com concentração maior
rr['Ack_out'] = 0.7
rr['k_mrna_req_prod'] = 4.0  # Aumentar taxa de produção
```

### Adicionar Novos Parâmetros Globais
```python
antimony_code = """
...
k_new_param = 1.5;  # Adiciona novo parâmetro
...
J_new: -> Species_X; k_new_param * trigger;
...
"""
```

---

## Salvando Resultados

### Exportar para CSV
```python
data.to_csv("handshake_simulation.csv")
sensitivity_results.to_csv("sensitivity_analysis.csv")
robust.to_csv("robustness_analysis.csv")
```

### Exportar para Excel (requer openpyxl)
```bash
pip install openpyxl
```

```python
data.to_excel("handshake_simulation.xlsx")
```

### Salvar Gráficos como PNG
```python
fig, axes = plt.subplots(5, 1, figsize=(14, 12))
# ... plotting code ...
plt.savefig("handshake_simulation.png", dpi=300, bbox_inches='tight')
```

---

## Próximos Passos

1. **Executar**: `python main.py` e verificar saídas
2. **Explorar**: Usar análises da Etapa 4 em seus modelos
3. **Customizar**: Modificar parâmetros e reações
4. **Validar**: Comparar COPASI vs Tellurium (deve estar próximo)
5. **Estender**: Adicionar novas espécies/reações e re-otimizar

---

## Referências Rápidas

| Tarefa | Comando |
|--------|---------|
| Ver parâmetros disponíveis | `rr.getGlobalParameterIds()` |
| Ver espécies | `rr.getFloatingSpeciesIds()` |
| Resetar modelo | `rr.resetToOrigin()` |
| Simular | `result = rr.simulate(t_start, t_end, n_points)` |
| Modificar parâmetro | `rr['param_name'] = value` |
| Modificar espécie | `rr['species_name'] = value` |
| Ver help | `help(rr.simulate)` |
| Exportar SBML | `rr.exportToSBML('model.xml')` |

---

## Contato e Feedback

Se encontrar problemas ou tiver sugestões:
1. Abra uma **Issue** no GitHub
2. Faça um **Pull Request** com suas contribuições
3. Envie feedback por email

**Última atualização**: 7 de dezembro de 2025  
**Versão**: 1.0 (Etapas 1-4 completadas)
