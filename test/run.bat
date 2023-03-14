echo on

cd %0\..\..
set root=%cd%

echo %PYTHON%
echo %PIP%
echo %PIPINSTALL%

if not defined PYTHON set PYTHON=python
if "%PYTHON%" == "" set PYTHON=python
if not defined PIP set PIP=%PYTHON%\..\..\Scripts\pip
if "%PIP%" == "" set PIP=%PYTHON%\..\..\Scripts\pip
if not defined PIPINSTALL set "PIPINSTALL=%PIP% install"
if "%PIPINSTALL%" == "" set "PIPINSTALL=%PIP% install"

echo %PYTHON%
echo %PIP%
echo %PIPINSTALL%

:: run the cmany unit tests
cd test
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
set PYTHONPATH=%root%\src
%PYTHON% -m pytest --cov=..\src --cov-reset %*
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

exit /b %ERRORLEVEL%
