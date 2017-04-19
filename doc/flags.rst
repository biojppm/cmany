Flags
=====

cmany allows you to transparently pass flags to all or some of the builds.
These flags can be compiler flags, preprocessor defines or CMake cache
variables. Specifying flags is an important cmany usage pattern, which is
used also when specifying :doc:`variants` or :ref:`Per-item flags`.

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
   also set flags per :ref:`Per-item flags`, so that when one specific
   build item (such as a compiler or operating system) is used, then the
   flags are also used in the resulting build.


CMake cache variables
---------------------

To set cmake cache variables use ``--cmake-vars/-V``. For example::

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

Note also that ``--defines/-D`` can be chained, with the same result::

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
the ``wall`` alias (shown here in the yml markup which cmany uses to define
it)::

    wall:
        desc: turn on all warnings
        gcc,clang,icc: -Wall
        vs: /Wall

or eg the ``avx`` alias if you want to enable AVX SIMD processing::

    avx:
        desc: enable AVX instructions
        gcc,clang,icc: -mavx
        vs: /arch:avx

This allows use of the aliases instead of the flags directly, thus
insulating you from differences between compilers. For example, the following
command will translate to ``g++ -mavx -Wall`` with gcc, clang or icc, but
with Visual Studio it will translate instead to ``cl.exe /Wall /arch:avx``::

    $ cmany b --cxxflags avx,wall

Note that flag aliases are translated only when they are given through
``--cxxflags/-cflags``. Do not use aliases with ``--cmake-vars
CMAKE_CXX_FLAGS=...``, as cmany will not translate them there.

Built-in flag aliases
^^^^^^^^^^^^^^^^^^^^^

cmany provides some built-in flag aliases to simplify working with different
compilers at the same time. Currently, you can see them in the file
``conf/cmany.yml`` (see the `current version at github
<https://github.com/biojppm/cmany/blob/master/conf/cmany.yml>`_).

Defining more flag aliases
^^^^^^^^^^^^^^^^^^^^^^^^^^

Being able to define your own flag aliases is in the roadmap. For now, you
can submit PRs for adding aliases.


Excluding item combinations
---------------------------

cmany accepts arguments for excluding certain combinations of build
items. These arguments specify rules which apply either to a build's name or
to the items the build is composed of.

Like all the arguments above, item combination arguments can be used both at
the cmany command level or at each build item level.

When multiple combination arguments are given, they are processed in the
order in which they are given. A build is then included if it successfully 
matches every argument.


Excluding builds by item name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To exclude a build based on the items it is composed of, cmany offers the
following arguments:

 * systems:
   * ``-xs/--exclude-systems sys1[,sys2[,...]]``
   * ``-is/--include-systems sys1[,sys2[,...]]``
 * architectures
   * ``-xa/--exclude-architectures arch1[,arch2[,...]]``
   * ``-ia/--include-architectures arch1[,arch2[,...]]``
 * compilers
   * ``-xc/--exclude-compilers comp1[,comp2[,...]]``
   * ``-ic/--include-compilers comp1[,comp2[,...]]``
 * build types
   * ``-xt/--exclude-build-types btype1[,btype2[,...]]``
   * ``-it/--include-build-types btype1[,btype2[,...]]``
 * variants
   * ``-xv/--exclude-variants var1[,var2[,...]]``
   * ``-iv/--include-variants var1[,var2[,...]]``

The names of the arguments should be self-explaining. Each argument receives
a comma-separated list of item names. These names are matched literally to
any prospective item of the same type.


Excluding builds by build name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These are the arguments to prevent a build by name:

 * ``-xb / --exclude-builds rule1[,rule2[,...]]``: excludes a build if its
   name matches **any** of the rules
 * ``-ib / --include-builds rule1[,rule2[,...]]``: includes a build only if
   *its name matches **any** of the rules
 * ``-xba / --exclude-builds-all rule1[,rule2[,...]]``: excludes a build if
   its name matches **all** of the rules
 * ``-iba / --include-builds-all rule1[,rule2[,...]]``: includes a build only
   *if its name matches **all** of the rules

As noted above, each argument accepts a comma-separated list of `Python
regular expressions <https://docs.python.org/3/library/re.html>`_ that will
serve as matching rules to each build name. A build is included only if its
name successfully matches every combination argument. Note that the form of
the name is
``{system}-{architecture}-{compiler}-{build_type}[-{variant}]``. Note also
the hyphen separating the build items; it can be used to distinguish between
similarly named items such as ``x86`` and ``x86_64``.


Examples
^^^^^^^^

As a first example, consider this command which shows 12 builds by combining 2
architectures, 2 build types and 3 variants::

  $ cmany show_builds -a x86,x86_64 -t Debug,Release \
                      -v none,'foo: -D FOO','bar: -D BAR'
  linux-x86-g++5.4-Debug
  linux-x86-g++5.4-Debug-foo
  linux-x86-g++5.4-Debug-bar
  linux-x86-g++5.4-Release
  linux-x86-g++5.4-Release-foo
  linux-x86-g++5.4-Release-bar
  linux-x86_64-g++5.4-Debug
  linux-x86_64-g++5.4-Debug-foo
  linux-x86_64-g++5.4-Debug-bar
  linux-x86_64-g++5.4-Release
  linux-x86_64-g++5.4-Release-foo
  linux-x86_64-g++5.4-Release-bar

Now, if we want to exclude ``foo`` variants of the ``x86`` architecture, we
can use::

  $ cmany show_builds -a x86,x86_64 -t Debug,Release \
                      -v none,'foo: -D FOO','bar: -D BAR' \
                      --exclude-builds '.*x86-.*foo'
  linux-x86-g++5.4-Debug
  linux-x86-g++5.4-Debug-bar     # NOTE: no foo variant above
  linux-x86-g++5.4-Release
  linux-x86-g++5.4-Release-bar   # NOTE: no foo variant above
  linux-x86_64-g++5.4-Debug
  linux-x86_64-g++5.4-Debug-foo
  linux-x86_64-g++5.4-Debug-bar
  linux-x86_64-g++5.4-Release
  linux-x86_64-g++5.4-Release-foo
  linux-x86_64-g++5.4-Release-bar

Note the hyphen appearing in the regular expression passed to
``--exclude-builds '.*x86-.*foo'``. This prevents it from matching
``x86_64``. As noted above, the name of the build is obtained by separating
the build items of which it is composed with an hyphen. If this regular
expression did not have the hyphen and was instead ``.*x86.*foo``, then it
would match both ``x86`` and ``x86_64``, with the result that no builds would
contain the ``foo`` variant.

The logical opposite of ``--exclude-builds`` is naturally ``-include-builds``::

  $ cmany show_builds -a x86,x86_64 -v none,'foo: -D FOO','bar: -D BAR' \
                      --include-builds '.*x86-.*foo'
  linux-x86-g++5.4-Debug-foo
  linux-x86-g++5.4-Release-foo

