@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0src
echo Starting Hotel Agent on http://127.0.0.1:8080
echo Docs: http://127.0.0.1:8080/docs
echo Health: http://127.0.0.1:8080/health
echo.
python -m uvicorn hotel_agent.main:app --host 127.0.0.1 --port 8080 --reload
