@echo off
REM OmniSLM Development Setup (Windows)
REM Installs all framework packages in editable mode for local development.
REM
REM Usage:
REM   scripts\dev-install.bat

echo 🚀 Installing OmniSLM packages in development mode...

echo   [1/11] Installing omnislm-core...
pip install -e packages\omnislm-core --quiet

echo   [2/11] Installing omnislm-runtimes...
pip install -e packages\omnislm-runtimes --quiet

echo   [3/11] Installing omnislm-memory...
pip install -e packages\omnislm-memory --quiet

echo   [4/11] Installing omnislm-rag...
pip install -e packages\omnislm-rag --quiet

echo   [5/11] Installing omnislm-agents...
pip install -e packages\omnislm-agents --quiet

echo   [6/11] Installing omnislm-workflows...
pip install -e packages\omnislm-workflows --quiet

echo   [7/11] Installing omnislm-plugins...
pip install -e packages\omnislm-plugins --quiet

echo   [8/11] Installing omnislm-observability...
pip install -e packages\omnislm-observability --quiet

echo   [9/11] Installing omnislm-evaluation...
pip install -e packages\omnislm-evaluation --quiet

echo   [10/11] Installing omnislm (SDK)...
pip install -e packages\omnislm-sdk --quiet

echo   [11/11] Installing omnislm-cli...
pip install -e packages\omnislm-cli --quiet

echo.
echo ✅ All packages installed! Try:
echo    omnislm version
echo    omnislm dev doctor
echo    omnislm create chat-app --name my-app
