"""
pyc-zipper is a complete toolchain for compressing, obfuscating, and unpacking pyc files based on Python's underlying bytecode.
pyc-zipper是基于Python的底层字节码，实现的一套完整的pyc文件的压缩、混淆和脱壳工具链。
"""
from pyc_zipper.compress import compress_code
from pyc_zipper.obfuscate import obfuscate_code
from pyc_zipper.utils import dump_to_pyc,compile_to_pyc,hook_pyinstaller

__version__="1.0.4"

def process_code(co,comp_module=None,no_obfuscation=False,
                 obfuscate_global=True,obfuscate_lineno=True,
                 obfuscate_filename=True,obfuscate_code_name=True,
                 obfuscate_bytecode=True,obfuscate_argname=False):
    if not no_obfuscation:
        co=obfuscate_code(co,
                          obfuscate_global=obfuscate_global,
                          obfuscate_lineno=obfuscate_lineno,
                          obfuscate_filename=obfuscate_filename,
                          obfuscate_code_name=obfuscate_code_name,
                          obfuscate_bytecode=obfuscate_bytecode,
                          obfuscate_argname=obfuscate_argname)
    if comp_module is not None:
        return compress_code(co,comp_module)
    else:
        return co