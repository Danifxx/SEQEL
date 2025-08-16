@echo off
setlocal
if not exist .venv (
  echo Creating venv...
  py -3 -m venv .venv
)
call .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
set PYTHONPATH=%CD%
uvicorn app.main:app --reload
