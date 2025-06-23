|Stars| |GitHub release| |License: MIT|

[English \| `中文 <README_zh.md>`__]

This repository implements a complete toolchain for compressing,
packing, obfuscating and unpacking pyc files based on Python’s
underlying bytecode.

0. Installation and Dependencies
--------------------------------

Open the terminal and enter the command:

::

   pip install pyc-zipper

| This will install ``pyc-zipper``.
| Additionally, this tool depends on the
  `pyobject <https://github.com/ekcbw/pyobject>`__ library, particularly
  the ``Code`` class in the
  `pyobject.code <https://github.com/ekcbw/pyobject/blob/main/pyobject/code.py>`__
  submodule. The ``Code`` class is a mutable bytecode wrapper that spans
  multiple Python versions (currently supporting 3.4 to 3.14) and even
  other implementations including PyPy.
| When installing ``pyc-zipper``, the ``pyobject`` library will be
  automatically installed, so manual installation is not required.

1. Usage and Command Line
-------------------------

::

   pyc-zipper [options] [file1 file2 ...]

The available options are:

::

   pyc-zipper [-h] [--obfuscate] [--obfuscate-global]
                   [--obfuscate-lineno] [--obfuscate-filename]
                   [--obfuscate-code-name] [--obfuscate-bytecode]
                   [--obfuscate-argname] [--unpack] [--version]
                   [--compress-module COMPRESS_MODULE] [--no-obfuscation]
                   file1 [file2 ...]

| **Compression, Obfuscation, and Packing** - ``file1, file2``: File
  names, which can be ``.py`` files or ``.pyc`` files. If a ``.py`` file
  is provided, a processed ``.pyc`` will be automatically generated.
| - ``compress-module``: The module used to compress ``.pyc`` files,
  such as ``bz2``, ``lzma``, ``zlib``, ``brotli``, etc., but the module
  must have ``compress`` and ``decompress`` functions. If not provided,
  the ``.pyc`` file will not be compressed.
| - ``obfuscate``: Obfuscate the ``.pyc`` file using default options,
  enabling all options except for parameter name obfuscation.
| - ``obfuscate-global``: Obfuscate global variable names, as well as
  class names, function names, etc.
| - ``obfuscate-lineno``: Obfuscate line number information, preventing
  decompilers from knowing the line numbers through Traceback.
| - ``obfuscate-filename``: Obfuscate the original ``.py`` source file
  name corresponding to the bytecode, removing privacy information such
  as the username from paths like
  ``C:\Users\<username>\...\Python313\Lib\original_source.py``.
| - ``obfuscate-code-name``: Obfuscate the internal names (function
  names, class names) of the bytecode.
| - ``obfuscate-bytecode``: Obfuscate the bytecode instructions.
| - ``obfuscate-argname``: Obfuscate function parameter names. (TODO:
  currently the source code cannot use keyword arguments to call
  obfuscated functions.) - ``no-obfuscation``: Disable obfuscation. (If
  obfuscation is not explicitly disabled, obfuscating local variable
  names is enabled by default.)

**Decompression and Unpacking** - ``unpack``: Decompress previously
compressed ``.pyc`` files. ``pyc-zipper`` will automatically detect the
module name, which can also be manually provided through the
``compress-module`` parameter. Note that the ``unpack`` switch can only
be used with ``compress-module`` and cannot be combined with other
switches.

Additionally, if the terminal prompts that the ``pyc-zipper`` command
cannot be found, you can use ``python -m pyc_zipper`` as an alternative.

For PyInstaller
^^^^^^^^^^^^^^^

| ``pyc-zipper`` has built-in functionality to integrate with the
  PyInstaller packaging tool. After calling ``pyinstaller file.py``, a
  file named ``file.spec`` will be generated.
| ``file.spec`` is generally a Python file, and you only need to add the
  following at the beginning of ``file.spec``:

.. code:: python

   from pyc_zipper import hook_pyinstaller
   hook_pyinstaller()

Alternatively, you can customize your own parameters, such as:

.. code:: python

   hook_pyinstaller(comp_module="lzma", no_obfuscation=False,
                    obfuscate_global=True, obfuscate_lineno=True,
                    obfuscate_filename=True, obfuscate_code_name=True,
                    obfuscate_bytecode=True, obfuscate_argname=False)

| ``comp_module`` is a string representing the name of the compression
  module, defaulting to ``None``. Aside from that, the usage of other
  parameters is consistent with the command line options of
  ``pyc-zipper``.
| Finally, run:

::

   pyinstaller file.spec

| Note that you cannot use ``pyinstaller file.py`` again, as it will
  generate a new spec file that will overwrite ``file.spec``.
| If you see output information from ``pyc-zipper`` while running
  PyInstaller, such as:

::

   3926 INFO: checking PKG
   3927 INFO: Building PKG because PKG-00.toc is non existent
   3927 INFO: Building PKG (CArchive) PKG-00.pkg
   pyc-zipper: processing ('pyiboot01_bootstrap', 'D:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python37-32\\lib\\site-packages\\PyInstaller\\loader\\pyiboot01_bootstrap.py') in _load_code
   Obfuscating code '<module>'
   Obfuscating code 'NullWriter'
   Obfuscating code 'write'
   Obfuscating code 'flush'
   Obfuscating code 'isatty'
   Obfuscating code '_frozen_name'
   Obfuscating code 'PyInstallerImportError'
   Obfuscating code '__init__'
   ...

Then the obfuscation is successful.

2. Compression Packing
----------------------

`pyc_zipper/compress.py <https://github.com/ekcbw/pyc-zipper/blob/main/pyc_zipper/compress.py>`__
is responsible for adding a compression pack to ``.pyc`` files. The
packed ``.pyc`` files will call Python’s built-in ``bz2``, ``lzma``, or
``zlib`` modules to decompress the bytecode during execution.

Self-Extracting Program
^^^^^^^^^^^^^^^^^^^^^^^

In the packed ``.pyc`` file, there is a “compression pack” that first
decompresses and restores the original bytecode before execution.

For example, using ``zlib``, the self-extraction program is as follows:

.. code:: py

   import zlib, marshal
   exec(marshal.loads(zlib.decompress(b'x\xda...'))) # b'x\xda...' is the compressed bytecode data

For ``bz2`` and ``lzma``:

.. code:: py

   import bz2, marshal
   exec(marshal.loads(bz2.decompress(b'BZh9...')))

.. code:: py

   import lzma, marshal
   exec(marshal.loads(lzma.decompress(b'\xfd7zXZ...')))

Compression Efficiency Comparison
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

My tests have shown that the ``.pyc`` file compressed with ``lzma``
results in the smallest size, followed by ``bz2``, with ``zlib``
performing the least efficiently.

Compatibility
^^^^^^^^^^^^^

These compression tools are compatible with all versions of Python 3, as
they do not rely on specific bytecode versions.

3. Obfuscation and Anti-Decompilation Packing
---------------------------------------------

The previous compression tools cannot prevent ``.pyc`` files from being
decompiled by libraries like ``uncompyle6``. To prevent decompilation,
an obfuscation tool in
`pyc_zipper/obfuscate.py <https://github.com/ekcbw/pyc-zipper/blob/main/pyc_zipper/obfuscate.py>`__
is used to obfuscate the bytecode instructions and variable names.

A Brief Introduction to the Obfuscation Principles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Obfuscating Code Metadata and Anti-Debugging
'''''''''''''''''''''''''''''''''''''''''''''''

.. code:: python

   if obfuscate_lineno:
       co.co_lnotab = b''
       co.co_firstlineno = 1
   if obfuscate_filename: co.co_filename = ''
   if obfuscate_code_name: co.co_name = ''

-  Set ``co_lnotab`` to an empty byte string to clear the line number
   mapping table. (For Python 3.10+, the ``pyobject`` library
   automatically converts ``co_lnotab`` to ``co_linetable``, so
   compatibility is not an issue.)
-  Set ``co_firstlineno`` to 1, as line numbers are calculated by adding
   ``co_firstlineno`` and the results from ``co_lnotab``.
-  Set ``co_filename`` to an empty string to hide the file path of the
   code source.
-  Set ``co_name`` to an empty string to hide the name of the code
   object (e.g., function name).

This completely hides the filename, line number, and function name
information in Traceback error outputs, increasing the difficulty of
reverse engineering.

2. Obfuscating Binary Bytecode
''''''''''''''''''''''''''''''

.. code:: python

   if obfuscate_bytecode and co.co_code[-len(RET_INSTRUCTION)*2:] != RET_INSTRUCTION*2:
       co.co_code += RET_INSTRUCTION

-  Check if the binary bytecode (``co_code``) already contains two
   consecutive return instructions (``RET_INSTRUCTION``) at the end. If
   not, append a redundant return instruction to disrupt the parsing of
   decompilation tools.

3. Obfuscating Local Variable Names
'''''''''''''''''''''''''''''''''''

| Local variable names in Python bytecode are stored in the
  ``co_varnames``, ``co_cellvars``, and ``co_freevars`` attributes.
| - ``co_varnames`` contains local variable names used only within the
  function. - ``co_cellvars`` contains variable names exported to inner
  closure functions. - ``co_freevars`` contains variable names
  referenced from outer closure functions.

For example:

.. code:: python

   def f():
       x, y = 1, 2; z = 3
       def g():
           print(x, y)
       g()

-  ``f.__code__.co_cellvars`` will include the exported variable names
   ``("x", "y")`` but not ``"z"``, which is only used within ``f``.
-  ``f.__code__.co_varnames`` will include the variable name ``("z",)``.
-  ``g.__code__.co_freevars`` will include the imported variable names
   ``("x", "y")``.

The code replaces local variable names with sequential numbers in the
following order: 1. Free variables inherited from the outer scope,
stored in the ``closure_vars`` dictionary. 2. Newly defined
``co_cellvars`` within the function. 3. Ordinary variables defined in
``co_varnames``.

Additionally, since obfuscating parameter names can prevent proper
keyword argument passing, this feature is optional.

4. Obfuscating Global Variable Names
''''''''''''''''''''''''''''''''''''

| Unlike local variables, global variable names are stored in the
  ``co_names`` attribute of the bytecode.
| The ``co_names`` attribute also includes other names, such as
  attribute names, imported module names, and built-in function names,
  which should not be obfuscated.

The code: - Uses the ``dis.get_instructions`` function to retrieve all
bytecode instructions. - Identifies the operands of ``STORE_NAME``
instructions (global variable names). - Analyzes operands of
instructions like ``IMPORT_NAME``, ``IMPORT_FROM``, and ``LOAD_ATTR``
that also reference ``co_names`` to avoid obfuscating them and causing
naming conflicts. - Ensures that names imported via
``from ... import *`` (handled by the ``IMPORT_STAR`` instruction) are
not obfuscated, as they introduce many names.

5. Recursively Processing Nested Bytecode
'''''''''''''''''''''''''''''''''''''''''

| Constants used in Python bytecode are stored in the ``co_consts``
  attribute. If the code defines functions or classes, their bytecode is
  also stored in ``co_consts``.
| For example, the bytecode returned by
  ``compile("def f(): pass", "", "exec")`` has ``co_consts`` as
  ``(<code object f at 0x..., file "", line 1>, 'f', None)``, which
  includes the bytecode of the function ``f()``.

The code: - Iterates through ``co_consts`` to find nested bytecode
objects (e.g., nested functions, classes). - Recursively calls
``process_code`` on the nested bytecode objects.

6. Effectiveness on Formatted Strings (f-strings)
'''''''''''''''''''''''''''''''''''''''''''''''''

Python’s formatted strings are compiled into bytecode without storing
variable names as a whole. Instead, they are split into multiple
substrings, like this:

.. code:: python

   >>> from dis import dis
   >>> dis("f'start{x!r}end'")
     0           RESUME                   0

     1           LOAD_CONST               0 ('start')
                 LOAD_NAME                0 (x)
                 CONVERT_VALUE            2 (repr)
                 FORMAT_SIMPLE
                 LOAD_CONST               1 ('end')
                 BUILD_STRING             3
                 RETURN_VALUE

Since the variable name ``x`` is stored as the operand of the
``LOAD_NAME`` instruction in the ``co_names`` array, it can still be
obfuscated.

Example of Obfuscation Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| Here is an example of bytecode obtained by decompiling an obfuscated
  ``.pyc`` file using the ``uncompyle6`` library (``obfuscate_bytecode``
  was set to ``False`` for easier observation of the decompiled results,
  and parameter name obfuscation ``obfuscate_argname`` was enabled).
| Since the ``co_name`` information was removed, class and function
  names cannot be decompiled. However, the obfuscated code still runs
  because the classes and functions are stored in local and global
  variables:

.. code:: python

   -- Stacks of completed symbols:
   START ::= |- stmts . 
   and ::= expr . JUMP_IF_FALSE_OR_POP expr \e_come_from_opt
   and ::= expr . JUMP_IF_FALSE_OR_POP expr come_from_opt
   and ::= expr . jifop_come_from expr
   and ::= expr . jmp_false expr
   and ::= expr . jmp_false expr COME_FROM
   and ::= expr . jmp_false expr jmp_false
   ...
   Instruction context:
                     60  STORE_FAST               'l3'
                     62  LOAD_GLOBAL              g18
                     64  LOAD_FAST                'l3'
                     66  CALL_FUNCTION_1       1  '1 positional argument'
                     68  RETURN_VALUE     

   import functools
   try:
       from timer_tool import timer
   except ImportError:
       def (func):
           return func

   g4 = False

   def (l0, l1, l2=[], l3=False):
       for l4 in dir(l0):
           if (l3 or l4.startswith)("_"):
               pass
           elif l4 in l2:
               pass
           else:
               l1[l4] = getattr(l0, l4)

   g9 = {}
   for g13 in range(len(g8.priority)):
       for g14 in g8.priority[g13]:
           g9[g14] = g13

   g5(g8, globals(), ["priority"])

   def (l0, l1):
       l2 = g9[l1]
       l3 = g9[getattr(l0, "_DynObj__last_symbol", HIGHEST)]
       l4 = "({!r})" if l2 > l3 else "{!r}"
       return l4.format(l0)

   class :
       _cache = {}
       if g4:
           def (l0, l1, l2=HIGHEST):
               if l1 in l0._cache:
                   return l0._cache[l1]
               l3 = super().__new__(l0)
               l0._cache[l1] = l3
               return l3

       def (l0, l1, l2=HIGHEST):
           l0._DynObj__code = l1
           l0._DynObj__last_symbol = l2

       def Parse error at or near `LOAD_FAST' instruction at offset 16

       def (l0, l1):
           l2 = "{}.{}".format(l0, l1)
           return g18(l2)

       def (l0, l1):
           return g18(f"{g16(l0, ADD)} + {g16(l1, ADD)}", ADD)

   ...
   # Deparsing stopped due to parse error

.. _compatibility-1:

Compatibility
^^^^^^^^^^^^^

This obfuscation tool is also compatible with all versions of Python 3,
as it does not depend on specific bytecode versions.

4. Unpacking Tool
-----------------

| The unpacking tool in
  `pyc_zipper/unpack.py <https://github.com/ekcbw/pyc-zipper/blob/main/pyc_zipper/unpack.py>`__
  supports unpacking ``.pyc`` files that have been packed using the
  aforementioned compression tools. It restores the original ``.pyc``
  file before compression.
| However, the unpacking tool cannot restore the instructions and
  variable names that have been obfuscated by the obfuscation tool.

.. |Stars| image:: https://img.shields.io/github/stars/ekcbw/pyc-zipper
   :target: https://img.shields.io/github/stars/ekcbw/pyc-zipper
.. |GitHub release| image:: https://img.shields.io/github/v/release/ekcbw/pyc-zipper
   :target: https://github.com/ekcbw/pyc-zipper/releases/latest
.. |License: MIT| image:: https://img.shields.io/github/license/ekcbw/pyc-zipper
   :target: https://github.com/ekcbw/pyc-zipper/blob/main/LICENSE
