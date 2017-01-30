echo on

cd %0\..\..
set root=%cd%
cd test

set PYTHONPATH=%root%\src

if not defined PYTHON set PYTHON=python3
if "%PYTHON%" == "" set PYTHON=python3

%PYTHON% -m nose -d -v --with-id --nocapture %*

exit /b %ERRORLEVEL%
