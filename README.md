**The English introduction is placed below the Chinese version.**

本仓库基于Python的底层字节码，实现了一套完整的pyc文件的压缩、加壳和脱壳工具链。
## 0.依赖的库
这些加壳和脱壳的工具依赖于`pyobject`库，尤其是`pyobject.code_`这个子模块中的`Code`类。`Code`类是跨多个Python版本的(目前支持3.4到3.14)。  
`pyobject`库可在[GitHub](https://github.com/ekcbw/pyobject)找到，或通过`pip install pyobject`命令安装。  

## 1.命令行
```
python pyc_zipper_xxx.py <待处理的.pyc文件1> <.pyc文件2> ...
```
## 2.压缩壳
`pyc_zipper_bz2.py`，`pyc_zipper_lzma.py`和`pyc_zipper_zlib.py`是为.pyc文件添加压缩壳的工具，加壳后的.pyc文件在运行时，会调用Python内置的`bz2`，`lzma`或`zlib`模块对压缩前的字节码进行自解压缩，再执行解压后的字节码。
此外，压缩工具还会删除`co_lnotab`这一无用的附加信息，以及`co_filename`这一包含源`.py`文件路径的隐私信息，以进一步缩小体积。
#### 自解压程序
加壳后的`.pyc`文件中存在一个"压缩壳"，首先解压缩、还原出原先的字节码，再执行。
以`zlib`为例，自解压缩程序如下：
```py
import zlib, marshal
exec(marshal.loads(zlib.decompress(b'x\xda...'))) # b'x\xda...'为压缩后的字节码数据
```
对于`bz2`和`lzma`：
```py
import bz2, marshal
exec(marshal.loads(bz2.decompress(b'BZh9...')))
```
```py
import lzma, marshal
exec(marshal.loads(lzma.decompress(b'\xfd7zXZ...')))
```
#### 压缩效率的对比
经测试，一般同一`.pyc`文件使用`lzma`加壳后的体积最小，`bz2`次之，`zlib`效果最差。
#### 兼容性
这些压缩工具兼容所有Python 3版本，由于不依赖特定版本的字节码。
## 3.混淆和防反编译壳
前面的压缩工具并不能防止`.pyc`文件被`uncompyle6`等库反编译。要防止反编译，还需要用到混淆工具`pyc_zipper_obfuscate.py`，混淆字节码的指令，并混淆变量名。

#### `process_code` 函数的简明混淆原理

##### 1. 混淆代码元数据，反调试
```python
if obfuscate_lineno:
    co.co_lnotab = b''
    co.co_firstlineno = 1
if obfuscate_filename: co.co_filename = ''
if obfuscate_code_name: co.co_name = ''
```
  - 将 `co_lnotab` 设置为空字节串，清空行号映射表。（对于3.10+的版本，`pyobject`库会自动将`co_lnotab`转换为`co_linetable`，无需考虑兼容性）
  - 将 `co_firstlineno` 设置为 1，由于行号计算是`co_firstlineno`和`co_lnotab`的计算结果相加的。
  - 将 `co_filename` 设置为空字符串，隐藏代码来源的文件路径。
  - 将 `co_name` 设置为空字符串，隐藏代码对象的名称（如函数名）。

这会完全隐藏Traceback错误输出中的文件名、行号，乃至函数名信息，加大破解难度。  

##### 2. 混淆二进制字节码
```python
if obfuscate_bytecode and co.co_code[-len(RET_INSTRUCTION)*2:] != RET_INSTRUCTION*2:
    co.co_code += RET_INSTRUCTION
```
- 检查二进制字节码(`co_code`)的尾部是否已经包含两个连续的返回指令（`RET_INSTRUCTION`），如果没有，则追加一个无用的返回指令，目的是干扰反编译工具的解析。

##### 3. 混淆局部变量名
Python字节码的局部变量名存储在`co_varnames`和`co_cellvars`, `co_freevars`属性中。  
`co_varnames`是仅在函数内使用的局部变量名，而`co_cellvars`是会导出到更内部的闭包函数的变量名，`co_freevars`是引用的外层闭包函数的变量名。  
例如：
```python
def f():
    x,y=1,2;z=3
    def g():
        print(x,y)
    g()
```
`f.__code__.co_cellvars`最终会包含导出的变量名`("x","y")`，不会包含只有函数`f`用到的`"z"`，`f`的`co_varnames`会包含变量名`("z",)`。  
而`g.__code__.co_freevars`会包含导入的变量名`("x","y")`。  

代码依次将局部变量名替换成序号，序号从小到大依次是：
- 从上层继承的自由变量，在`closure_vars`字典中。
- 函数内部新定义的`co_cellvars`。
- 函数定义的普通变量`co_varnames`。

此外，由于混淆参数名称会导致无法正确传递关键字参数，混淆参数名的功能是可选的。  

##### 4. 混淆全局变量名

和局部变量不同，全局变量名存储在字节码的`co_names`属性。  
当然`co_names`属性还有一些其他名称，如属性名、导入模块名、内置函数名称等，不能被混淆。  

代码首先通过`dis.get_instructions`函数获取字节码所有的指令，找出所有`STORE_NAME`指令的操作数（全局变量名）。  
再分析`IMPORT_NAME`,`IMPORT_FROM`,`LOAD_ATTR`等同样会引用`co_names`的指令的操作数对应的变量名，不加以混淆，避免命名冲突。  
此外，由于`from ... import *`指令用到的`IMPORT_STAR`会导入大量的名称，因此也需要不混淆导入的名字。  

##### 5. 递归处理嵌套字节码

Python字节码用到的常量会存储在`co_consts`属性中。如果代码定义了函数或者类，函数、类本身的字节码也会放在`co_consts`。  
如`compile("def f():pass","","exec")`返回的字节码的`co_consts`是`(<code object f at 0x..., file "", line 1>, 'f', None)`，会嵌套进函数`f()`本身的字节码。  

代码会：
- 遍历 `co_consts`，找到嵌套的字节码对象（如嵌套函数、类等）。
- 对嵌套的字节码对象递归调用 `process_code`。

##### 6. 对于格式化字符串(f-string)是否有效

Python的格式化字符串在编译成字节码时，会抹去具体的变量名，因此格式化字符串不可能一整段地存储在`co_consts`，  
而是会分割成多个子串，就像这样：
```python
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
```
由于变量名`x`存储在`LOAD_NAME`的操作数，`co_names`数组中，因此依然是能被混淆的。  

#### 混淆效果示例

这是将混淆后的.pyc文件，用uncompyle6库反编译得到的字节码示例（`obfuscate_bytecode`参数设为了`False`，便于观察到反编译结果，而且开启了混淆参数名`obfuscate_argname`）。  
由于`co_name`信息被删除，类名和函数名无法被反编译，但类和函数存储在了局部和全局变量，因此混淆后的代码依然能运行：
```
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

    def (l0):
        return l0._DynObj__code

    def (l0, l1):
        return g18(f"{g16(l0, ADD)} + {g16(l1, ADD)}", ADD)

...
# Deparsing stopped due to parse error
```

#### 兼容性
这个混淆工具也兼容所有Python 3版本，由于不依赖特定版本的字节码。

## 4.脱壳工具
`pyc_zipper_unpack.py`这个脱壳工具支持脱壳前面压缩工具压缩过的`.pyc`文件，将压缩前的`.pyc`文件还原。  
但是，脱壳工具无法还原混淆工具混淆过的指令和变量名。  

---

This repository implements a complete toolchain for compressing, packing, and unpacking pyc files based on Python's underlying bytecode.

## 0. Dependencies
The packing and unpacking tools depend on the `pyobject` library, particularly the `Code` class in the `pyobject.code_` submodule. The `Code` class is compatible across multiple Python versions (currently supporting 3.4 to 3.14).  
The `pyobject` library can be found on [GitHub](https://github.com/ekcbw/pyobject) or installed via the command `pip install pyobject`.  

## 1. Command Line
```
python pyc_zipper_xxx.py <input .pyc file1> <input .pyc file2> ...
```

## 2. Compression Packing
`pyc_zipper_bz2.py`, `pyc_zipper_lzma.py`, and `pyc_zipper_zlib.py` are tools for adding a compression pack to `.pyc` files. The packed `.pyc` files will call Python's built-in `bz2`, `lzma`, or `zlib` modules to decompress the bytecode during execution.

Additionally, the packing tools will remove the `co_lnotab`, which is unnecessary additional information, and `co_filename`, which contains the privacy information of the source `.py` file path, further reducing the file size.

#### Self-Extracting Program
In the packed `.pyc` file, there is a "compression pack" that first decompresses and restores the original bytecode before execution. 

For example, using `zlib`, the self-extraction program is as follows:
```py
import zlib, marshal
exec(marshal.loads(zlib.decompress(b'x\xda...'))) # b'x\xda...' is the compressed bytecode data
```
For `bz2` and `lzma`:
```py
import bz2, marshal
exec(marshal.loads(bz2.decompress(b'BZh9...')))
```
```py
import lzma, marshal
exec(marshal.loads(lzma.decompress(b'\xfd7zXZ...')))
```

#### Compression Efficiency Comparison
My tests have shown that the `.pyc` file compressed with `lzma` results in the smallest size, followed by `bz2`, with `zlib` performing the least efficiently.

#### Compatibility
These compression tools are compatible with all versions of Python 3, as they do not rely on specific bytecode versions.

## 3. Obfuscation and Anti-Decompilation Packing
The previous compression tools cannot prevent `.pyc` files from being decompiled by libraries like `uncompyle6`. To prevent decompilation, an obfuscation tool `pyc_zipper_obfuscate.py` is used to obfuscate the bytecode instructions and variable names.

#### A Brief Introduction to the Obfuscation Principles

##### 1. Obfuscating Code Metadata and Anti-Debugging
```python
if obfuscate_lineno:
    co.co_lnotab = b''
    co.co_firstlineno = 1
if obfuscate_filename: co.co_filename = ''
if obfuscate_code_name: co.co_name = ''
```
  - Set `co_lnotab` to an empty byte string to clear the line number mapping table. (For Python 3.10+, the `pyobject` library automatically converts `co_lnotab` to `co_linetable`, so compatibility is not an issue.)
  - Set `co_firstlineno` to 1, as line numbers are calculated by adding `co_firstlineno` and the results from `co_lnotab`.
  - Set `co_filename` to an empty string to hide the file path of the code source.
  - Set `co_name` to an empty string to hide the name of the code object (e.g., function name).

This completely hides the filename, line number, and function name information in Traceback error outputs, increasing the difficulty of reverse engineering.

##### 2. Obfuscating Binary Bytecode
```python
if obfuscate_bytecode and co.co_code[-len(RET_INSTRUCTION)*2:] != RET_INSTRUCTION*2:
    co.co_code += RET_INSTRUCTION
```
- Check if the binary bytecode (`co_code`) already contains two consecutive return instructions (`RET_INSTRUCTION`) at the end. If not, append a redundant return instruction to disrupt the parsing of decompilation tools.

##### 3. Obfuscating Local Variable Names
Local variable names in Python bytecode are stored in the `co_varnames`, `co_cellvars`, and `co_freevars` attributes.  
- `co_varnames` contains local variable names used only within the function.
- `co_cellvars` contains variable names exported to inner closure functions.
- `co_freevars` contains variable names referenced from outer closure functions.

For example:
```python
def f():
    x, y = 1, 2; z = 3
    def g():
        print(x, y)
    g()
```
- `f.__code__.co_cellvars` will include the exported variable names `("x", "y")` but not `"z"`, which is only used within `f`.  
- `f.__code__.co_varnames` will include the variable name `("z",)`.  
- `g.__code__.co_freevars` will include the imported variable names `("x", "y")`.

The code replaces local variable names with sequential numbers in the following order:
1. Free variables inherited from the outer scope, stored in the `closure_vars` dictionary.
2. Newly defined `co_cellvars` within the function.
3. Ordinary variables defined in `co_varnames`.

Additionally, since obfuscating parameter names can prevent proper keyword argument passing, this feature is optional.

##### 4. Obfuscating Global Variable Names
Unlike local variables, global variable names are stored in the `co_names` attribute of the bytecode.  
The `co_names` attribute also includes other names, such as attribute names, imported module names, and built-in function names, which should not be obfuscated.

The code:
- Uses the `dis.get_instructions` function to retrieve all bytecode instructions.
- Identifies the operands of `STORE_NAME` instructions (global variable names).
- Analyzes operands of instructions like `IMPORT_NAME`, `IMPORT_FROM`, and `LOAD_ATTR` that also reference `co_names` to avoid obfuscating them and causing naming conflicts.
- Ensures that names imported via `from ... import *` (handled by the `IMPORT_STAR` instruction) are not obfuscated, as they introduce many names.

##### 5. Recursively Processing Nested Bytecode
Constants used in Python bytecode are stored in the `co_consts` attribute. If the code defines functions or classes, their bytecode is also stored in `co_consts`.  
For example, the bytecode returned by `compile("def f(): pass", "", "exec")` has `co_consts` as `(<code object f at 0x..., file "", line 1>, 'f', None)`, which includes the bytecode of the function `f()`.

The code:
- Iterates through `co_consts` to find nested bytecode objects (e.g., nested functions, classes).
- Recursively calls `process_code` on the nested bytecode objects.

##### 6. Effectiveness on Formatted Strings (f-strings)
Python's formatted strings are compiled into bytecode without storing variable names as a whole. Instead, they are split into multiple substrings, like this:
```python
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
```
Since the variable name `x` is stored as the operand of the `LOAD_NAME` instruction in the `co_names` array, it can still be obfuscated.

#### Example of Obfuscation Results
Here is an example of bytecode obtained by decompiling an obfuscated `.pyc` file using the `uncompyle6` library (`obfuscate_bytecode` was set to `False` for easier observation of the decompiled results, and parameter name obfuscation `obfuscate_argname` was enabled).  
Since the `co_name` information was removed, class and function names cannot be decompiled. However, the obfuscated code still runs because the classes and functions are stored in local and global variables:
```
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

    def (l0):
        return l0._DynObj__code

    def (l0, l1):
        return g18(f"{g16(l0, ADD)} + {g16(l1, ADD)}", ADD)

...
# Deparsing stopped due to parse error
```

#### Compatibility
This obfuscation tool is also compatible with all versions of Python 3, as it does not depend on specific bytecode versions.

## 4. Unpacking Tool
The unpacking tool `pyc_zipper_unpack.py` supports unpacking `.pyc` files that have been packed using the aforementioned compression tools. It restores the original `.pyc` file before compression.  
However, the unpacking tool cannot restore the instructions and variable names that have been obfuscated by the obfuscation tool.
