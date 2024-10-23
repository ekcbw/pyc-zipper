# 使用bz2的pyc文件压缩、保护工具
import sys,marshal,bz2
from inspect import iscode
from pyobject.code_ import Code
try:
    from importlib._bootstrap_external import MAGIC_NUMBER
except ImportError:
    from importlib._bootstrap import MAGIC_NUMBER

def dump_to_pyc(pycfilename,code,pycheader=None):
    c=Code(compile("""
import bz2,marshal
exec(marshal.loads(bz2.decompress(b'')))""","","exec"))
    #也可换成bz2,lzma等其他压缩模块
    data=bz2.compress(marshal.dumps(code._code))
    for i in range(len(c.co_consts)):
        if c.co_consts[i]==b'':
            c.co_consts=c.co_consts[:i]+(data,)+c.co_consts[i+1:]
            break
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
        marshal.dump(c._code,f)

def process_code(co):
    co.co_lnotab = b''
    co.co_filename = ''
    #co.co_name = ''
    co_consts = co.co_consts
    for i in range(len(co_consts)):
        obj = co_consts[i]
        if iscode(obj):
            data=process_code(Code(obj)) # 递归处理
            co_consts = co_consts[:i] + (data._code,) + co_consts[i+1:]
    co.co_consts = co_consts
    return co

if len(sys.argv) == 1:
    print('Usage: %s [filename]' % sys.argv[0])

for file in sys.argv[1:]:
    data=open(file,'rb').read()
    if data[16]==0xe3:
        old_header=data[:16];data=data[16:]
    else:
        old_header=data[:12];data=data[12:]
    co = Code(marshal.loads(data))

    process_code(co)
    dump_to_pyc(file,co,pycheader=old_header)
    print('Processed:',file)
