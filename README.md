本仓库实现了一套pyc文件的压缩、加壳和脱壳工具链。
## 0.依赖的模块
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
经测试，这些压缩工具兼容3.7至3.10的Python版本。
而针对3.11及以上版本的适配，作者正在开发中。
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
这个混淆工具兼容从3.4到3.13的所有Python版本。
## 4.脱壳工具
`pyc_zipper_脱壳.py`这个脱壳工具支持脱壳前面压缩工具压缩过的`.pyc`文件，将压缩前的`.pyc`文件还原。
但是，脱壳工具无法还原混淆工具混淆过的指令和变量名。
