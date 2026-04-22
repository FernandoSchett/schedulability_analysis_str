# Analise Exata de Escalonabilidade: EDF (QPA) vs DM (RTA)

Este projeto implementa:

- **RTA para Prioridade Fixa com Deadline Monotonic (DM)**
- **QPA para EDF** com:
  - jitter de liberacao (`J > 0`)
  - prazos restritos (`D <= T`)
  - backtracking seguro (`t <- dbf(t)`)

A implementacao segue as formas classicas de:

- Audsley et al. (RTA em prioridade fixa)
- Spuri (dbf com jitter)
- Zhang & Burns (QPA)

## 1) Modelagem

Cada tarefa `tau_i` e definida por:

- `C_i`: WCET
- `T_i`: periodo minimo (sporadic)
- `D_i`: deadline relativo
- `J_i`: jitter de liberacao

## 2) RTA para DM

As tarefas sao ordenadas por deadline crescente (Deadline Monotonic).

Para cada tarefa `i`, calcula-se o ponto fixo:

\[
R_i = C_i + \sum_{j \in hp(i)} \left\lceil \frac{R_i + J_j}{T_j} \right\rceil C_j
\]

Criterio de teste de deadline com jitter proprio:

\[
R_i + J_i \le D_i
\]

## 3) dbf com jitter (EDF)

Para cada tarefa:

\[
dbf_i(t) = \max\left(0, \left\lfloor \frac{t - D_i + J_i}{T_i} \right\rfloor + 1\right) C_i
\]

Demanda total:

\[
dbf(t) = \sum_i dbf_i(t)
\]

## 4) QPA com backtracking seguro

O teste exato de EDF verifica violacao quando `dbf(t) > t` em pontos criticos.

Com jitter, pontos criticos por tarefa:

\[
t = D_i - J_i + kT_i, \quad k \ge 0
\]

No algoritmo QPA:

1. Inicia em `t = l_max`.
2. Se `dbf(t) > t`, o conjunto e nao escalonavel em EDF.
3. Se `dbf(t) = t`, avanca para o ponto critico imediatamente anterior.
4. Se `dbf(t) < t`, aplica backtracking seguro `t <- dbf(t)` e alinha para o maior ponto critico `<= t`.
5. Se nao houver mais ponto critico positivo, o conjunto e escalonavel.

## 5) Estrutura

- `src/rt_sched/analysis.py`: `rta_deadline_monotonic`, `dbf`, `qpa`
- `src/rt_sched/io_utils.py`: leitura de multiplos JSONs
- `src/rt_sched/experiment.py`: execucao em lote e agregacao por `n_tasks`
- `run_analysis.py`: CLI principal

## 6) Execucao

```bash
python run_analysis.py examples
```

Com saidas padrao:

- `summary_by_n_tasks.csv`
- `detailed_results.json`

Tabela impressa no terminal:

```text
N    EDF (%)    DM (%)    count
```

## 7) Observacoes de fidelidade

- Sem heuristicas de aproximacao no lugar dos testes exatos.
- Jitter esta presente explicitamente tanto no RTA quanto no dbf.
- O QPA inclui mecanismo de retrocesso seguro via `t <- dbf(t)`.
