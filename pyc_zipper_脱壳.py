import sys,marshal,traceback,warnings
try:
    from importlib._bootstrap_external import MAGIC_NUMBER
except ImportError:
    from importlib._bootstrap import MAGIC_NUMBER

def dump_to_pyc(pycfilename,data,pycheader=None):
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
        f.write(data)

if len(sys.argv) == 1:
    print('Usage: %s [filename]' % sys.argv[0])

for file in sys.argv[1:]:
    try:
        with open(file,'rb') as f:
            d=f.read()
            if d[16]==227:  # 寻找数据开始的'\xe3'标志
                old_header=d[:16];d=d[16:]
            else:
                old_header=d[:12];d=d[12:]
            c=marshal.loads(d)
            modname=c.co_names[0] if len(c.co_names)>=1 else ''
            if modname in ('bz2','lzma','zlib'):
                mod=__import__(modname)
                data=mod.decompress(c.co_consts[2]) # 解压数据
                try:marshal.loads(data) # 测试解压后数据完整性
                except Exception as err:
                    warnings.warn("Bad decompressed data: %s (%s)" % (
                        type(err).__name__,str(err)))
                dump_to_pyc(file,data,old_header)
                print('Processed:',file)
            else:
                raise TypeError('不是压缩的pyc文件: '+file)
    except Exception:
        traceback.print_exc()
