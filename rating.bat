@echo off
setlocal

rem Set this to the directory that contains the chess-rating project.
set "PROJECT_DIR=%USERPROFILE%\dev\python\chess-rating"
set "VENV_PYTHON=%PROJECT_DIR%\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Could not find virtualenv Python at "%VENV_PYTHON%".
    exit /b 1
)

pushd "%PROJECT_DIR%" >nul
"%VENV_PYTHON%" -m rating %*
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul

exit /b %EXIT_CODE%
