@echo off
echo Building FOR-BAZI Windows executable...
echo.

pip install pyinstaller --quiet

pyinstaller --onefile ^
    --name "玄冥命理终端" ^
    --add-data "streamlit_app.py;." ^
    --add-data "engine;engine" ^
    --add-data "prompts;prompts" ^
    --add-data "tools;tools" ^
    --add-data "agent;agent" ^
    --add-data "mcp_server;mcp_server" ^
    --hidden-import streamlit ^
    --hidden-import lunar ^
    --hidden-import openai ^
    --hidden-import plotly ^
    --hidden-import pandas ^
    --collect-all streamlit ^
    --collect-all lunar_python ^
    --noconsole ^
    launcher.py

echo.
echo Build complete! Executable is in dist\玄冥命理终端.exe
pause
