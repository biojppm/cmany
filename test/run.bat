echo on

cd %0\..\..
set root=%cd%
cd test

set PYTHONPATH=%root%\src

if not defined PYTHON set PYTHON=python3
if "%PYTHON%" == "" set PYTHON=python3
if not defined PIP set PIP="pip3 --user"
if "%PIP%" == "" set PYTHON="pip3 --user"

%PYTHON% -m nose -d -v --with-id --nocapture %*
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

cd %root%
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

if exist dist (
   del dist/cmany-*.whl
)
%PYTHON% setup.py sdist bdist_wheel
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

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

exit /b %ERRORLEVEL%
