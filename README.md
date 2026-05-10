<h1 align="center">⏱️ QPA/RTA Schedulability Analysis ⏱️</h1>

## Developed by 💻

- [Fernando Schettini](https://linktr.ee/fernandoschett)

## About 🤔

This repository contains a Python implementation for exact schedulability analysis of real-time task sets. The project compares two scheduling approaches:

- **EDF** (*Earliest Deadline First*) using **QPA** (*Quick Processor-demand Analysis*);
- **Deadline Monotonic** using **RTA** (*Response Time Analysis*).

The project was developed as part of the evaluation for the **Tópicos em Sistemas de Tempo Real I** course at the **Federal University of Bahia (UFBA)**, during the 2026.1 semester, under the supervision of Professor George Lima.

The final report is available on Overleaf at this [link](https://www.overleaf.com/read/qkhjdrfftwbh#90ade5).

## Repository Overview 📝

```text
.
├── dados/
│   └── JSON datasets used as input
│
├── src/
│   └── rt_sched/
│       ├── __init__.py
│       ├── analysis.py
│       ├── experiment.py
│       └── io_utils.py
│
├── run_analysis.py
├── run_experiment.ps1
├── requirements.txt
├── README.md
└── .gitignore
```

### Main files

- `src/rt_sched/analysis.py`: implements `dbf`, QPA/EDF, and RTA/Deadline Monotonic.
- `src/rt_sched/experiment.py`: runs the analyses over all loaded task sets and summarizes results by `N`.
- `src/rt_sched/io_utils.py`: loads task sets from JSON files or directories.
- `run_analysis.py`: main script used to execute the experiment.
- `run_experiment.ps1`: PowerShell script for running the experiment on Windows.

## Requirements 🛠️

No requeriments or dependencies.

## How to Run 🏃

First, clone the repository:

```bash
git clone https://github.com/FernandoSchett/qpa-rta-schedulability-analysis.git
cd qpa-rta-schedulability-analysis
```
To run the analysis over the dataset directory, use:

```bash
python run_analysis.py dados
```

### Output description

- `summary_by_n_tasks.csv`: aggregated schedulability percentages grouped by number of tasks `N`.
- `detailed_results.json`: detailed result for each task set.
- `per_dataset_results.csv`: per-task-set output, including EDF result, DM result, `l_max`, `dbf(l_max)`, and checked QPA points.
- `results_by_dataset.csv`: aggregated results by input JSON file.
- `results_by_dataset.tex`: LaTeX table generated from the per-file aggregation.
- `lmax_analysis.txt`: basic analysis of the possible conservativeness of `l_max`.

## Academic and AI Use Disclaimer ⚠️

During the development of this project and the writing of the final report, ChatGPT was used as a support tool to improve readability, correct grammar, organize explanations, and assist with code structure and documentation. After using this tool, the content, implementation, results, and final report were reviewed and edited by the author.

The author assumes full responsibility for the correctness, integrity, and originality of the submitted work. This use is aligned with the guidelines of the Federal University of Bahia for the ethical and responsible use of generative artificial intelligence.[5]

## References 📙

[1] Sanjoy K. Baruah, Rodney R. Howell, and Louis E. Rosier. “Algorithms and Complexity Concerning the Preemptive Scheduling of Periodic, Real-Time Tasks on One Processor”. In: *Real-Time Systems* 2.4 (1990), pp. 301–324.

[2] Marco Spuri. *Analysis of Deadline Scheduled Real-Time Systems*. Technical Report RR-2772. INRIA, 1996.

[3] Fengxiang Zhang and Alan Burns. “Schedulability Analysis for Real-Time Systems with EDF Scheduling”. In: *IEEE Transactions on Computers* 58.9 (2009), pp. 1250–1258.

[4] Neil C. Audsley et al. “Applying New Scheduling Theory to Static Priority Pre-emptive Scheduling”. In: *Software Engineering Journal* 8.5 (1993), pp. 284–292.

[5] Universidade Federal da Bahia. *Guia para Uso Ético e Responsável da Inteligência Artificial Generativa na Universidade Federal da Bahia*. Universidade Federal da Bahia. Salvador, April 2025.