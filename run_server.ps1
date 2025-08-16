if (!(Test-Path ".venv")) {
  py -3 -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
uvicorn app.main:app --reload
