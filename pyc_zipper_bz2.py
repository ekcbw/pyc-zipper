# 使用bz2的pyc文件压缩、保护工具
import sys,marshal,bz2
from inspect import iscode
from pyobject.code_ import Code
try:
    from importlib._bootstrap_external import MAGIC_NUMBER
except ImportError:
    from importlib._bootstrap import MAGIC_NUMBER

def dump_to_pyc(pycfilename,code,pycheader=None):
    c=Code()
# 反汇编的co_code
##2     0 LOAD_CONST               0 (455)
##      2 LOAD_CONST               1 (None)
##      4 IMPORT_NAME              0 (bz2)
##      6 STORE_NAME               0 (bz2)
##      8 LOAD_CONST               0 (455)
##     10 LOAD_CONST               1 (None)
##     12 IMPORT_NAME              1 (marshal)
##     14 STORE_NAME               1 (marshal)
##
##3    16 LOAD_NAME                2 (exec)
##     18 LOAD_NAME                1 (marshal)
##     20 LOAD_METHOD              3 (loads)
##     22 LOAD_NAME                0 (bz2)
##     24 LOAD_METHOD              4 (decompress)
##     26 LOAD_CONST               2 (数据)
##     28 CALL_METHOD              1
##     30 CALL_METHOD              1
##     32 CALL_FUNCTION            1
##     34 RETURN_VALUE
    c.co_code=b'''d\x00d\x01l\x00Z\x00d\x00d\x01l\x01Z\x01e\x02\
e\x01\xa0\x03e\x00\xa0\x04d\x02\xa1\x01\xa1\x01\x83\x01\x01\x00d\x01S\x00''' # 仅支持Python 3.7及以上
    c.co_names=('bz2', 'marshal', 'exec', 'loads', 'decompress')
    #也可换成bz2,bz2等其他压缩模块
    c.co_consts=(0, None,bz2.compress(marshal.dumps(code._code)))
    c.co_flags=64 # NOFREE
    c.co_stacksize=6
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
    if data[16]==227:
        old_header=data[:16];data=data[16:]
    else:
        old_header=data[:12];data=data[12:]
    co = Code(marshal.loads(data))

    process_code(co)
    dump_to_pyc(file,co,pycheader=old_header)
    print('Processed:',file)
