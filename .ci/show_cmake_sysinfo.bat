ECHO ON

echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
cmake -G "Visual Studio 12 2013" --system-information
echo errorlevel for "Visual Studio 12 2013" is %errorlevel%

echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
cmake -G "Visual Studio 12 2013 Win64" --system-information
echo errorlevel for "Visual Studio 12 2013 Win64" is %errorlevel%

echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
cmake -G "Visual Studio 14 2015" --system-information
echo errorlevel for "Visual Studio 14 2015" is %errorlevel%

echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
cmake -G "Visual Studio 14 2015 Win64" --system-information
echo errorlevel for "Visual Studio 14 2015 Win64" is %errorlevel%

echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
cmake -G "Visual Studio 14 2015" -T v140_clang_c2 --system-information
echo errorlevel for "Visual Studio 14 2015" is %errorlevel%

echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
cmake -G "Visual Studio 14 2015 Win64" -T v140_clang_c2 --system-information
echo errorlevel for "Visual Studio 14 2015 Win64" is %errorlevel%

