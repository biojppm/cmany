echo on

set cwd=%cd%
echo Running in directory %cd%

set PYTHONPATH=src
%PYTHON%\\python.exe -m nose -v --with-id --nocapture

