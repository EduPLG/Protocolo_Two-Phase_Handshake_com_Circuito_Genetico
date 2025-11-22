# Protocolo **Two-Phase Handshake** com Circuito Genético  
**Estudo Científico – INE7006-08208 (2025/2)**  
*Biologia Computacional e Computação Biológica – UFSC*

Este repositório reúne o estudo e desenvolvimento de um modelo híbrido — digital e bioquímico — para a implementação do protocolo **Two-Phase Handshake** em circuitos genéticos. O trabalho envolve desde a modelagem lógica assíncrona até sua tradução para representações bioquímicas e simulações celulares.

## Etapas do Estudo

1. **Modelagem Lógica Digital**  
   Construção do modelo lógico de um circuito sequencial assíncrono utilizando portas C, buffers e o protocolo two-phase handshake, com diagramas, Logisim-evolution ou VHDL.

2. **Tradução para Modelo Bioquímico**  
   Conversão do modelo digital para representações biológicas utilizando **SBOL** (padronização de componentes) e **CelloCAD** (síntese de circuitos genéticos digitais).

3. **Implementação Bioquímica do Handshake**  
   Modelagem do liga/desliga de promotores controlados por RNAs regulatórios usando ferramentas como **COPASI**, **VCell** e **TinkerCell**.

4. **Simulação de Redes Metabólicas e Regulatórias**  
   Representação de RNAs como portadores de sinais lógicos, usando **SBML**, **BioNetGen**, **Tellurium** e **PySB** para simulação em Python.

5. **Modelagem do Protocolo em Nível Bioquímico**  
   Modelos baseados em ativação de promotores, transcrição de RNA e geração de sinais de *acknowledge*. Uso de **Petri Nets** (Snakes, PEP Tool) e **SBML2PN** para converter redes bioquímicas em redes de Petri.

6. **Análise de Robustez**  
   Avaliação da sensibilidade do circuito a ruído molecular e variações temporais por meio de simulações determinísticas e estocásticas em **StochKit** e **COPASI**.

7. **Ajuste de Parâmetros (Opcional)**  
   Otimização de taxas bioquímicas, como transcrição, degradação de RNA e afinidades de ligação.


## Virtual enviroment

- Criar um ambiente virtual
```bash
python -m venv venv --system-site-packages
```
- Ativar o ambiente virtual
```bash
.\venv\Scripts\activate 
```

- Para desativar:
```bash
deactivate
```

## Install requerements

```bash
pip install -r requirements.txt
```

```bash
pip install git+https://github.com/copasi/basico.git
```