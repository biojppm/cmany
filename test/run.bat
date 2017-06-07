echo on

cd %0\..\..
set root=%cd%

echo %PYTHON%
echo %PIP%
echo %PIPINSTALL%

if not defined PYTHON set PYTHON=python3
if "%PYTHON%" == "" set PYTHON=python3
if not defined PIP set PIP=%PYTHON%\..\..\Scripts\pip
if "%PIP%" == "" set PIP=%PYTHON%\..\..\Scripts\pip
if not defined PIPINSTALL set "PIPINSTALL=%PIP% install"
if "%PIPINSTALL%" == "" set "PIPINSTALL=%PIP% install"

echo %PYTHON%
echo %PIP%
echo %PIPINSTALL%

:: test that cmany can be installed and ran
cd %root%
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
if exist dist (
   del dist/cmany-*.whl
)
%PIP% uninstall -y cmany
%PYTHON% setup.py sdist bdist_wheel
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
dir dist
for %%X IN (dist\cmany-*.whl) do (
      set WHEEL=%%X
      )
echo %WHEEL%
%PIPINSTALL% %WHEEL%
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
%PIP% show -f cmany
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmany h
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
cmany h quick_tour
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
%PIP% uninstall -y cmany
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

:: run the cmany unit tests
cd test
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
set PYTHONPATH=%root%\src
%PYTHON% -m nose -d -v --with-id --nocapture %*
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

exit /b %ERRORLEVEL%
