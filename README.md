**The English introduction is placed below the Chinese version.**

本仓库基于Python的底层字节码，实现了一套完整的pyc文件的压缩、加壳和脱壳工具链。
## 0.依赖的库
这些加壳和脱壳的工具依赖于`pyobject`库，尤其是`pyobject.code_`这个子模块中的`Code`类。`pyobject`可通过`pip install pyobject`命令安装。
## 1.命令行
```
python pyc_zipper_xxx.py <待处理的.pyc文件1> <.pyc文件2> ...
```
对于处理目录的工具：
```
python pyc_zipper_处理目录.py <待处理的目录>
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
前面的压缩工具并不能防止`.pyc`文件被`uncompyle6`等库反编译。要防止反编译，还需要用到混淆工具`pyc_zipper_保护字节码.py`，混淆字节码的指令，并混淆变量名。
这是混淆部分的核心代码（如果有更好的混淆方法，可以在issue中提出）：
```py
def process_code(co):
    co.co_lnotab = b''
    if co.co_code[-4:]!=b'S\x00S\x00': # 未添加过
        co.co_code += b'S\x00' # 增加一个无用的RETURN_VALUE指令，用于干扰反编译器的解析
    co.co_filename = ''
    co_consts = co.co_consts
    # 无需加上co.co_posonlyargcount的值 (Python 3.8+中)
    argcount = co.co_argcount+co.co_kwonlyargcount
    # 修改、混淆本地变量的名称为0,1,2,3,4,5,6,7,8,9,...
    co.co_varnames = co.co_varnames[:argcount] + \
                     tuple(str(i) for i in range(argcount,len(co.co_varnames)))
    # 递归处理自身包含的字节码
    for i in range(len(co_consts)):
        obj = co_consts[i]
        if iscode(obj):
            data=process_code(Code(obj))
            co_consts = co_consts[:i] + (data._code,) + co_consts[i+1:]
    co.co_consts = co_consts
    return co
```
#### 兼容性
这个混淆工具也兼容所有Python 3版本，由于不依赖特定版本的字节码。
## 4.脱壳工具
`pyc_zipper_脱壳.py`这个脱壳工具支持脱壳前面压缩工具压缩过的`.pyc`文件，将压缩前的`.pyc`文件还原。
但是，脱壳工具无法还原混淆工具混淆过的指令和变量名。


This repository implements a complete toolchain for compressing, packing, and unpacking pyc files based on Python's underlying bytecode.

## 0. Dependencies
The packing and unpacking tools depend on the `pyobject` library, particularly the `Code` class in the `pyobject.code_` submodule. You can install `pyobject` using the command:
```
pip install pyobject
```

## 1. Command Line
```
python pyc_zipper_xxx.py <input .pyc file1> <input .pyc file2> ...
```
For the directory processing tool:
```
python pyc_zipper_process_directory.py <input directory>
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
The previous compression tools cannot prevent `.pyc` files from being decompiled by libraries like `uncompyle6`. To prevent decompilation, an obfuscation tool `pyc_zipper_obfuscate_bytecode.py` is used to obfuscate the bytecode instructions and variable names.

Here is the core code for the obfuscation part (if there are better obfuscation methods, you can suggest them in the issues):
```py
def process_code(co):
    co.co_lnotab = b''
    if co.co_code[-4:] != b'S\x00S\x00': # Not previously added
        co.co_code += b'S\x00' # Add a useless RETURN_VALUE instruction to confuse the decompiler
    co.co_filename = ''
    co_consts = co.co_consts
    # No need to add co.co_posonlyargcount value (for Python 3.8+)
    argcount = co.co_argcount + co.co_kwonlyargcount
    # Rename and obfuscate local variable names to 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,...
    co.co_varnames = co.co_varnames[:argcount] + \
                     tuple(str(i) for i in range(argcount, len(co.co_varnames)))
    # Recursively process the bytecode contained within itself
    for i in range(len(co_consts)):
        obj = co_consts[i]
        if iscode(obj):
            data = process_code(Code(obj))
            co_consts = co_consts[:i] + (data._code,) + co_consts[i + 1:]
    co.co_consts = co_consts
    return co
```

#### Compatibility
This obfuscation tool is also compatible with all versions of Python 3, as it does not depend on specific bytecode versions.

## 4. Unpacking Tool
The unpacking tool `pyc_zipper_unpack.py` supports unpacking `.pyc` files that have been packed using the aforementioned compression tools. It restores the original `.pyc` file before compression.
However, the unpacking tool cannot restore the instructions and variable names that have been obfuscated by the obfuscation tool.
