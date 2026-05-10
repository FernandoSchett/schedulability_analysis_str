<h1 align="center">⏱️ QPA/RTA Schedulability Analysis ⏱️</h1>

<div align="center">
  <p>
    Exact schedulability analysis of real-time task sets comparing EDF/QPA and Deadline Monotonic/RTA with release jitter.
  </p>
</div>

## Developed by 💻

- [Fernando Schettini](https://linktr.ee/fernandoschett)

## About 🤔

This repository contains a Python implementation for exact schedulability analysis of real-time task sets. The project compares two scheduling approaches:

- **EDF** (*Earliest Deadline First*) using **QPA** (*Quick Processor-demand Analysis*);
- **Deadline Monotonic** using **RTA** (*Response Time Analysis*).

The project was developed as part of the evaluation for the **Tópicos em Sistemas de Tempo Real I** course at the **Federal University of Bahia (UFBA)**, during the 2026.1 semester, under the supervision of Professor George Lima.

The implemented tool reads synthetic task sets in JSON format, executes both schedulability analyses, and generates summarized and detailed output files for comparison.

The final report is available on Overleaf at this [link](https://www.overleaf.com/read/qkhjdrfftwbh#90ade5).

## Main Features 🧪

- JSON task set reader;
- EDF schedulability analysis using QPA;
- Processor-demand function with release jitter;
- Deadline Monotonic priority assignment;
- Response Time Analysis with release jitter;
- Aggregated results by number of tasks;
- Per-dataset result summaries;
- Detailed JSON output for debugging and validation;
- Basic analysis of the conservativeness of `l_max`;
- LaTeX table generation for report usage.

## Task Model 📌

Each task is represented by:

- `C`: worst-case execution time;
- `T`: period;
- `D`: relative deadline;
- `J`: release jitter.

The datasets contain multiple task sets with constrained deadlines and release jitter.

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

- Python 3.10 or newer

No external Python dependencies are required. The project uses only modules from the Python standard library.

Therefore, the `requirements.txt` file is intentionally empty or only contains a note indicating that no external packages are needed.

## How to Run 🏃

First, clone the repository:

```bash
git clone https://github.com/FernandoSchett/qpa-rta-schedulability-analysis.git
cd qpa-rta-schedulability-analysis
```

Optionally, create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Since the project has no external dependencies, there is no package installation step required.

To run the analysis over the dataset directory, use:

```bash
python run_analysis.py dados
```

The script also accepts one or more specific JSON files:

```bash
python run_analysis.py dados/tasksets_n15_easy.json dados/tasksets_n50_easy.json
```

To disable recursive search inside directories, use:

```bash
python run_analysis.py dados --no-recursive
```

You can also choose the names of the main output files:

```bash
python run_analysis.py dados --summary-csv summary_by_n_tasks.csv --details-json detailed_results.json
```

## Generated Outputs 📊

After running the experiment, the script generates the following files:

```text
summary_by_n_tasks.csv
detailed_results.json
per_dataset_results.csv
results_by_dataset.csv
results_by_dataset.tex
lmax_analysis.txt
```

### Output description

- `summary_by_n_tasks.csv`: aggregated schedulability percentages grouped by number of tasks `N`.
- `detailed_results.json`: detailed result for each task set.
- `per_dataset_results.csv`: per-task-set output, including EDF result, DM result, `l_max`, `dbf(l_max)`, and checked QPA points.
- `results_by_dataset.csv`: aggregated results by input JSON file.
- `results_by_dataset.tex`: LaTeX table generated from the per-file aggregation.
- `lmax_analysis.txt`: basic analysis of the possible conservativeness of `l_max`.

## Example Output 📈

The aggregated output by number of tasks has the following format:

```csv
N,count,EDF (%),DM (%)
15,3000,49.4,3.8
50,3000,49.733333333333334,3.066666666666667
100,3000,49.96666666666667,4.666666666666667
```

Where:

- `N`: number of tasks in each task set;
- `count`: number of task sets analyzed for that value of `N`;
- `EDF (%)`: percentage of task sets schedulable under EDF/QPA;
- `DM (%)`: percentage of task sets schedulable under Deadline Monotonic/RTA.

## Dataset Structure 📁

The expected JSON input contains task sets with the following structure:

```json
{
  "id": "15_hard_sched_0",
  "n_tasks": 15,
  "tasks": [
    {
      "C": 1.25,
      "T": 10.0,
      "D": 8.5,
      "J": 0.2
    }
  ],
  "l_max": 250435.0,
  "schedulable": true,
  "class": "hard"
}
```

The script accepts both:

- a single JSON object containing one task set;
- a JSON list containing multiple task sets.

## Academic and AI Use Disclaimer ⚠️

During the development of this project and the writing of the final report, ChatGPT was used as a support tool to improve readability, correct grammar, organize explanations, and assist with code structure and documentation. After using this tool, the content, implementation, results, and final report were reviewed and edited by the author.

The author assumes full responsibility for the correctness, integrity, and originality of the submitted work. This use is aligned with the guidelines of the Federal University of Bahia for the ethical and responsible use of generative artificial intelligence.

## References 📙

[1] Sanjoy K. Baruah, Rodney R. Howell, and Louis E. Rosier. “Algorithms and Complexity Concerning the Preemptive Scheduling of Periodic, Real-Time Tasks on One Processor”. In: *Real-Time Systems* 2.4 (1990), pp. 301–324.

[2] Marco Spuri. *Analysis of Deadline Scheduled Real-Time Systems*. Technical Report RR-2772. INRIA, 1996.

[3] Fengxiang Zhang and Alan Burns. “Schedulability Analysis for Real-Time Systems with EDF Scheduling”. In: *IEEE Transactions on Computers* 58.9 (2009), pp. 1250–1258.

[4] Neil C. Audsley et al. “Applying New Scheduling Theory to Static Priority Pre-emptive Scheduling”. In: *Software Engineering Journal* 8.5 (1993), pp. 284–292.

[5] Universidade Federal da Bahia. *Guia para Uso Ético e Responsável da Inteligência Artificial Generativa na Universidade Federal da Bahia*. Universidade Federal da Bahia. Salvador, April 2025.

## License 📜

This project is intended for academic use. Add a license file if the repository will be publicly distributed.