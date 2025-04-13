import sys,os,marshal,py_compile,functools
try:
    from importlib._bootstrap_external import MAGIC_NUMBER
except ImportError:
    from importlib._bootstrap import MAGIC_NUMBER
from pyobject import Code
import pyc_zipper # 不使用from pyc_zipper import ...，由于pyc_zipper尚未初始化完毕

def compile_to_pyc(filename):
    target_file=os.path.splitext(filename)[0]+".pyc"
    py_compile.compile(filename,cfile=target_file,doraise=True)
    return target_file

def dump_to_pyc(pycfilename,code,pycheader=None):
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
        if isinstance(code,Code):
            marshal.dump(code._code,f)
        else:
            f.write(code)

def hook_pyinstaller(*args,**kw): # 可在pyinstaller的spec文件中使用
    try:
        import PyInstaller.building.utils as utils
        import PyInstaller.archive.writers as writers
    except ImportError:
        raise NotImplementedError("PyInstaller is required")

    _get_code_object = utils.get_code_object
    @functools.wraps(utils.get_code_object)
    def inner_get_code_object(*_args,**_kw):
        print(f"""pyc-zipper: processing \
{_args}{' '+str(_kw) if _kw else ''} in get_code_object""")
        co = _get_code_object(*_args,**_kw)
        return pyc_zipper.process_code(Code(co),*args,**kw).to_code()

    utils.get_code_object=inner_get_code_object
    writers.get_code_object=inner_get_code_object