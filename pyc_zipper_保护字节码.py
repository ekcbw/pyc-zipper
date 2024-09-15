# pyc文件压缩、保护工具
import sys,marshal
from inspect import iscode
from pyobject.code_ import Code
try:
    from importlib._bootstrap_external import MAGIC_NUMBER
except ImportError:
    from importlib._bootstrap import MAGIC_NUMBER

def dump_to_pyc(pycfilename,code,pycheader=None):
    # 制作pyc文件
    with open(pycfilename,'wb') as f:
        # 写入 pyc 文件头
        if pycheader is None:
            # 自动生成 pyc 文件头
            if sys.version_info.minor >= 7:
                pycheader=MAGIC_NUMBER+b'\x00'*12
            else:
                pycheader=MAGIC_NUMBER+b'\x00'*8
        f.write(pycheader)
        # 写入bytecode
        marshal.dump(code._code,f)

def process_code(co):
    co.co_lnotab = b''
    if co.co_code[-4:]!=b'S\x00S\x00':
        co.co_code += b'S\x00' # 增加一个无用的RETURN_VALUE指令，用于干扰反编译器的解析
    co.co_filename = ''
    #co.co_name = ''
    co_consts = co.co_consts
    # 无需加上co.co_posonlyargcount的值 (Python 3.8+中)
    argcount = co.co_argcount+co.co_kwonlyargcount
    # 修改、混淆本地变量的名称
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
if len(sys.argv) == 1:
    print('Usage: %s [filename]' % sys.argv[0])

for file in sys.argv[1:]:
    data=open(file,'rb').read()
    if data[16]==227: # 兼容不同Python版本
        old_header=data[:16];data=data[16:]
    else:
        old_header=data[:12];data=data[12:]
    co = Code(marshal.loads(data))

    process_code(co)
    dump_to_pyc(file,co,pycheader=old_header)
    print('Processed:',file)
