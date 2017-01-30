echo on

cd orig=%cd%
cd %0\..\..
set root=%cd%
cd test

set PYTHON=%PYTHON%\python.exe
call %root%\test\run.bat
set stat=%ERRORLEVEL%

cd %orig%

exit /b %stat%
