Excluding builds
================

cmany accepts arguments for excluding certain combinations of build
items. These arguments specify combination exclusion rules which apply either
to a build's name or to the individual build items of which the build is
composed.

When multiple combination arguments are given, they are processed in the
order in which they are given. A build is then included if it successfully 
matches every argument.

Be aware that for added convenience, cmany offers the commands
``show_build_names`` and ``show_builds``, which are useful for testing the
input arguments.


Excluding builds by item name
-----------------------------

To exclude a build based on its composing items, cmany offers the
following arguments, which should be fairly self-explaining:

* systems (``-s/--systems``):
   * ``-xs/--exclude-systems sys1[,sys2[,...]]``
   * ``-is/--include-systems sys1[,sys2[,...]]``
* architectures (``-a/--architectures``):
   * ``-xa/--exclude-architectures arch1[,arch2[,...]]``
   * ``-ia/--include-architectures arch1[,arch2[,...]]``
* compilers (``-c/--compilers``):
   * ``-xc/--exclude-compilers comp1[,comp2[,...]]``
   * ``-ic/--include-compilers comp1[,comp2[,...]]``
* build types (``-t/--build-types``):
   * ``-xt/--exclude-build-types btype1[,btype2[,...]]``
   * ``-it/--include-build-types btype1[,btype2[,...]]``
* variants (``-v/--variants``):
   * ``-xv/--exclude-variants var1[,var2[,...]]``
   * ``-iv/--include-variants var1[,var2[,...]]``

Each argument receives a comma-separated list of item names. These names are
matched literally to the name of any item of the same type, and the
prospective build (which would combine those items) is included or excluding
according to the rule.

Also note the mnemonic for the build item arguments: the letter you use to
specify a build item is the letter after the short form of the include or
exclude flag.


Excluding builds by build name
------------------------------

These are the arguments to prevent a build by matching against the build's
final name:

 * ``-xb/--exclude-builds rule1[,rule2[,...]]``: excludes a build if its
   name matches **any** of the rules
 * ``-ib/--include-builds rule1[,rule2[,...]]``: includes a build only if
   its name matches **any** of the rules
 * ``-xba/--exclude-builds-all rule1[,rule2[,...]]``: excludes a build if
   its name matches **all** of the rules
 * ``-iba/--include-builds-all rule1[,rule2[,...]]``: includes a build only
   if its name matches **all** of the rules

As noted above, each argument accepts a comma-separated list of `Python
regular expressions <https://docs.python.org/3/library/re.html>`_ that will
be used as matching rules to each build name. A build is included only if its
name successfully matches every combination argument. Note that the form of a
build's name is
``{system}-{architecture}-{compiler}-{build_type}[-{variant}]``. Note also
the presence of the hyphen separating the build items; it can be used to
distinguish between similarly named items such as ``x86`` and ``x86_64``.

The rules do not need to be regular expressions: passing the full names of
the builds to the argument works as expected.


Examples
--------

As a first example, consider this command which addresses 12 builds by combining 2
architectures, 2 build types and 3 variants::

  $ cmany show_build_names -a x86,x86_64 -t Debug,Release \
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

  $ cmany show_build_names -a x86,x86_64 -t Debug,Release \
                           -v none,'foo: -D FOO','bar: -D BAR' \
                           --exclude-builds '.*x86-.*foo'
  linux-x86-g++5.4-Debug
  linux-x86-g++5.4-Debug-bar     # NOTE: no x86 foo variant
  linux-x86-g++5.4-Release
  linux-x86-g++5.4-Release-bar   # NOTE: no x86 foo variant
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

For the previous example, it is actually easier to have the ``foo`` variant
directly exclude the ``x86`` architecture. The result is exactly the same::

  $ cmany show_builds -a x86,x86_64 -t Debug,Release \
                      -v none,'foo: -D FOO -xa x86','bar: -D BAR'

You could instead have the ``x86`` architecture exclude the ``foo`` variant,
with the same result::

  $ cmany show_builds -a 'x86: -xv foo',x86_64 -t Debug,Release \
                      -v none,'foo: -D FOO','bar: -D BAR' \

The logical opposite of ``--exclude-builds`` is naturally
``--include-builds``::

  $ cmany show_builds -a x86,x86_64 -t Debug,Release \
                      -v none,'foo: -D FOO','bar: -D BAR' \
                      --include-builds '.*x86-.*foo'
  linux-x86-g++5.4-Debug-foo
  linux-x86-g++5.4-Release-foo

This can also be done with the following command::

  $ cmany show_builds -a x86,x86_64 -t Debug,Release \
                     -v none,'foo: -D FOO','bar: -D BAR' \
                     -ia x86 -iv foo

If you are wondering about the usefulness of the ``-i*/--include`` arguments,
consider that the compile-edit loop is usually repeated many times. Being
that the arguments to cmany usually come to a certain degree of complexity
(something which :doc:`Project mode </project_mode>` also addresses),
rewriting them every time is something we would like to avoid. So when you
want to narrow down your previous command (or your project setup) just to a
certain combination of builds, the ``--include-*`` arguments usually come in
very handy.

Like all the arguments above, item combination arguments can be used both at
the cmany command level or at each build item level.

You may have noticed that it does not make much sense to provide the
``--include-*`` arguments in a build item specification, as combination is
implied for every build item. However, being able to use these at the scope
of the command is certainly useful, either as a form of saving extensive
editing when reusing complicated cmany commands (for example in shell
sessions), or with :doc:`Project mode </project_mode>`.
