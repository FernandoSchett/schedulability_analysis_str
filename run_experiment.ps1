param(
    [string]$InputPath = "dados",
    [string]$SummaryCsv = "summary_by_n_tasks.csv",
    [string]$DetailsJson = "detailed_results.json"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Runner = Join-Path $ProjectRoot "run_analysis.py"

if (-not (Test-Path $PythonExe)) {
    throw "Python da venv nao encontrado em: $PythonExe"
}

if (-not (Test-Path $Runner)) {
    throw "Script principal nao encontrado em: $Runner"
}

Push-Location $ProjectRoot
try {
    & $PythonExe $Runner $InputPath --summary-csv $SummaryCsv --details-json $DetailsJson
}
finally {
    Pop-Location
}
