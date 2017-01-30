echo on

cd %0\..\..
set root=%cd%
cd test

set PYTHON=%PYTHON%\python.exe
call %root%\test\run.bat

exit /b %ERRORLEVEL%
