# pycmake

Easily build several variations of a CMake C/C++ project. These variations
consist in selecting different compilers, cmake build types, processor
architectures (WIP) or operating systems (also WIP).

Aside from being able to build many variations of the project with a
single command (eg for final deployment), a distinct advantage
is avoiding a full rebuild when the build type changes (like when using
Visual Studio).

## Examples

Configure and build a CMakeLists.txt project located on the dir above.
The build trees will be placed under a folder "build" located on the
current dir. Likewise, installation will be set to a sister dir
named "install". A c++ compiler will be selected from the path, and the
CMAKE_BUILD_TYPE will be set to Release.

```
$  pycmake.py -b ..
```

Same as above, but now look for CMakeLists.txt on the current dir.

```
$  pycmake.py -b .
```

Same as above.

```
$  pycmake.py -b
```

Same as above, and additionally install.

```
$  pycmake.py -i
```

Build both Debug and Release build types (resulting in 2 build trees).

```
$  pycmake.py -t Debug,Release
```

Build using both clang++ and g++ (2 build trees).

```
$  pycmake.py -p clang++,g++
```

Build using both clang++,g++ and in Debug,Release modes (4 build trees).

```
$  pycmake.py -p clang++,g++ -t Debug,Release
```

Build using clang++,g++,icpc in Debug,Release,MinSizeRel modes (9 build trees).

```
$  pycmake.py -p clang++,g++,icpc -t Debug,Release,MinSizeRel
```
  
## License
Licensed under the BSD License.

## Usage

```
usage: pycmake.py [-c,--configure] [-b,--build] [-i,--install] [options...] [proj-dir]

Handle several cmake build trees of a single project

positional arguments:
  proj-dir              the directory where CMakeLists.txt is located
                        (defaults to the current directory ie, "."). Passing a
                        directory which does not contain a CMakeLists.txt will
                        cause an exception.

optional arguments:
  -h, --help            show this help message and exit
  --build-dir BUILD_DIR
                        set the build root (defaults to ./build)
  --install-dir INSTALL_DIR
                        set the install root (defaults to ./install)
  -G GENERATOR, --generator GENERATOR
                        set the cmake generator
  -j JOBS, --jobs JOBS  build with the given number of parallel jobs (defaults
                        to 4 on this machine). This may not work with every
                        generator.

Available commands:
  -c, --configure       only configure the selected builds
  -b, --build           build the selected builds, configuring before if
                        necessary
  -i, --install         install the selected builds, configuring and building
                        before if necessary
  --clean               clean the selected builds
  --create-tree         just create the build tree and the cmake preload
                        scripts

Selecting the builds:
  -s os1,os2,..., --systems os1,os2,...
                        (WIP) restrict actions to the given operating systems.
                        This feature requires os-specific toolchains and is
                        currently a WIP.
  -a arch1,arch2,..., --architectures arch1,arch2,...
                        (WIP) restrict actions to the given processor
                        architectures
  -p compiler1,compiler2,..., --compilers compiler1,compiler2,...
                        restrict actions to the given compilers
  -t type1,type2,..., --build-types type1,type2,...
                        restrict actions to the given build types (eg Release
                        or Debug)
  -v variant1,variant2,..., --variants variant1,variant2,...
                        (WIP) restrict actions to the given variants

Commands that show info:
  --show-builds
  --show-systems
  --show-architectures
  --show-build-types
  --show-compilers
  --show-variants
```
