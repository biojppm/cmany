echo on

set root=%0\..\..
echo root is %root%

set PYTHON=%PYTHON%\python.exe
call %root%\test\run.bat

exit /b %ERRORLEVEL%
