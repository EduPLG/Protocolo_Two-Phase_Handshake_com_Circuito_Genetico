"""
Etapa 4: Simulação de Redes Metabólicas e Regulatórias
======================================================

Implementação do Two-Phase Handshake Protocol usando:
- PySB (Protein Synthesis Backend) para definição modular
- Tellurium para simulação e integração numérica
- RNAs como portadores de sinais lógicos

Abordagem:
1. Definem-se espécies moleculares: mRNA_Req, Proteína_Req_out, mRNA_Ack, Proteína_Ack_out
2. Reações com taxas definidas explicitamente (não implícitas por estequiometria)
3. Sinais lógicos implementados via concentrações: alto (≈1.0), baixo (≈0.0)
4. Simulação determinística e estocástica possíveis
5. Validação cruzada com resultados COPASI

Cascata lógica:
    Req_in (sinal externo)
         ↓ [produção de mRNA_Req]
    mRNA_Req ─→ Proteína_Req_out
         ↓ [degradação]
    mRNA_Ack ←─ ativado por Req_out
         ↓ [tradução]
    Proteína_Ack_out ──┐
                       ↓ [inibição negativa]
    Proteína_Req_out ←┘ (feedback)
"""

import tellurium as te
import pandas as pd
import matplotlib.pyplot as plt
import logging
from utils.logger_functions import _timed_debug, _timed

logger = logging.getLogger(__name__)

# ==============================================================================
# ABORDAGEM 1: Usando Tellurium com Antimony (linguagem de texto para modelos)
# ==============================================================================


def generate_tellurium_model():
    """
    Cria modelo Two-Phase Handshake usando Antimony (sintaxe do Tellurium).

    Espécies:
    - Req_in: sinal externo (0 ou 1) - será simulado manualmente
    - mRNA_Req: mensageiro de requisição
    - Req_out: proteína de saída de requisição
    - mRNA_Ack: mensageiro de acknowledge
    - Ack_out: proteína de acknowledge

    Reações:
    1. Produção de mRNA_Req (ativada por Req_in)
    2. Degradação de mRNA_Req
    3. Tradução mRNA_Req → Req_out
    4. Degradação de Req_out
    5. Produção de mRNA_Ack (ativada por Req_out)
    6. Degradação de mRNA_Ack
    7. Tradução mRNA_Ack → Ack_out
    8. Degradação de Ack_out (inibida por Ack_out - feedback)
    """
    with _timed_debug(logger, "Criando modelo Tellurium com Antimony"):

        antimony_code = """
        // ===== PARÂMETROS =====
        var Req_in;  // Sinal externo (será manipulado)
        Req_in = 0.0;

        // Constantes de taxa (cinética)
        k_mrna_req_prod = 3.0;      // Produção de mRNA_Req
        k_mrna_req_deg = 2.5;       // Degradação de mRNA_Req
        k_req_out_transl = 1.5;     // Tradução mRNA_Req → Req_out
        k_req_out_deg = 1.5;        // Degradação de Req_out

        k_mrna_ack_prod = 3.0;      // Produção de mRNA_Ack
        k_mrna_ack_deg = 2.5;       // Degradação de mRNA_Ack
        k_ack_out_transl = 1.5;     // Tradução mRNA_Ack → Ack_out
        k_ack_out_deg = 25.0;       // Inibição mútua: MUITO forte para manter relação direta com Req_out
        k_ack_out_basal = 0.5;      // Produção basal de Ack_out (reduzido)
        k_ack_out_deg_basal = 0.5;  // Degradação basal de Ack_out

        K_req = 0.5;                // Threshold de Req_out para ativar mRNA_Ack
        K_ack = 0.5;                // Threshold de Ack_out para feedback

        // ===== ESPÉCIES (concentrações) =====
        var mRNA_Req, Req_out, mRNA_Ack, Ack_out;

        mRNA_Req = 0.0;
        Req_out = 0.0;
        mRNA_Ack = 0.0;
        Ack_out = 1.0;  // Começa alto (inibidor desativado)

        // ===== REAÇÕES =====

        // R1: Produção de mRNA_Req (ativada por Req_in, Hill n=2)
        // Taxa = k * Req_in^2 / (K^2 + Req_in^2)
        J1: -> mRNA_Req; k_mrna_req_prod * Req_in^2 / (0.25 + Req_in^2);

        // R2: Degradação de mRNA_Req
        J2: mRNA_Req -> ; k_mrna_req_deg * mRNA_Req;

        // R3: Tradução mRNA_Req → Req_out
        J3: mRNA_Req -> mRNA_Req + Req_out; k_req_out_transl * mRNA_Req;

        // R4: Degradação de Req_out
        J4: Req_out -> ; k_req_out_deg * Req_out;

        // R5: Produção de mRNA_Ack (ativada por Req_out, Hill n=2)
        // Taxa = k * Req_out^2 / (K^2 + Req_out^2)
        J5: -> mRNA_Ack; k_mrna_ack_prod * Req_out^2 / (K_req^2 + Req_out^2);

        // R6: Degradação de mRNA_Ack
        J6: mRNA_Ack -> ; k_mrna_ack_deg * mRNA_Ack;

        // R7: Tradução mRNA_Ack → Ack_out
        J7: mRNA_Ack -> mRNA_Ack + Ack_out; k_ack_out_transl * mRNA_Ack;

        // R8: Inibição mútua - Ack_out é consumido por Req_out (feedback negativo real)
        // Quando Req_out sobe, consome Ack_out MUITO rapidamente
        J8: Req_out + Ack_out -> Req_out; k_ack_out_deg * Req_out * Ack_out;

        // R9: Inibição de Ack_out por mRNA_Ack (competição por recursos)
        // Quando mRNA_Ack sobe, reduz produção de Ack_out
        // Taxa = k * [mRNA_Ack^2 / (1 + mRNA_Ack^2)] (só consome, não produz)
        J9: Ack_out -> ; 3.0 * (mRNA_Ack^2 / (1.0 + mRNA_Ack^2)) * Ack_out;

        // R10: Produção FORTE de Ack_out (sempre tenta manter em 1)
        // Produção constitutiva que domina quando mRNA_Ack e Req_out são baixos
        J10: -> Ack_out; 2.5;

        // R11: Degradação proporcional à concentração de Ack_out
        // Taxa = 5.0 * [Ack_out^2 / (1 + Ack_out^2)] - aumenta quando Ack_out > 1
        J11: Ack_out -> ; 5.0 * (Ack_out^2 / (1.0 + Ack_out^2));
        """

        try:
            rr = te.loadAntimonyModel(antimony_code)
            logger.info("✓ Modelo Tellurium criado com sucesso!")
            logger.info(f"  Espécies: {rr.getFloatingSpeciesIds()}")
            logger.info(f"  Parâmetros: {rr.getGlobalParameterIds()}")
            return rr
        except Exception as e:
            logger.error(f"❌ Erro ao criar modelo: {e}")
            raise


def run_tellurium_simulation(rr) -> pd.DataFrame:
    """
    Executa simulação em 5 fases com mudanças de Req_in.
    Fase 1: Req_in=0 (t=0-10)
    Fase 2: Req_in=1 (t=10-30)
    Fase 3: Req_in=0 (t=30-50)
    Fase 4: Req_in=1 (t=50-70)
    Fase 5: Req_in=0 (t=70-100)
    """
    with _timed_debug(logger, "Executando simulação Tellurium 5 fases"):

        all_data = []
        species_names = rr.getFloatingSpeciesIds()

        # ===== FASE 1: t=0-10, Req_in=0 =====
        rr['Req_in'] = 0.0
        rr.resetToOrigin()
        result1 = rr.simulate(0, 10, 100)
        # Extrai dados: coluna 0 é tempo, depois as espécies
        time1 = result1[:, 0]
        df1 = pd.DataFrame({name: result1[:, i + 1] for i, name in enumerate(species_names)}, index=time1)
        df1['Req_in'] = 0.0
        all_data.append(df1)

        logger.info(f"✓ Fase 1 (t=0-10, Req_in=0): Req_out={df1['Req_out'].iloc[-1]:.4f}, Ack_out={df1['Ack_out'].iloc[-1]:.4f}")

        # ===== FASE 2: t=10-30, Req_in=1 =====
        rr['Req_in'] = 1.0
        # Inicia do estado final da fase 1
        for i, name in enumerate(species_names):
            rr[name] = df1[name].iloc[-1]

        result2 = rr.simulate(10, 30, 200)
        time2 = result2[:, 0]
        df2 = pd.DataFrame({name: result2[:, i + 1] for i, name in enumerate(species_names)}, index=time2)
        df2['Req_in'] = 1.0
        all_data.append(df2)

        logger.info(f"✓ Fase 2 (t=10-30, Req_in=1): Req_out={df2['Req_out'].iloc[-1]:.4f}, Ack_out={df2['Ack_out'].iloc[-1]:.4f}")

        # ===== FASE 3: t=30-50, Req_in=0 =====
        rr['Req_in'] = 0.0
        for i, name in enumerate(species_names):
            rr[name] = df2[name].iloc[-1]

        result3 = rr.simulate(30, 50, 200)
        time3 = result3[:, 0]
        df3 = pd.DataFrame({name: result3[:, i + 1] for i, name in enumerate(species_names)}, index=time3)
        df3['Req_in'] = 0.0
        all_data.append(df3)

        logger.info(f"✓ Fase 3 (t=30-50, Req_in=0): Req_out={df3['Req_out'].iloc[-1]:.4f}, Ack_out={df3['Ack_out'].iloc[-1]:.4f}")

        # ===== FASE 4: t=50-70, Req_in=1 =====
        rr['Req_in'] = 1.0
        for i, name in enumerate(species_names):
            rr[name] = df3[name].iloc[-1]

        result4 = rr.simulate(50, 70, 200)
        time4 = result4[:, 0]
        df4 = pd.DataFrame({name: result4[:, i + 1] for i, name in enumerate(species_names)}, index=time4)
        df4['Req_in'] = 1.0
        all_data.append(df4)

        logger.info(f"✓ Fase 4 (t=50-70, Req_in=1): Req_out={df4['Req_out'].iloc[-1]:.4f}, Ack_out={df4['Ack_out'].iloc[-1]:.4f}")

        # ===== FASE 5: t=70-100, Req_in=0 =====
        rr['Req_in'] = 0.0
        for i, name in enumerate(species_names):
            rr[name] = df4[name].iloc[-1]

        result5 = rr.simulate(70, 100, 300)
        time5 = result5[:, 0]
        df5 = pd.DataFrame({name: result5[:, i + 1] for i, name in enumerate(species_names)}, index=time5)
        df5['Req_in'] = 0.0
        all_data.append(df5)

        logger.info(f"✓ Fase 5 (t=70-100, Req_in=0): Req_out={df5['Req_out'].iloc[-1]:.4f}, Ack_out={df5['Ack_out'].iloc[-1]:.4f}")

        # Combina todos os dados
        data = pd.concat(all_data, ignore_index=False)

        logger.info(f"✅ Simulação Tellurium 5 fases: {len(data)} pontos com CONTINUIDADE")

        return data


def show_tellurium_plot(data: pd.DataFrame):
    """Exibe gráficos da simulação Tellurium."""
    logger.debug(f"Colunas: {list(data.columns)}")
    
    fig, axes = plt.subplots(5, 1, figsize=(16, 14), sharex=True)
    eventos = [10, 30, 50, 70]

    # Req_in
    if 'Req_in' in data.columns:
        axes[0].plot(data.index, data['Req_in'], color='green', linewidth=2.5, label='Req_in')
        for t in eventos:
            axes[0].axvline(x=t, color='gray', linestyle=':', alpha=0.5)
        axes[0].set_ylabel('Req_in', fontsize=11, fontweight='bold')
        axes[0].set_ylim(-0.1, 1.2)
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()

    # mRNA_Req
    if 'mRNA_Req' in data.columns:
        axes[1].plot(data.index, data['mRNA_Req'], color='blue', linewidth=2, label='mRNA_Req')
        for t in eventos:
            axes[1].axvline(x=t, color='gray', linestyle=':', alpha=0.5)
        axes[1].set_ylabel('mRNA_Req', fontsize=11, fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()

    # Req_out
    if 'Req_out' in data.columns:
        axes[2].plot(data.index, data['Req_out'], color='orange', linewidth=2.5, label='Req_out')
        for t in eventos:
            axes[2].axvline(x=t, color='gray', linestyle=':', alpha=0.5)
        axes[2].set_ylabel('Req_out', fontsize=11, fontweight='bold')
        axes[2].grid(True, alpha=0.3)
        axes[2].legend()

    # mRNA_Ack e Ack_out
    if 'mRNA_Ack' in data.columns:
        axes[3].plot(data.index, data['mRNA_Ack'], color='purple', linewidth=2, label='mRNA_Ack')
        for t in eventos:
            axes[3].axvline(x=t, color='gray', linestyle=':', alpha=0.5)
        axes[3].set_ylabel('mRNA_Ack', fontsize=11, fontweight='bold')
        axes[3].grid(True, alpha=0.3)
        axes[3].legend()

    if 'Ack_out' in data.columns:
        axes[4].plot(data.index, data['Ack_out'], color='red', linewidth=2.5, label='Ack_out')
        for t in eventos:
            axes[4].axvline(x=t, color='gray', linestyle=':', alpha=0.5)
        axes[4].set_ylabel('Ack_out', fontsize=11, fontweight='bold')
        axes[4].set_ylim(-0.1, 1.5)
        axes[4].grid(True, alpha=0.3)
        axes[4].legend()

    axes[4].set_xlabel('Tempo', fontsize=12, fontweight='bold')
    fig.suptitle('Two-Phase Handshake - Simulação Tellurium (Rede Metabólica com RNAs)',
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.show()


# ==============================================================================
# FUNÇÃO PRINCIPAL: Orquestra etapa 4
# ==============================================================================

def run_stage_4_tellurium():
    """Executa Etapa 4: Simulação com Tellurium."""
    with _timed(logger, "(Etapa 4) Simulação de Redes Metabólicas com Tellurium"):

        # Gera modelo
        rr = generate_tellurium_model()

        # Executa simulação
        data = run_tellurium_simulation(rr)

        # Exibe resultados
        show_tellurium_plot(data)

        return data


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    data = run_stage_4_tellurium()
    print("\n✅ Etapa 4 concluída com sucesso!")
    print(f"   Total de pontos: {len(data)}")
    print(f"   Intervalo de tempo: [{data.index.min():.1f}, {data.index.max():.1f}]")
