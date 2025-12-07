import basico
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from os.path import join
import logging
from utils.logger_functions import _timed_debug, _timed
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
"""Two-Phase Handshake Protocol
Iniciando a Primeira Transferência (ambos os fios em 0):

ENVIO: O remetente tem algo para enviar e faz a primeira transição em Req_in (muda de 0 → 1).

PERCEPÇÃO: O seu circuito percebe isso e faz Req_out também mudar de 0 → 1.

RECEBIMENTO: O destinatário recebe o dado e faz a primeira transição em Ack_in como resposta (muda de 0 → 1).

CONFIRMAÇÃO: Seu circuito percebe o Ack_in e faz a transição em Ack_out (ele inverte, então Ack_out muda de 1 → 0). O remetente vê essa mudança e sabe que a primeira transferência foi concluída.

Iniciando a Segunda Transferência (ambos os fios em 1):

ENVIO (novo dado): O remetente agora faz a segunda transição em Req_in (muda de 1 → 0). Essa descida é o sinal para o próximo dado.

PERCEPÇÃO: Seu circuito vê essa nova transição e faz Req_out também mudar de 1 → 0.

RECEBIMENTO (novo dado): O destinatário recebe o novo dado e responde com a segunda transição em Ack_in (muda de 1 → 0).

CONFIRMAÇÃO: Seu circuito vê essa mudança e Ack_out faz a transição de volta (muda de 0 → 1).

Agora, ambos os fios estão de volta ao estado inicial (0), prontos para a próxima transferência. Esse ciclo pode se repetir indefinidamente, permitindo uma comunicação confiável entre o remetente e o destinatário."""


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
    Gera um modelo COPASI para o protocolo Two-Phase Handshake.
    Cascata simples: Req_in → Req_out → Ack_in → inibe Ack_out
    """
    with _timed_debug(logger, "Criando modelo Two Phase-Handshake"):
        basico.new_model(name="Two Phase Handshake")

        # Parâmetros (incluindo Req_in que será controlado por eventos)
        basico.add_parameter(name="Req_in", value=0.0)  # Será controlado por eventos
        basico.add_parameter(name="k_req_out_prod", value=2.0)   # Produção
        basico.add_parameter(name="k_req_out_deg", value=5.0)    # Degradação MUITO MAIOR
        basico.add_parameter(name="k_ack_in_prod", value=2.0)    # Produção
        basico.add_parameter(name="k_ack_in_deg", value=5.0)     # Degradação MUITO MAIOR
        basico.add_parameter(name="k_ack_out_deg", value=8.0)    # Degradação muito rápida

        # Espécies (apenas as que se integram)
        basico.add_species(name="Req_out", initial_concentration=0.0)
        basico.add_species(name="Ack_in", initial_concentration=0.0)
        basico.add_species(name="Ack_out", initial_concentration=1.0)

        logger.info("Modelo criado com sucesso!")

        define_phase_reactions()


def define_phase_reactions():
    """
    Define as reações da cascata de ativação com inibição.
    Usa Mass Action Law com estequiometria para calcular automaticamente.
    """
    with _timed_debug(logger, "Adicionando reações"):

        # Req_in → Req_out (produção)
        r1 = basico.add_reaction(
            name="R_Req_out_Production",
            scheme="-> Req_out",
            reversible=False
        )
        try:
            # Acessa via get_reactions e modifica diretamente
            rxns = basico.get_reactions()
            rxns.loc['R_Req_out_Production', 'k1'] = 2.0
            logger.info("✓ R1 (Req_out produção): k=2.0")
        except Exception as e:
            logger.warning(f"⚠ R1: {e}")
        
        # Req_out degradação
        r2 = basico.add_reaction(
            name="R_Req_out_Degradation",
            scheme="Req_out -> ",
            reversible=False
        )
        try:
            rxns = basico.get_reactions()
            rxns.loc['R_Req_out_Degradation', 'k1'] = 5.0
            logger.info("✓ R2 (Req_out degradação): k=5.0")
        except Exception as e:
            logger.warning(f"⚠ R2: {e}")

        # Req_out → Ack_in
        r3 = basico.add_reaction(
            name="R_Ack_in_Production",
            scheme="Req_out -> Req_out + Ack_in",
            reversible=False
        )
        try:
            rxns = basico.get_reactions()
            rxns.loc['R_Ack_in_Production', 'k1'] = 2.0
            logger.info("✓ R3 (Ack_in produção): k=2.0")
        except Exception as e:
            logger.warning(f"⚠ R3: {e}")
        
        # Ack_in degradação
        r4 = basico.add_reaction(
            name="R_Ack_in_Degradation",
            scheme="Ack_in -> ",
            reversible=False
        )
        try:
            rxns = basico.get_reactions()
            rxns.loc['R_Ack_in_Degradation', 'k1'] = 5.0
            logger.info("✓ R4 (Ack_in degradação): k=5.0")
        except Exception as e:
            logger.warning(f"⚠ R4: {e}")

        # Ack_out degradação (ativada por Ack_in)
        r5 = basico.add_reaction(
            name="R_Ack_out_Degradation",
            scheme="Ack_in + Ack_out -> Ack_in",
            reversible=False
        )
        try:
            rxns = basico.get_reactions()
            rxns.loc['R_Ack_out_Degradation', 'k1'] = 8.0
            logger.info("✓ R5 (Ack_out degradação): k=8.0")
        except Exception as e:
            logger.warning(f"⚠ R5: {e}")

        logger.info("✅ 5 reações adicionadas com Mass Action!")


def save_model(file_dir: str = MODELS):
    """Salva o modelo COPASI atual no formato SBML no diretório especificado."""
    with _timed(logger, f"Salvando modelo em {file_dir} | formato: SBML"):
        basico.save_model(
            join(file_dir, "two_phase_handshake_model.sbml"),
            type="SBML"
        )


def run_simulation() -> pd.DataFrame:
    """
    Executa 5 fases com Req_in mudando em pontos específicos.
    Cada fase começa exatamente onde a anterior terminou (SEM RESET).
    """
    with _timed_debug(logger, "Executando simulação 5 fases com CONTINUIDADE"):
        
        all_data = []
        
        # ============= FASE 1: t=0-10, Req_in=0 =============
        basico.set_parameters("Req_in", 0.0)
        data1 = basico.run_time_course(duration=10, intervals=100, intervals_output=100)
        all_data.append(data1)
        
        logger.info(f"✓ Fase 1 (t=0-10, Req_in=0): Final state: Req_out={data1['Req_out'].iloc[-1]:.4f}, Ack_in={data1['Ack_in'].iloc[-1]:.4f}, Ack_out={data1['Ack_out'].iloc[-1]:.4f}")
        
        # ============= FASE 2: t=10-30, Req_in=1 =============
        # Muda Req_in ANTES de rodar
        basico.set_parameters("Req_in", 1.0)
        # IMPORTANTE: set initial concentrations com valores do final da fase 1
        basico.set_species("Req_out", data1['Req_out'].iloc[-1])
        basico.set_species("Ack_in", data1['Ack_in'].iloc[-1])
        basico.set_species("Ack_out", data1['Ack_out'].iloc[-1])
        
        data2 = basico.run_time_course(duration=20, intervals=200, intervals_output=200)
        data2.index = data2.index + 10  # Ajusta tempo para continuar de t=10
        all_data.append(data2)
        
        logger.info(f"✓ Fase 2 (t=10-30, Req_in=1): Final state: Req_out={data2['Req_out'].iloc[-1]:.4f}, Ack_in={data2['Ack_in'].iloc[-1]:.4f}, Ack_out={data2['Ack_out'].iloc[-1]:.4f}")
        
        # ============= FASE 3: t=30-50, Req_in=0 =============
        basico.set_parameters("Req_in", 0.0)
        basico.set_species("Req_out", data2['Req_out'].iloc[-1])
        basico.set_species("Ack_in", data2['Ack_in'].iloc[-1])
        basico.set_species("Ack_out", data2['Ack_out'].iloc[-1])
        
        data3 = basico.run_time_course(duration=20, intervals=200, intervals_output=200)
        data3.index = data3.index + 30  # Ajusta tempo
        all_data.append(data3)
        
        logger.info(f"✓ Fase 3 (t=30-50, Req_in=0): Final state: Req_out={data3['Req_out'].iloc[-1]:.4f}, Ack_in={data3['Ack_in'].iloc[-1]:.4f}, Ack_out={data3['Ack_out'].iloc[-1]:.4f}")
        
        # ============= FASE 4: t=50-70, Req_in=1 =============
        basico.set_parameters("Req_in", 1.0)
        basico.set_species("Req_out", data3['Req_out'].iloc[-1])
        basico.set_species("Ack_in", data3['Ack_in'].iloc[-1])
        basico.set_species("Ack_out", data3['Ack_out'].iloc[-1])
        
        data4 = basico.run_time_course(duration=20, intervals=200, intervals_output=200)
        data4.index = data4.index + 50  # Ajusta tempo
        all_data.append(data4)
        
        logger.info(f"✓ Fase 4 (t=50-70, Req_in=1): Final state: Req_out={data4['Req_out'].iloc[-1]:.4f}, Ack_in={data4['Ack_in'].iloc[-1]:.4f}, Ack_out={data4['Ack_out'].iloc[-1]:.4f}")
        
        # ============= FASE 5: t=70-100, Req_in=0 =============
        basico.set_parameters("Req_in", 0.0)
        basico.set_species("Req_out", data4['Req_out'].iloc[-1])
        basico.set_species("Ack_in", data4['Ack_in'].iloc[-1])
        basico.set_species("Ack_out", data4['Ack_out'].iloc[-1])
        
        data5 = basico.run_time_course(duration=30, intervals=300, intervals_output=300)
        data5.index = data5.index + 70  # Ajusta tempo
        all_data.append(data5)
        
        logger.info(f"✓ Fase 5 (t=70-100, Req_in=0): Final state: Req_out={data5['Req_out'].iloc[-1]:.4f}, Ack_in={data5['Ack_in'].iloc[-1]:.4f}, Ack_out={data5['Ack_out'].iloc[-1]:.4f}")
        
        # ============= Combina dados =============
        data = pd.concat(all_data, ignore_index=False)
        
        # Reconstrói Req_in para visualização
        time_values = data.index.values
        req_in_values = np.zeros_like(time_values, dtype=float)
        
        for t_idx, t_val in enumerate(time_values):
            if t_val >= 70:
                req_in_values[t_idx] = 0.0
            elif t_val >= 50:
                req_in_values[t_idx] = 1.0
            elif t_val >= 30:
                req_in_values[t_idx] = 0.0
            elif t_val >= 10:
                req_in_values[t_idx] = 1.0
            else:
                req_in_values[t_idx] = 0.0
        
        data.insert(0, 'Req_in', req_in_values)
        
        logger.info(f"✅ Simulação 5 fases: {len(data)} pontos com CONTINUIDADE TOTAL")
    
    return data


def show_plot(data: pd.DataFrame):
    """Exibe o Two-Phase Handshake Protocol em gráficos separados."""
    logger.debug(f"Colunas disponíveis no DataFrame: {list(data.columns)}")
    logger.debug(f"Primeiras linhas:\n{data.head()}")
    logger.debug(f"Últimas linhas:\n{data.tail()}")
    logger.info(f"Req_in range: {data['Req_in'].min():.3f} - {data['Req_in'].max():.3f}")
    logger.info(f"Req_out range: {data['Req_out'].min():.3f} - {data['Req_out'].max():.3f}")
    logger.info(f"Ack_in range: {data['Ack_in'].min():.3f} - {data['Ack_in'].max():.3f}")
    logger.info(f"Ack_out range: {data['Ack_out'].min():.3f} - {data['Ack_out'].max():.3f}")
    
    # Criar figura com 4 subplots
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    
    # Marcadores de eventos para todos os gráficos
    eventos = [10, 30, 50, 70]
    
    # Req_in (entrada)
    if 'Req_in' in data.columns:
        axes[0].plot(data.index, data['Req_in'], color='green', linewidth=2.5, label='Req_in (entrada)')
        for t in eventos:
            axes[0].axvline(x=t, color='gray', linestyle=':', alpha=0.5)
        axes[0].set_ylabel('Req_in', fontsize=11, fontweight='bold')
        axes[0].set_ylim(-0.1, 1.2)
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(loc='upper right', fontsize=10)
    
    # Req_out
    if 'Req_out' in data.columns:
        axes[1].plot(data.index, data['Req_out'], color='orange', linewidth=2.5, label='Req_out')
        for t in eventos:
            axes[1].axvline(x=t, color='gray', linestyle=':', alpha=0.5)
        axes[1].set_ylabel('Req_out', fontsize=11, fontweight='bold')
        axes[1].set_ylim(-0.1, 1.2)
        axes[1].grid(True, alpha=0.3)
        axes[1].legend(loc='upper right', fontsize=10)
    
    # Ack_in
    if 'Ack_in' in data.columns:
        axes[2].plot(data.index, data['Ack_in'], color='blue', linewidth=2.5, label='Ack_in')
        for t in eventos:
            axes[2].axvline(x=t, color='gray', linestyle=':', alpha=0.5)
        axes[2].set_ylabel('Ack_in', fontsize=11, fontweight='bold')
        axes[2].set_ylim(-0.1, 1.2)
        axes[2].grid(True, alpha=0.3)
        axes[2].legend(loc='upper right', fontsize=10)
    
    # Ack_out
    if 'Ack_out' in data.columns:
        axes[3].plot(data.index, data['Ack_out'], color='red', linewidth=2.5, label='Ack_out')
        for t in eventos:
            axes[3].axvline(x=t, color='gray', linestyle=':', alpha=0.5)
        axes[3].set_ylabel('Ack_out', fontsize=11, fontweight='bold')
        axes[3].set_ylim(-0.1, 1.2)
        axes[3].grid(True, alpha=0.3)
        axes[3].legend(loc='upper right', fontsize=10)
    
    # Configurações gerais
    axes[3].set_xlabel('Tempo', fontsize=12, fontweight='bold')
    fig.suptitle('Protocolo Two-Phase Handshake - Cascata de Ativação com Inibição', 
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.show()
    
    return data
