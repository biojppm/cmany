Reusing arguments
=================

In certain scenarios, the arguments to a ``cmany`` command can get a bit
complicated. To aid in such scenarios, ``cmany`` offers two ways of storing
these arguments, so that they are implicitly used in simple
commands such as ``cmany build``.


Session arguments
-----------------

You can store arguments in the environment variable ``CMANY_ARGS``. Then the
resulting cmany command is taken as if it were given ``cmany <subcommand>
$CMANY_ARGS`` (or ``cmany <subcommand> %CMANY_ARGS%`` in DOS). In the example
below, the configure, build and install commands will all use the five given
compilers and two build types, resulting in 10 build trees:

.. code:: bash

    export CMANY_ARGS="-c clang++-3.9,clang++-3.8,g++-6,g++-7,icpc -t Debug,Release"
    cmany c
    cmany b
    cmany i

The arguments stored in ``CMANY_ARGS`` can be combined with any other
argument. For example, if you now want to build only the ``Debug`` types of
the current value of ``CMANY_ARGS``, just use the ``--include-types/--it``
:doc:`inclusion flag </excluding_builds>`:

.. code:: bash

    cmany b -it Debug

or as another example, you can process only a single build tree via the
``--include-builds/-ib``, say, ``g++-6`` with ``Release``:

.. code:: bash

    cmany b -ib '.*6.*Debug'

Some arguments to cmany are meant to be used before the cmany subcommand. For
those arguments, you should use the ``CMANY_PFX_ARGS`` environment variable
instead of ``CMANY_ARGS``. That is, cmany will see commands given to it as
``cmany $CMANY_PFX_ARGS <subcommand> $CMANY_ARGS``.

.. note::
   The value of ``CMANY_ARGS`` and ``CMANY_PFX_ARGS`` is always used in every
   ``cmany`` invokation. To prevent their use, you will have to unset the
   environment variables.


Project file
------------

``cmany`` also allows you to permanently store its arguments in the
``cmany.yml`` which should be placed alongside the project
``CMakeLists.txt``. This feature is under current development and should be
used with care.

