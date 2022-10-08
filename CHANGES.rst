.. -*- coding: utf-8 -*-

Changelog
=========

2.0.0 (2022-10-08)
------------------

- Mark support for python 3.9. [lovetoburnswhen]

- Replace travis for GitHub. [cclauss]

- Fix CI badge. [sobolevn]

- Make black and isort mandatory. [cclauss]

- Drop python 2.7 and 3.6. [gforcada]

- Overhaul GitHub actions to test on actual supported python versions. [gforcada]

- New flake8 option `--builtins-ignorelist` to specify a list of builtins to ignore. [gsingh93]

1.5.3 (2020-05-14)
------------------

- Change messages to have shorter text


1.5.2 (2020-03-16)
------------------

- Add `DictComp`, `SetComp`, and `GeneratorExpr` support.
  [sobolevn]

1.5.1 (2020-03-16)
------------------

- Adds kwonly and posonly args support.
  [sobolevn]

1.5.0 (2020-03-14)
------------------

- Add ``python3.8`` support.
  [sobolevn]

- Add ``AnnAssign`` support.
  [soboelvn]

- Add ``NamedExpr`` or ``:=`` support.
  [sobolevn]


1.4.2 (2019-12-18)
------------------

- Fix tuple parsing.
  [memery-imb]

1.4.1 (2018-05-11)
------------------

- Fix regression in 1.4.0 and interaction with flake8-bugbear.
  [dirk-thomas]

1.4.0 (2018-05-03)
------------------

- Make code more robust by not assuming that a node is an ``ast.Name``
  but actually checking it.
  [gforcada]

- Handle ``ast.Starred`` as well (i.e. ``a, *int = range(4)``)
  [gforcada]

- Handle lists as well, i.e. ``[a, int] = 3, 4``
  [gforcada]

1.3.1 (2018-04-30)
------------------

- Fix TypeError.
  Fixes https://github.com/gforcada/flake8-builtins/issues/30
  [gforcada]

1.3.0 (2018-04-13)
------------------

- Report different error codes for function (A001) or method definitions (A003).
  Fixes https://github.com/gforcada/flake8-builtins/issues/22#issuecomment-378720168
  [gforcada]

- Ignore underscore variables, django adds it on the list of builtins on its own.
  Fixes https://github.com/gforcada/flake8-builtins/issues/25
  [gforcada]

1.2.3 (2018-04-10)
------------------

- Handle cases where an unpacking happens in a with statement.
  Fixes https://github.com/gforcada/flake8-builtins/issues/26
  [gforcada]

1.2.2 (2018-04-03)
------------------

- Fix error message in function names shadowing a builtin.
  Fixes https://github.com/gforcada/flake8-builtins/issues/22
  [gforcada]


1.2.1 (2018-04-01)
------------------

- re-relase 1.2 from master branch.
  [gforcada]

1.2 (2018-04-01)
----------------
- Fix error message in for loops.
  [gforcada]

- Inspect the following places for possible builtins being shadowed:

  - with open('/tmp/bla.txt') as int
  - except ValueError as int
  - [int for int in range(4)]
  - from zope.component import provide as int
  - import zope.component as int
  - class int(object)
  - def int()
  - async def int()
  - async for int in range(4)
  - async with open('/tmp/bla.txt') as int

  [gforcada]

1.1.1 (2018-03-20)
------------------

- Variables assigned in a for loop can be not only a Tuple, but a Tuple inside a Tuple.
  [dopplershift]

1.1.0 (2018-03-17)
------------------

- Update more trove classifiers.
  [gforcada]

- Inspect variables assigned in a for loop as well.
  Thanks to sobolevn for reporting it!
  [gforcada]

1.0.post0 (2017-12-02)
----------------------

- Update README.
  [DmytroLitvinov]

- Update trove classifiers.
  [dirn]

1.0 (2017-08-19)
----------------

- Use requirements.txt to pin dependencies.
  [gforcada]

- Fix tests with newer flake8 version.
  [gforcada]

- BREAKING CHANGE: error codes have been changed from B00X to A00X to not clash with flake8-bugbear,
  see https://github.com/gforcada/flake8-builtins/issues/7
  [gforcada]

0.4 (2017-05-29)
----------------

- Use a different code for class attributes.
  [karamanolev]

0.3.1.post0 (2017-05-27)
------------------------

- Release universal wheels, not only python 2 wheels.
  [gforcada]

- Update trove classifiers.
  [gforcada]

0.3.1 (2017-05-27)
------------------

- Fix stdin handling.
  [sangiovanni]

0.3 (2017-05-15)
----------------

- Handle stdin, which is the way flake8 gets integrated into editors.
  [gforcada]

- Test against Python 2.7, 3.5, 3.6 and pypy.
  [gforcada]

0.2 (2016-03-30)
----------------
- Whitelist *some* builtins.
  [gforcada]

0.1 (2016-03-04)
----------------
- Initial release
  [gforcada]

- Add buildout and other stuff.
  [gforcada]

- Add actual code.
  [gforcada]

- Drop support for python 3.3, only python 2.7 and python 3.4 are tested.
  [gforcada]
