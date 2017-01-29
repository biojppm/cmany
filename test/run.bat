echo on

set mydir=%0\..
echo mydir %cd%

set PYTHONPATH=%mydir%\..\src

if not defined PYTHON set PYTHON=python3
if "%PYTHON%" == "" set PYTHON=python3

%PYTHON% -m nose -d -v --with-id --nocapture %*

exit /b %ERRORLEVEL%
