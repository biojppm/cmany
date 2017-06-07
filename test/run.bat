echo on

cd %0\..\..
set root=%cd%

if not defined PYTHON set PYTHON=python3
if "%PYTHON%" == "" set PYTHON=python3
if not defined PIP set PIP=pip3
if "%PIP%" == "" set PYTHON=pip3

:: test that cmany can be installed and ran
cd %root%
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
if exist dist (
   del dist/cmany-*.whl
)
%PYTHON% setup.py sdist bdist_wheel
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
%PIP% uninstall cmany
%PIP% install --user dist/cmany-*.whl
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
%PIP% show -f cmany
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmany h
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmany h quick_tour
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
%PIP% uninstall cmany
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

:: cd test
:: if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
:: set PYTHONPATH=%root%\src
:: %PYTHON% -m nose -d -v --with-id --nocapture %*
:: if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

exit /b %ERRORLEVEL%
