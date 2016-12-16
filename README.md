# PyCMake

```
usage: pycmake.py [-h] [-f] [-b] [-i] [--create-tree] [--show-builds]
                  [--show-systems] [--show-architectures] [--show-modes]
                  [--show-compilers] [--show-variants] [-s os1,os2,...]
                  [-a arch1,arch2,...] [-m mode1,mode2,...]
                  [-c compiler1,compiler2,...] [-v variant1,variant2,...]
                  [--build-dir BUILD_DIR] [--install-dir INSTALL_DIR]
                  [--num-processors NUM_PROCESSORS]
                  [proj_dir]

Handle several cmake build trees of a single project

positional arguments:
  proj_dir

optional arguments:
  -h, --help            show this help message and exit
  --build-dir BUILD_DIR
                        set the build root (defaults to ./build)
  --install-dir INSTALL_DIR
                        set the install root (defaults to ./install)
  --num-processors NUM_PROCESSORS
                        build with the given number of processors

Available commands:
  -f, --configure
  -b, --build
  -i, --install
  --create-tree
  --show-builds
  --show-systems
  --show-architectures
  --show-modes
  --show-compilers
  --show-variants

Configs:
  -s os1,os2,..., --systems os1,os2,...
                        restrict actions to the given operating systems
  -a arch1,arch2,..., --architectures arch1,arch2,...
                        restrict actions to the given processor architectures
  -m mode1,mode2,..., --modes mode1,mode2,...
                        restrict actions to the given compilation modes
  -c compiler1,compiler2,..., --compilers compiler1,compiler2,...
                        restrict actions to the given compilers
  -v variant1,variant2,..., --variants variant1,variant2,...
                        restrict actions to the given variants
```
                        
