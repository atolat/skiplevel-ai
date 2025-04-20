@echo off
echo Setting up SkipLevel Agent...

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo uv is not installed. Installing uv...
    pip install uv
)

REM Create virtual environment
echo Creating virtual environment...
uv venv

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
uv pip install -e .

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env file to add your API keys.
)

echo Setup complete! You can now run the application with:
echo chainlit run chainlit_app.py 