echo on

cd %0\..\..
set root=%cd%

if not defined PY set PY=python3
if "%PY%" == "" set PY=python3
if not defined PIP set PIP=pip
if "%PIP%" == "" set PIP=pip
if not defined PIPINSTALL set "PIPINSTALL=pip install"
if "%PIPINSTALL%" == "" set "PIPINSTALL=pip install"

:: test that cmany can be installed and ran
cd %root%
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
if exist dist (
   del dist/cmany-*.whl
)
%PY% setup.py sdist bdist_wheel
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
%PIP% uninstall -y cmany
%PIPINSTALL% dist/cmany-*.whl
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
%PIP% show -f cmany
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmany h
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmany h quick_tour
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
%PIP% uninstall -y cmany
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

:: cd test
:: if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
:: set PYPATH=%root%\src
:: %PY% -m nose -d -v --with-id --nocapture %*
:: if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

exit /b %ERRORLEVEL%
