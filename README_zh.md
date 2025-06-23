[[English](README.md) | 中文]

本仓库基于Python的底层字节码，实现了一套完整的pyc文件的压缩、加壳、混淆和脱壳工具链。

## 0.安装及依赖的库

打开终端，输入命令：
```
pip install pyc-zipper
```
即可安装`pyc-zipper`。  
此外，本工具依赖于[pyobject](https://github.com/ekcbw/pyobject)库，尤其是[pyobject.code](https://github.com/ekcbw/pyobject/blob/main/pyobject/code.py)中的`Code`类。`Code`类是跨多个Python版本(目前支持3.4到3.14，以及PyPy等)的可变字节码封装。  
安装`pyc-zipper`时，会自动一并安装`pyobject`库，因此无需手动安装。  

## 1.用法及命令行
```
pyc-zipper [options] [file1 file2 ...]
```
其中的选项`options`有: 
```
pyc-zipper [-h] [--obfuscate] [--obfuscate-global]
                [--obfuscate-lineno] [--obfuscate-filename]
                [--obfuscate-code-name] [--obfuscate-bytecode]
                [--obfuscate-argname] [--unpack] [--version]
                [--compress-module COMPRESS_MODULE] [--no-obfuscation]
                file1 [file2 ...]
```
**压缩、混淆和加壳**
- file1, file2: 文件名，可以是.py文件或.pyc文件。如果提供了.py文件，则会自动生成处理后的.pyc。  
- compress-module: 压缩pyc文件用的模块，如bz2,lzma,zlib,brotli等，但要求模块必须有`compress`和`decompress`函数。如果不提供，则不压缩pyc文件。  
- obfuscate: 使用默认选项混淆pyc文件，会启用混淆除参数名以外的所有选项。  
- obfuscate-global: 混淆全局变量名，以及类名、函数名等。  
- obfuscate-lineno: 混淆行号信息，使得反编译者无法通过Traceback得知行号进行反编译。  
- obfuscate-filename: 混淆字节码对应的原始.py源文件名，会去除源文件名如`C:\Users\<用户名>\...\Python313\Lib\original_source.py`中的用户名等隐私。  
- obfuscate-code-name: 混淆字节码的内部名称(函数名、类名)。  
- obfuscate-bytecode: 混淆字节码的指令。  
- obfuscate-argname: 混淆函数参数名。(目前要求代码不能用关键字参数调用被混淆的函数)  
- no-obfuscation: 禁用混淆功能。(如果不指定禁用混淆，混淆本地变量名是默认启用的)  

**解压缩、脱壳**
- unpack: 解压缩被压缩过的pyc文件，pyc-zipper会自动检测模块名称，模块名称也可以手动通过compress-module参数提供。注意unpack开关只能和compress-module，不能和其他开关一起使用。  

此外，如果终端提示找不到`pyc-zipper`命令，可以用`python -m pyc_zipper`替代。  

#### 用于PyInstaller
`pyc-zipper`内置了集成PyInstaller打包工具的功能。调用`pyinstaller file.py`之后，会生成一个文件`file.spec`。  
`file.spec`一般是一个Python文件，只需要在`file.spec`开头加入：  
```python
from pyc_zipper import hook_pyinstaller
hook_pyinstaller()
```
或者自定义自己的参数，如：
```python
hook_pyinstaller(comp_module="lzma",no_obfuscation=False,
                 obfuscate_global=True,obfuscate_lineno=True,
                 obfuscate_filename=True,obfuscate_code_name=True,
                 obfuscate_bytecode=True,obfuscate_argname=False)
```
`comp_module`为表示压缩模块名称的字符串，默认为`None`，除此之外其他参数的用法和命令行的`pyc-zipper`一致。  
最后运行：  
```
pyinstaller file.spec
```
注意不能再使用`pyinstaller file.py`，因为会生成一个新的spec文件覆盖掉`file.spec`。  
如果在运行PyInstaller时看到`pyc-zipper`的输出信息，如：  
```
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
```
则混淆成功。

## 2.压缩壳
[pyc_zipper/compress.py](https://github.com/ekcbw/pyc-zipper/blob/main/pyc_zipper/compress.py)负责为.pyc文件添加压缩壳，加壳后的.pyc文件在运行时，会调用Python内置的`bz2`，`lzma`或`zlib`模块对压缩前的字节码进行自解压缩，再执行解压后的字节码。
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
前面的压缩工具并不能防止`.pyc`文件被`uncompyle6`等库反编译。要防止反编译，还需要用到源代码在[pyc_zipper/obfuscate.py](https://github.com/ekcbw/pyc-zipper/blob/main/pyc_zipper/obfuscate.py)中的混淆工具，混淆字节码的指令，并混淆变量名。

#### `obfuscate_code` 函数的简明混淆原理

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
```python
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
```

#### 兼容性
这个混淆工具也兼容所有Python 3版本，由于不依赖特定版本的字节码。

## 4.脱壳工具
源代码在[pyc_zipper/unpack.py](https://github.com/ekcbw/pyc-zipper/blob/main/pyc_zipper/unpack.py)的脱壳工具支持脱壳前面压缩工具压缩过的`.pyc`文件，将压缩前的`.pyc`文件还原。  
但是，脱壳工具无法还原混淆工具混淆过的指令和变量名。  