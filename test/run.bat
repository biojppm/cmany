echo on

set rdir=%0\..
echo rdir %cd%

set PYTHONPATH=%rdir%\src

if not defined PYTHON set PYTHON=python3
if "%PYTHON%" == "" set PYTHON=python3

%PYTHON% -m nose -d -v --with-id --nocapture %*

exit /b %ERRORLEVEL%
