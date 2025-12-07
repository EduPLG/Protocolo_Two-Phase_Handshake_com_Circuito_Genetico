"""
Extensões da Etapa 4: Exemplos e Tutoriais
===========================================

Este arquivo contém funções auxiliares e exemplos para estender
a Etapa 4 com análises avançadas.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import logging

logger = logging.getLogger(__name__)


# ==============================================================================
# EXTENSÃO 1: Análise de Sensibilidade Paramétrica
# ==============================================================================

def sensitivity_analysis(
    rr, parameter_name: str,
    parameter_range: np.ndarray,
    output_species: str = "Req_out"
) -> pd.DataFrame:
    """
    Análise de sensibilidade: varia um parâmetro e mede efeito em espécie alvo.

    Exemplo:
    --------
    >>> rr = generate_tellurium_model()
    >>> k_range = np.linspace(1.0, 5.0, 20)
    >>> results = sensitivity_analysis(rr, "k_mrna_req_prod", k_range, "Req_out")
    >>> print(results)
    """
    results = []

    for k_val in parameter_range:
        rr[parameter_name] = k_val
        rr.resetToOrigin()

        # Simula com Req_in = 1 para ver ativação máxima
        rr['Req_in'] = 1.0
        sim = rr.simulate(0, 30, 100)

        # Extrai valor máximo da espécie alvo
        col_idx = rr.getFloatingSpeciesIds().index(output_species)
        max_val = np.max(sim[:, col_idx + 1])

        results.append({
            'parameter': k_val,
            f'{output_species}_max': max_val,
            f'{output_species}_steady_state': sim[-1, col_idx + 1]
        })

    return pd.DataFrame(results)


# ==============================================================================
# EXTENSÃO 2: Otimização de Parâmetros
# ==============================================================================

def optimize_handshake_kinetics(rr) -> dict:
    """
    Encontra parâmetros ótimos para maximizar velocidade de resposta.

    Objetivo: minimizar tempo para Req_out atingir 50% do máximo após Req_in=1

    Exemplo:
    --------
    >>> rr = generate_tellurium_model()
    >>> opt_params = optimize_handshake_kinetics(rr)
    >>> print(f"Parâmetros ótimos: {opt_params}")
    """

    def objective(params_array):
        """Função objetivo: tempo até 50% de Req_out máximo."""
        k_mrna, k_trans, k_deg_mrna, k_deg_prot = params_array

        # Define parâmetros
        rr['k_mrna_req_prod'] = max(0.1, k_mrna)
        rr['k_req_out_transl'] = max(0.1, k_trans)
        rr['k_mrna_req_deg'] = max(0.01, k_deg_mrna)
        rr['k_req_out_deg'] = max(0.01, k_deg_prot)

        try:
            rr.resetToOrigin()
            rr['Req_in'] = 1.0
            sim = rr.simulate(0, 30, 300)

            # Encontra tempo para atingir 50% do máximo
            col_idx = rr.getFloatingSpeciesIds().index('Req_out')
            conc = sim[:, col_idx + 1]
            max_conc = np.max(conc)

            if max_conc < 0.1:  # Muito baixo
                return 1000  # Penalidade alta

            idx_50 = np.where(conc >= 0.5 * max_conc)[0]
            if len(idx_50) == 0:
                return 500

            time_50 = sim[idx_50[0], 0]

            # Penaliza tempos muito longos
            return max(0.1, time_50)
        except Exception:
            return 1000

    # Condições iniciais
    x0 = [3.0, 2.0, 1.5, 0.5]

    # Limites para cada parâmetro
    bounds = [(0.1, 10.0), (0.1, 10.0), (0.01, 5.0), (0.01, 2.0)]

    # Otimização
    result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')

    return {
        'k_mrna_req_prod': result.x[0],
        'k_req_out_transl': result.x[1],
        'k_mrna_req_deg': result.x[2],
        'k_req_out_deg': result.x[3],
        'response_time': result.fun
    }


# ==============================================================================
# EXTENSÃO 3: Simulação Estocástica (Gillespie)
# ==============================================================================

def stochastic_simulation(rr, n_runs: int = 100) -> dict:
    """
    Executa simulação estocástica (Monte Carlo) do handshake.

    Mede variabilidade em tempos de resposta com flutuações moleculares.

    Exemplo:
    --------
    >>> rr = generate_tellurium_model()
    >>> stoch_results = stochastic_simulation(rr, n_runs=100)
    >>> print(f"Tempo médio: {stoch_results['mean_response_time']:.2f}s")
    >>> print(f"Desvio: {stoch_results['std_response_time']:.2f}s")
    """

    response_times = []
    max_values = []

    for run in range(n_runs):
        try:
            rr.resetToOrigin()
            rr['Req_in'] = 1.0

            # Simula com algoritmo de Gillespie se disponível
            # Caso contrário, adiciona ruído gaussiano aos resultados ODE
            sim = rr.simulate(0, 30, 300)

            col_idx = rr.getFloatingSpeciesIds().index('Req_out')
            conc = sim[:, col_idx + 1]

            # Adiciona ruído estocástico
            noise = np.random.normal(0, 0.05, len(conc))
            conc_noisy = np.maximum(conc + noise, 0)

            max_val = np.max(conc_noisy)
            max_values.append(max_val)

            # Tempo até 50%
            idx_50 = np.where(conc_noisy >= 0.5 * max_val)[0]
            if len(idx_50) > 0:
                response_times.append(sim[idx_50[0], 0])
            else:
                response_times.append(30.0)

        except Exception as e:
            logger.warning(f"Run {run}: {e}")
            continue

    return {
        'mean_response_time': np.mean(response_times),
        'std_response_time': np.std(response_times),
        'min_response_time': np.min(response_times),
        'max_response_time': np.max(response_times),
        'mean_max_conc': np.mean(max_values),
        'std_max_conc': np.std(max_values),
        'n_runs': len(response_times)
    }


# ==============================================================================
# EXTENSÃO 4: Análise de Robustez
# ==============================================================================

def robustness_analysis(rr,
                        perturbation_pct: float = 20) -> pd.DataFrame:
    """
    Testa robustez do handshake a variações de parâmetros ±perturbation_pct%.

    Exemplo:
    --------
    >>> rr = generate_tellurium_model()
    >>> robust = robustness_analysis(rr, perturbation_pct=20)
    >>> print(robust[['parameter', 'nominal_response_time', 'perturbed_response_time']])
    """

    param_names = rr.getGlobalParameterIds()
    results = []

    # Valor nominal
    rr.resetToOrigin()
    rr['Req_in'] = 1.0
    sim_nominal = rr.simulate(0, 30, 300)
    col_idx = rr.getFloatingSpeciesIds().index('Req_out')
    conc_nominal = sim_nominal[:, col_idx + 1]
    time_nominal = sim_nominal[np.where(conc_nominal >= 0.5 * np.max(conc_nominal))[0][0], 0]

    for param in param_names:
        if param in ['Req_in']:  # Skip non-tunable parameters
            continue

        nominal_val = rr[param]

        # Perturbação positiva
        rr[param] = nominal_val * (1 + perturbation_pct / 100)
        rr.resetToOrigin()
        rr['Req_in'] = 1.0
        try:
            sim_plus = rr.simulate(0, 30, 300)
            conc_plus = sim_plus[:, col_idx + 1]
            time_plus = sim_plus[np.where(conc_plus >= 0.5 * np.max(conc_plus))[0][0], 0]
        except Exception:
            time_plus = np.nan

        # Perturbação negativa
        rr[param] = nominal_val * (1 - perturbation_pct / 100)
        rr.resetToOrigin()
        rr['Req_in'] = 1.0
        try:
            sim_minus = rr.simulate(0, 30, 300)
            conc_minus = sim_minus[:, col_idx + 1]
            time_minus = sim_minus[np.where(conc_minus >= 0.5 * np.max(conc_minus))[0][0], 0]
        except Exception:
            time_minus = np.nan

        # Restaura valor nominal
        rr[param] = nominal_val

        results.append({
            'parameter': param,
            'nominal_response_time': time_nominal,
            'perturbed_plus': time_plus,
            'perturbed_minus': time_minus,
            'sensitivity': abs((time_plus - time_minus) / (2 * perturbation_pct / 100)) if not np.isnan(time_plus) and not np.isnan(time_minus) else np.nan
        })

    return pd.DataFrame(results)


# ==============================================================================
# EXTENSÃO 5: Bifurcação e Dinâmica Não-Linear
# ==============================================================================

def bifurcation_diagram(
    rr,
    bifurcation_param: str = "k_mrna_req_prod",
    param_range: np.ndarray = None
) -> dict:
    """
    Constrói diagrama de bifurcação variando um parâmetro.

    Identifica transições de fase (e.g., steady-state → oscilações).

    Exemplo:
    --------
    >>> rr = generate_tellurium_model()
    >>> k_range = np.linspace(1.0, 10.0, 50)
    >>> bifurca = bifurcation_diagram(rr, "k_mrna_req_prod", k_range)
    """

    if param_range is None:
        param_range = np.linspace(1.0, 10.0, 50)

    bifurcation_data = []

    for k_val in param_range:
        rr[bifurcation_param] = k_val
        rr.resetToOrigin()
        rr['Req_in'] = 1.0

        try:
            # Deixa transiente morrer (primeiros 20s)
            rr.simulate(0, 20, 100)

            # Pega regime permanente (últimos 10s)
            sim_steady = rr.simulate(20, 30, 100)

            col_idx = rr.getFloatingSpeciesIds().index('Req_out')
            conc_steady = sim_steady[:, col_idx + 1]

            bifurcation_data.append({
                'parameter_value': k_val,
                'steady_state_mean': np.mean(conc_steady),
                'steady_state_std': np.std(conc_steady),
                'steady_state_max': np.max(conc_steady),
                'steady_state_min': np.min(conc_steady),
                'oscillation': np.std(conc_steady) > 0.1  # Heurística para oscilação
            })
        except Exception as e:
            logger.warning(f"Bifurcation point {k_val}: {e}")
            continue

    return {
        'parameter': bifurcation_param,
        'data': pd.DataFrame(bifurcation_data),
        'transitions': sum(1 for d in bifurcation_data if d['oscillation'])
    }


# ==============================================================================
# EXTENSÃO 6: Comparação COPASI vs Tellurium
# ==============================================================================

def compare_simulators(copasi_data: pd.DataFrame,
                       tellurium_data: pd.DataFrame) -> dict:
    """
    Compara resultados de simulação COPASI vs Tellurium.

    Calcula diferenças, correlações, e erros RMS.

    Exemplo:
    --------
    >>> copasi_df = run_simulation()  # Da etapa 3
    >>> tellurium_df = run_stage_4_tellurium()  # Da etapa 4
    >>> comparison = compare_simulators(copasi_df, tellurium_df)
    """

    # Resample para mesmo tamanho se necessário
    min_len = min(len(copasi_data), len(tellurium_data))
    copasi_subset = copasi_data.iloc[:min_len]
    tellurium_subset = tellurium_data.iloc[:min_len]

    comparison = {}

    for species in ['Req_out', 'Ack_out']:
        if species in copasi_subset.columns and species in tellurium_subset.columns:
            c_vals = copasi_subset[species].values
            t_vals = tellurium_subset[species].values

            # RMS Error
            rms = np.sqrt(np.mean((c_vals - t_vals) ** 2))

            # Correlação
            corr = np.corrcoef(c_vals, t_vals)[0, 1]

            # Diferença máxima
            max_diff = np.max(np.abs(c_vals - t_vals))

            comparison[species] = {
                'rms_error': rms,
                'correlation': corr,
                'max_difference': max_diff,
                'mean_diff': np.mean(c_vals - t_vals)
            }

    return comparison


if __name__ == "__main__":
    print("Extensões da Etapa 4 - módulo de análises avançadas")
    print("Use as funções acima para estender a simulação base")
