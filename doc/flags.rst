Flags
=====

cmany allows you to transparently pass flags to all or some of the builds.
These flags can be compiler flags, preprocessor defines or CMake cache
variables. Specifying flags is an important cmany usage pattern, which is
used also when specifying :doc:`variants` or :ref:`Per-parameter flags`.

.. note::
   The examples below apply the flags across the board to all the
   individual builds produced with the cmany command. For example, this will
   add ``-Wall`` to all of the 9 resulting builds::

     $ cmany b --compilers clang++,g++,icpc \
               --build-types Debug,Release,MinSizeRel \
               --cxxflags "-Wall"

   If you want to add flags only to certain builds, it's cool! One of the
   main motivations of cmany is being able to easily do that, and it offers
   two different solutions. You can :doc:`use variants </variants>`. You can
   also set flags per :ref:`Per-parameter flags`, so that when one specific
   build item (such as a compiler or operating system) is used, then the
   flags are also used in the resulting build.

CMake cache variables
---------------------

To set cmake cache variables use ``--vars/-V``. For example::

    $ cmany b -V CMAKE_VERBOSE_MAKEFILES=1,PROJECT_FOO=BAR

This is equivalent to the following sequence of commands::

    $ cmake -D CMAKE_VERBOSE_MAKEFILES=1 -D PROJECT_FOO=BAR ../..
    $ cmake --build .

Note the use of the comma to separate the variables. This is for consistency
with the rest of the cmany options, namely (for example) those selecting
compilers or build types. You can also use separate invocations::

    $ cmany b -V CMAKE_VERBOSE_MAKEFILES=1 -V PROJECT_FOO=BAR

which will have the same result as above.

Preprocessor macros
-------------------

To add preprocessor macros, use the option ``--defines/-D``::

    $ cmany b -D MY_MACRO=1,FOO=BAR

The command above has the same meaning of::

    $ cmake -D CMAKE_CXX_FLAGS="-D MYMACRO=1 -D FOO=BAR" ../..
    $ cmake --build .

Note also that ``--defines`` can be chained, with the same result::

    $ cmany b -D MY_MACRO=1 -D FOO=BAR


C++ compiler flags
------------------

To add C++ compiler flags to a cmany build, use the option
``--cxxflags/-X``. To prevent these flags being interpreted as cmany
command options, use quotes or single quotes::

    $ cmany b -X "-Wall","-O3"      # add -Wall -O3 to all builds

The command above has the same meaning of::

    $ cmake -D CMAKE_CXX_FLAGS="-Wall -O3" ../..
    $ cmake --build .

Note that ``--cxxflags/-X`` can be chained, with the same result::

    $ cmany b -X "-Wall" -X "-O3"

C compiler flags
----------------

To add C compiler flags, use the option ``--cflags/-C``. As with C++
flags, use quotes to escape::

    $ cmany b -C "-Wall","-O3"

The command above has the same meaning of::

    $ cmake -D CMAKE_C_FLAGS="-Wall -O3" ../..
    $ cmake --build .

Note that ``--cflags/-C`` can be chained, with the same result::

    $ cmany b -C "-Wall" -C "-O3"

Linker flags
------------

For now, cmany has no explicit support for linker flags. But you can set
linker flags through the cmake cache variable mechanism::

    $ cmany b -V '-DCMAKE_LINKER_FLAGS="....linker flags...."'

You may also have noticed that CMake cache variables will allow you to
specify macros and compiler flags as well via ``-DCMAKE_CXX_FLAGS=...``. Yes,
that's right, you can also do that. But not only is it less verbose when
passing macros and flags through ``--defines/--cflags/--cxxflags``: there is
a strong reason to prefer it this way: **flag aliases**, introduced below.


Flag aliases
------------

For simplicity of use, cmany comes with a predefined set of flag aliases
which you can use. A flag alias is a name which maps to specific flags for
each compiler. For example, if you want to enable maximum warnings there is
the ``wall`` alias (shown here in the sort-of-yml markup which cmany uses to
define it)::

    wall:
        desc: turn on all warnings
        gcc,clang,icc: -Wall
        vs: /Wall

or the ``avx`` alias if you want to enable AVX SIMD processing::

    avx:
        desc: enable AVX instructions
        gcc,clang,icc: -mavx
        vs: /arch:avx

This allows you to use the aliases instead of the flags directly, thus
insulating you from differences between compilers. For example, the following
command will translate to ``g++ -mavx -Wall`` with gcc, clang or icc, but
with Visual Studio it will translate instead to ``cl.exe /Wall /arch:avx``::

    $ cmany b --cxxflags avx,wall

Note that flag aliases are translated only when they are given through
``--cxxflags/-cflags``. Do not use aliases with ``--vars
CMAKE_CXX_FLAGS=...``, as cmany will not translate them there.

Built-in aliases
----------------

cmany provides built-in flag aliases to simplify working with different
compilers at the same time. Currently, you can see them in the file
``src/c4/cmany/flags.yml`` (see the `current version at github
<https://github.com/biojppm/cmany/blob/master/src/c4/cmany/flags.yml>`_).

Defining more flag aliases
--------------------------

Being able to define your own is in the roadmap. For now, you can submit PRs
for adding aliases.


