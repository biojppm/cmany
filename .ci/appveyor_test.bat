echo on

set orig=%cd%
cd %0\..\..
set root=%cd%
cd test

set PIP=%PYTHON%\Scripts\pip
set "PIPINSTALL=%PIP% install"
set PYTHON=%PYTHON%\python.exe
call %root%\test\run.bat
set stat=%ERRORLEVEL%

cd %orig%

exit /b %stat%
