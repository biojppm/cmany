echo on

set cwd=%cd%
echo Running in directory %cd%

set PYTHONPATH=%cwd%\src

%PYTHON%\python.exe -m nose -d -v --with-id --nocapture

exit /b %ERRORLEVEL%
