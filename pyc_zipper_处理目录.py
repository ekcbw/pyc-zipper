# 批量去除目录中的.pyc文件中的无效信息，但不压缩和混淆
import sys,marshal,os
from inspect import iscode
from pyobject.code_ import Code
from search_file import search # search_file库
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

def process(file):
    data=open(file,'rb').read()
    if data[16]==0xe3:
        old_header=data[:16];data=data[16:]
    else:
        old_header=data[:12];data=data[12:]
    co = Code(marshal.loads(data))

    process_code(co)
    dump_to_pyc(file,co,pycheader=old_header)
    print('Processed:',file)

sys.path.append('\\'.join(__file__.split('\\')[:-3]))
if len(sys.argv)==2 and os.path.isdir(sys.argv[1]):
    for file in search('.pyc',sys.argv[1]):
        process(file)
else:
    print('Usage: %s [directory name]' % sys.argv[0])
