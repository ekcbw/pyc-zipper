import marshal
from pyobject.code_ import Code

def compress_code(code,comp_module=None):
    if comp_module is not None:
        if isinstance(comp_module,str):
            comp_module=__import__(comp_module)
        print(f"Compressing file using {comp_module.__name__}")
        c=Code(compile(f"""
import {comp_module.__name__},marshal
exec(marshal.loads(zlib.decompress(b'')))""","","exec"))
        #也可换成bz2,lzma等其他压缩模块
        data=comp_module.compress(marshal.dumps(code._code))
        for i in range(len(c.co_consts)):
            if c.co_consts[i]==b'':
                # 将压缩后数据插入co_consts
                c.co_consts=c.co_consts[:i]+(data,)+c.co_consts[i+1:]
                break
        return c
    else:
        return code
