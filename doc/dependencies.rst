Project dependencies
====================

Certain projects need to integrate their dependencies fully into their build
system, maybe because they are cross-platform or maybe because certain
compiler flags and macros need to be used not just in the project's own
source code, but also in the source code of the project's dependencies. Or
maybe because it's just more practical to use `CMake's external project
facilities <https://cmake.org/cmake/help/v3.4/module/ExternalProject.html>`_
(which can serve as a sort-of dependency manager, as illustrated by projects
such as `Hunter <https://github.com/ruslo/hunter>`_) to get the dependencies'
source code and compile them.

cmany offers the argument ``--deps path/to/extern/CMakeLists.txt`` to enable
building another CMake project which builds and installs the dependencies of
the current project. When ``--deps`` is given, the external project is built
for each configuration, and installed in the configuration's build
directory. Use ``--deps-prefix`` to specify a different install directory for
the external project.

(To be continued)
