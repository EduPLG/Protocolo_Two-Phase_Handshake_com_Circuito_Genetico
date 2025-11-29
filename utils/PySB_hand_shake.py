import pysb
from pysb.simulator import ScipyOdeSimulator
import numpy as np
from os.path import join
import os
import sys
import matplotlib.pyplot as plt
import logging
import platform

logger = logging.getLogger(__name__)
tipo = platform.system().lower()

if tipo == "windows":
    tipo = "win"
elif tipo == "darwin":
    tipo = "mac"


CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
BNG_PATH_LOCATION = join(PROJECT_ROOT, "venv", "Lib", "site-packages", "bionetgen", f"bng-{tipo}")
# DEFINIR A VARIÁVEL DE AMBIENTE (APENAS PARA ESTE PROCESSO)
try:
    if not os.path.exists(BNG_PATH_LOCATION):
        print(f"ERRO: O caminho do BNG não existe: {BNG_PATH_LOCATION}")
        sys.exit(1)

    os.environ['BNGPATH'] = BNG_PATH_LOCATION
    print(f"BNGPATH configurado com sucesso para: {os.environ['BNGPATH']}")

except Exception as e:
    print(f"Ocorreu um erro ao configurar o BNGPATH: {e}")
    sys.exit(1)

# ----------------------------------------------------------------------
# Etapa 4: Modelagem Baseada em Regras (PySB)
# O foco é representar o Promotor como uma molécula com estados ('off', 'on'),
# e o RNA Regulatório como o sinal que muda esse estado.
# ----------------------------------------------------------------------

# 0. Declarações de Variáveis para satisfazer o Corretor/Linter (IDE)
# Embora essas variáveis sejam geradas dinamicamente pelo PySB,
# declará-las como None no topo evita avisos de "variável não definida".
model = None
Promoter = None
RNA_Regul = None
Product = None
k_act = None
k_reset = None
k_prod = None
k_deg_R = None
k_deg_G = None
P_total = None
R_initial = None
G_initial = None

# 1. Criação do Modelo
pysb.Model()

# 2. Definição das Moléculas e seus Estados (Sítios)
# Promoter: Tem um estado 'state' que alterna entre 'off' e 'on' (o Handshake).
pysb.Monomer('Promoter', ['state'], {'state': ['off', 'on']})

# RNA_Regul (R): O sinal de entrada.
pysb.Monomer('RNA_Regul')

# Product (G): A saída do sistema.
pysb.Monomer('Product')

# 3. Parâmetros (Constantes de Taxa)
# Usando as constantes validadas na etapa COPASI
pysb.Parameter('k_act', 0.5)      # k1: Ativação (Regra 1)
pysb.Parameter('k_reset', 0.1)    # k2: Reset (Regra 2)
pysb.Parameter('k_prod', 2.0)     # Taxa de produção (Regra 3)
pysb.Parameter('k_deg_R', 0.05)   # Degradação do RNA de Sinal
pysb.Parameter('k_deg_G', 0.01)   # Degradação do Produto

# 4. Concentrações Iniciais
pysb.Parameter('P_total', 10.0)    # Concentração total do promotor
pysb.Parameter('R_initial', 15.0)  # Concentração inicial do RNA de sinal
pysb.Parameter('G_initial', 0.0)   # Concentração inicial do Produto

# O promotor começa no estado desligado ('off')
pysb.Initial(Promoter(state='off'), P_total)
# O RNA de sinal começa presente
pysb.Initial(RNA_Regul(), R_initial)
# O produto começa em zero
pysb.Initial(Product(), G_initial)

# 5. Regras Lógicas do Two-Phase Handshake
# --- Fase 1: Ativação (O Sinal LIGA) ---
# O RNA Regulatório atua como um 'catalisador lógico', transformando o estado do Promotor de 'off' para 'on'.
# O RNA_Regul é consumido lentamente (Regra R4), garantindo a transitoriedade.
pysb.Rule('R1_Activation',
          RNA_Regul() + Promoter(state='off') >> RNA_Regul() + Promoter(state='on'),
          k_act)

# --- Fase 2: Reset (O Sinal DESLIGA) ---
# O promotor ativado retorna espontaneamente ao estado 'off'.
pysb.Rule('R2_Reset',
          Promoter(state='on') >> Promoter(state='off'),
          k_reset)

# --- Produção e Degradação ---
# Produção: Apenas o promotor no estado 'on' produz o Produto.
pysb.Rule('R3_Production',
          Promoter(state='on') >> Promoter(state='on') + Product(),
          k_prod)

# Degradação do RNA de Sinal (Consumo do Sinal)
pysb.Rule('R4_Degradation_R',
          RNA_Regul() >> None,
          k_deg_R)

# Degradação do Produto
pysb.Rule('R5_Degradation_G',
          Product() >> None,
          k_deg_G)


# 6. Observáveis (Para Rastreamento e Plotagem)
pysb.Observable('P_off_obs', Promoter(state='off'))
pysb.Observable('P_on_obs', Promoter(state='on'))
pysb.Observable('R_obs', RNA_Regul())
pysb.Observable('G_obs', Product())

# 7. Simulação
tspan = np.linspace(0, 100, 500)
sim = ScipyOdeSimulator(model, tspan=tspan)
simulation_results = sim.run()

# 8. Plotagem
plt.figure(figsize=(10, 6))
plt.plot(simulation_results.tout, simulation_results.observables['P_off_obs'], label='Promotor Off (P_off)')
plt.plot(simulation_results.tout, simulation_results.observables['P_on_obs'], label='Promotor On (P_on)')
plt.plot(simulation_results.tout, simulation_results.observables['R_obs'], label='RNA Sinal (R)')
plt.plot(simulation_results.tout, simulation_results.observables['G_obs'], label='Produto (G)')

plt.title('Simulação do Two-Phase Handshake em PySB (Lógica de Estados)')
plt.xlabel('Tempo (unidades arbitrárias)')
plt.ylabel('Concentração')
plt.legend()
plt.grid(True)
plt.show()

logger.info("Simulação PySB concluída.")
logger.info("O PySB gerou automaticamente as ODEs a partir das regras para esta simulação.")
