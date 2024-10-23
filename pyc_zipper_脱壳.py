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

modules=['bz2','lzma','zlib']
for file in sys.argv[1:]:
    try:
        with open(file,'rb') as f:
            d=f.read()
            if d[16]==0xe3:  # 寻找数据开始的'\xe3'标志
                old_header=d[:16];d=d[16:]
            else:
                old_header=d[:12];d=d[12:]

            c=marshal.loads(d)
            for mod_name in c.co_names:
                if mod_name in modules:
                    break
            else:
                raise ValueError('Not a compressed file: '+file)

            for data in c.co_consts:
                if isinstance(data,bytes):
                    break
            else:
                raise ValueError('Not a compressed file: '+file)

            mod=__import__(mod_name)
            decompressed=mod.decompress(data) # 解压数据
            try:marshal.loads(decompressed) # 测试解压后数据完整性
            except Exception as err:
                warnings.warn("Bad compressed data: %s (%s)" % (
                              type(err).__name__,str(err)))
            dump_to_pyc(file,decompressed,old_header)
            print('Processed:',file)
    except Exception:
        traceback.print_exc()
