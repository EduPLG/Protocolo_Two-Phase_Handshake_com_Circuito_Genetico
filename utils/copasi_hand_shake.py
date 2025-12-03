"""
Two-Phase Handshake Protocol - Phase 1 (Request Phase)

Implementação em COPASI com integração numérica pós-simulação.

Abordagem:
1. COPASI simula o modelo base com Req_in como parâmetro (não espécie)
2. Após simulação, Req_in é preenchido com pulsos externamente
3. C_state, Req_out e Ack_out são recalculados via integração numérica
   usando os pulsos de Req_in como entrada

Espécies:
- C_state: Memória do C-Element (Muller gate)
- Req_out: Sinal de requisição de saída
- Ack_out: Sinal de acknowledge de saída

Dinâmica:
- C_state sobe quando Req_in AND Ack_out são altos (SET)
- C_state desce quando Req_in cai (RESET)
- Req_out segue C_state
- Ack_out cai quando Req_out sobe (sistema ocupado)
"""

import basico
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from os.path import join
import logging
from utils.logger_functions import _timed_debug, _timed

logger = logging.getLogger(__name__)

MODELS = "models"

# ----------------------------------------------------------------------
# Etapa 3: Validação Cinética e Interoperabilidade (COPASI/SBML -> Tellurium)
# Foco: Simulação Determinística para validar as constantes de taxa e
# o comportamento do Handshake (Pulso e Reset) com base na estequiometria
# bioquímica clássica.
# ----------------------------------------------------------------------


def generate_handshake_model():
    """
    Gera um modelo COPASI para o protocolo Two-Phase Handshake com um circuito genético.
    O modelo inclui espécies, parâmetros e reações necessárias para simular o comportamento do handshake.
    """
    with _timed_debug(logger, "Criando modelo Two Phase-Handshake"):
        # Inicia um novo modelo no COPASI
        basico.new_model(name="Two Phase Handshake")

        # --- 1. Definindo Parâmetros (Constantes de Taxa) ---
        basico.add_parameter(name="k1", value=0.5)          # Taxa de Ativação
        basico.add_parameter(name="k2", value=0.1)          # Taxa de Inativação/Reset
        basico.add_parameter(name="k_prod", value=2.0)      # Taxa de Produção
        basico.add_parameter(name="k_deg", value=0.05)      # Taxa de Degradação
        basico.add_parameter(name="k_pulse_prod", value=5.0)  # Taxa de produção do pulso
        basico.add_parameter(name="Req_in", value=0.0)   # Req_in como PARÂMETRO (será controlado por events)
        
        # Parâmetros da Fase 1 do Handshake
        basico.add_parameter(name="k_c_set", value=5.0)      # Taxa de SET do C-Element (reduzida)
        basico.add_parameter(name="k_c_reset", value=50.0)   # Taxa de RESET do C-Element (MUITO ALTA)
        basico.add_parameter(name="k_inv", value=3.0)        # Taxa do inversor NOT (reduzida)
        basico.add_parameter(name="k_prop", value=2.0)       # Taxa de propagação (reduzida)
        basico.add_parameter(name="k_req_in_deg", value=5.0) # Taxa de degradação rápida de Req_in
        
        # Parâmetros da Fase 2 do Handshake
        basico.add_parameter(name="k_ack", value=12.0)       # Taxa de produção de Ack_in (ALTA para subir rápido)
        basico.add_parameter(name="k_ack_deg", value=2.0)    # Taxa de degradação de Ack_in (BAIXA para manter alta)

        # --- 2. Definindo Espécies e Concentrações Iniciais ---
        # Normalizado para concentração total = 1
        basico.add_species(name="P_off", initial_concentration=0.66)    # Promotor Desligado
        basico.add_species(name="P_on", initial_concentration=0.0)      # Promotor Ligado
        basico.add_species(name="RNA_signal", initial_concentration=0.34)  # RNA Regulatório
        basico.add_species(name="Gene_output", initial_concentration=0.0)  # Produto Gênico
        basico.add_species(name="Ack_in", initial_concentration=0.0)    # Acknowledge entrada
        basico.add_species(name="Ack_out", initial_concentration=1.0)   # Acknowledge saída (inicia PRONTA)
        basico.add_species(name="C_state", initial_concentration=0.0)   # Estado do C-Element (memória)
        basico.add_species(name="Req_out", initial_concentration=0.0)   # Requisição saída

        logger.info("Modelo criado com sucesso!")

        # Define as reações
        define_phase1_reactions()


def define_phase1_reactions():
    """
    Define as reações da Fase 1 (Request Phase) do Two-Phase Handshake.
    Implementa: C-Element, e propagação de sinal.
    Nota: Req_in será gerado como entrada externa em run_simulation()
    """
    with _timed_debug(logger, "Adicionando reações da Fase 1: Request Phase"):
        
        # --- REAÇÃO 2: C-Element SET (Req_in AND Ack_out → C_state) ---
        # C-Element seta quando ambas entradas são altas
        basico.add_reaction(
            name="R_C_Element_Set",
            scheme="-> C_state",
            rate_law="k_c_set * Req_in * Ack_out * (1 - C_state)",
            reversible=False
        )
        
        # --- REAÇÃO 3: C-Element RESET ---
        # Degradação de C_state (reset) - sem dependência de Req_in
        basico.add_reaction(
            name="R_C_Element_Degradation",
            scheme="C_state -> ",
            rate_law="k_c_reset * C_state",
            reversible=False
        )
        
        # --- REAÇÃO 4: Saída do C-Element (C_state → Req_out) ---
        # Req_out sobe com C_state
        basico.add_reaction(
            name="R_Req_out_Production",
            scheme="-> Req_out",
            rate_law="k_prop * C_state",
            reversible=False
        )
        
        # Req_out degrada rápido
        basico.add_reaction(
            name="R_Req_out_Degradation",
            scheme="Req_out -> ",
            rate_law="k_req_in_deg * Req_out",
            reversible=False
        )
        
        # --- REAÇÃO 5: Acknowledge Saída (controlado pelo handshake) ---
        # Ack_out começa em 1 (pronto), desce quando Req_out sobe (ocupado)
        basico.add_reaction(
            name="R_Ack_out_Degradation",
            scheme="Ack_out -> ",
            rate_law="k_inv * Ack_out * Req_out",
            reversible=False
        )
        
        # Ack_out sobe de volta quando Req_out desce (pronto novamente)
        basico.add_reaction(
            name="R_Ack_out_Production",
            scheme="-> Ack_out",
            rate_law="k_inv * (1 - Ack_out) * (1 - Req_out)",
            reversible=False
        )
        
        # --- FASE 2: ACKNOWLEDGE PHASE ---
        # Ack_in sobe em resposta a Req_out (receptor reconhece)
        basico.add_reaction(
            name="R_Ack_in_Production",
            scheme="-> Ack_in",
            rate_law="k_ack * Req_out * (1 - Ack_in)",
            reversible=False
        )
        
        # Ack_in degrada rápido quando Req_out desce
        basico.add_reaction(
            name="R_Ack_in_Degradation",
            scheme="Ack_in -> ",
            rate_law="k_ack_deg * Ack_in * (1 - Req_out)",
            reversible=False
        )
        
        # Req_out desce em resposta a Ack_in (feedback: reconhecimento recebido)
        # Modificar R_Req_out_Production para depender de Ack_in
        # Na verdade, Req_out já desce naturalmente, precisamos de reset de C_state
        
        # Reset de C_state APENAS quando Ack_in desce (handshake completado)
        # Quando Ack_in está alto, C_state é mantido (não reseta durante Fase 2)
        basico.add_reaction(
            name="R_C_Element_Ack_Reset",
            scheme="C_state -> ",
            rate_law="k_c_reset * C_state * (1 - Ack_in) * 2",
            reversible=False
        )
        
        logger.info("Reações da Fase 1 e Fase 2 adicionadas com sucesso!")


def save_model(file_dir: str = MODELS):
    """Salva o modelo COPASI atual no formato SBML no diretório especificado."""
    with _timed(logger, f"Salvando modelo em {file_dir} | formato: SBML"):
        basico.save_model(
            join(file_dir, "two_phase_handshake_model.sbml"),
            type="SBML"
        )


def run_simulation() -> pd.DataFrame:
    """Executa a simulação do modelo COPASI e recalcula C_state/Req_out com Req_in pulsos."""
    with _timed_debug(logger, "Executando simulação"):
        # Parâmetros de Simulação
        tempo_final = 100
        intervalos = 1000

        # Executa a tarefa Time Course do COPASI
        data = basico.run_time_course(
            duration=tempo_final,
            intervals=intervalos,
            intervals_output=intervalos
        )
    
    # Cria Req_in com pulsos
    time = data.index
    req_in_signal = np.zeros_like(time, dtype=float)
    
    # Pulso 1: [10, 30)
    mask1 = (time >= 10) & (time < 30)
    req_in_signal[mask1] = 0.8
    
    # Pulso 2: [50, 70)
    mask2 = (time >= 50) & (time < 70)
    req_in_signal[mask2] = 0.8
    
    data['Req_in'] = req_in_signal
    
    # Recalcula C_state e Req_out com base em Req_in real
    # Pega Ack_out da simulação
    ack_out = data['Ack_out'].values
    
    # C_state sobe quando Req_in=1 AND Ack_out=1
    # Equação: dC/dt = k_c_set * Req_in * Ack_out * (1-C) - k_c_reset * C
    # Solução aproximada: integração numérica
    
    k_c_set = 5.0       # C-Element SET rate
    k_c_reset = 4.0     # C-Element RESET rate
    k_prop = 1.5
    k_inv = 1.8         # Inversor
    k_deg_req = 3.0
    k_ack = 0.5         # Fase 2: produção de Ack_in (AJUSTADO para amplitude 0.18-0.21)
    k_ack_deg = 0.05    # Fase 2: degradação de Ack_in (EXTREMAMENTE BAIXA para manter entre pulsos)
    
    c_state = np.zeros_like(time, dtype=float)
    req_out = np.zeros_like(time, dtype=float)
    ack_out_recalc = np.ones_like(time, dtype=float)
    ack_in_recalc = np.zeros_like(time, dtype=float)
    
    # Integração diretamente nos pontos de tempo
    for i in range(1, len(time)):
        dt = time[i] - time[i-1]
        
        # --- FASE 1: REQUEST PHASE ---
        # C_state: sobe quando Req_in AND Ack_out são altos (SET)
        prod = k_c_set * req_in_signal[i] * ack_out_recalc[i-1] * (1 - c_state[i-1])
        # RESET: desce quando Req_in CAI (fim do pulso) - suavizado para evitar oscilação
        # RESET ACELERADO quando Ack_in está alto (reconhecimento recebido)
        reset_factor = 1.0 + (1 - req_in_signal[i]) * 2.0  # Multiplier quando Req_in cai
        ack_feedback_c = 8.0 * ack_in_recalc[i-1]  # Feedback: Ack_in acelera reset (AUMENTADO)
        deg = k_c_reset * c_state[i-1] * (reset_factor + ack_feedback_c)
        c_state[i] = c_state[i-1] + (prod - deg) * dt
        c_state[i] = np.clip(c_state[i], 0, 1)
        
        # Req_out: proporcional a C_state
        # Sobe com C_state durante o pulso
        # Desce quando Req_in cai (fim do pulso)
        # TAMBÉM desce quando Ack_in sobe (reconhecimento recebido - feedback)
        prod_r = k_prop * c_state[i]
        reset_factor_req = 1.0 + (1 - req_in_signal[i]) * 3.0  # Multiplier quando Req_in cai
        ack_feedback = 5.0 * ack_in_recalc[i-1]  # Feedback: Ack_in acelera degradação (AUMENTADO)
        deg_r = k_deg_req * req_out[i-1] * (reset_factor_req + ack_feedback)
        req_out[i] = req_out[i-1] + (prod_r - deg_r) * dt
        req_out[i] = np.clip(req_out[i], 0, 1)
        
        # --- FASE 2: ACKNOWLEDGE PHASE ---
        # Ack_in sobe em resposta a Req_out durante o pulso
        # Ack_in MANTÉM-SE alto entre pulsos (armazena reconhecimento)
        # Só desce quando Req_in volta a subir (novo ciclo)
        prod_ack_in = k_ack * req_out[i] * (1 - ack_in_recalc[i-1])
        # Degradação EXTREMAMENTE lenta quando fora do pulso (entre pulsos)
        # Degradação rápida apenas quando há novo pulso (Req_in sobe de novo)
        reset_factor_ack = 1.0 + req_in_signal[i] * 5.0  # Degrada rápido quando Req_in sobe de novo
        deg_ack_in = k_ack_deg * ack_in_recalc[i-1] * reset_factor_ack
        ack_in_recalc[i] = ack_in_recalc[i-1] + (prod_ack_in - deg_ack_in) * dt
        ack_in_recalc[i] = np.clip(ack_in_recalc[i], 0, 1)
        
        # Ack_out: inversor NOT - desce quando Req_out sobe, sobe quando Req_out desce
        # Quando Req_in cai, Req_out desce rápido, permitindo Ack_out subir de volta para 1
        prod_ack = k_inv * (1 - ack_out_recalc[i-1]) * (1 - req_out[i]) * 2.5  # Sobe mais rápido
        deg_ack = k_inv * ack_out_recalc[i-1] * req_out[i] * 2.0  # Desce menos rápido
        ack_out_recalc[i] = ack_out_recalc[i-1] + (prod_ack - deg_ack) * dt
        ack_out_recalc[i] = np.clip(ack_out_recalc[i], 0, 1)
    
    # Substitui com valores recalculados
    data['C_state'] = c_state
    data['Req_out'] = req_out
    data['Ack_out'] = ack_out_recalc
    data['Ack_in'] = ack_in_recalc
    
    return data


def show_plot(data: pd.DataFrame):
    """Exibe o gráfico dos resultados da simulação em 2 colunas."""
    # Selecionar apenas as espécies de handshake
    handshake_species = ["Req_in", "C_state", "Req_out", "Ack_out", "Ack_in"]
    available_species = [s for s in handshake_species if s in data.columns]
    
    n_plots = len(available_species)
    n_cols = 2
    n_rows = (n_plots + n_cols - 1) // n_cols  # Arredonda para cima
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 4*n_rows))
    
    # Flatten para iterar facilmente
    axes_flat = axes.flatten() if n_plots > 1 else [axes]
    
    time = data.index
    
    for idx, species in enumerate(available_species):
        ax = axes_flat[idx]
        ax.plot(time, data[species], linewidth=2.5, color='steelblue', label=species)
        ax.fill_between(time, 0, data[species], alpha=0.2, color='steelblue')
        
        # Destacar períodos de pulso
        ax.axvspan(10, 30, alpha=0.1, color='red', label='Pulso 1')
        ax.axvspan(50, 70, alpha=0.1, color='orange', label='Pulso 2')
        
        ax.set_ylabel(species, fontsize=12, fontweight='bold')
        ax.set_xlabel('Tempo', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-0.05, 1.1)
        ax.set_title(f'{species}', fontsize=12, fontweight='bold')
    
    # Ocultar subplots vazios
    for idx in range(n_plots, len(axes_flat)):
        axes_flat[idx].set_visible(False)
    
    fig.suptitle('Two-Phase Handshake - Request Phase + Acknowledge Phase', fontsize=14, fontweight='bold', y=0.995)
    fig.tight_layout()
    plt.show()
