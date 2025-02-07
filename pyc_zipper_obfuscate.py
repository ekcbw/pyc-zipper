# pyc文件压缩、保护工具
import sys,marshal,builtins
from dis import get_instructions
from inspect import iscode
from pyobject.code_ import Code
try:
    from importlib._bootstrap_external import MAGIC_NUMBER
except ImportError:
    from importlib._bootstrap import MAGIC_NUMBER

RET_INSTRUCTION=compile('','',"exec").co_code[-2:] \
    if sys.version_info.minor >= 6 else b'S' # 获取当前版本的返回指令
def is_builtin(name):
    return hasattr(builtins,name)
def is_magicname(name):
    return name.startswith("__") and name.endswith("__")
def dump_to_pyc(pycfilename,code,pycheader=None):
    # 生成pyc文件，支持自定义的文件头
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

def process_code(co,closure_vars={},globalvars={},
                 obfuscate_global=True,obfuscate_lineno=True,
                 obfuscate_filename=True,obfuscate_code_name=True,
                 obfuscate_bytecode=True,obfuscate_argname=False):
    # obfuscate_argname的函数目前不能用关键字参数调用
    # closure_vars: 闭包函数使用的外部本地变量
    old_co=co.copy()
    print(f"Processing name {old_co.co_name!r}")

    if obfuscate_lineno:
        co.co_lnotab = b''
        co.co_firstlineno=1
    if obfuscate_filename:co.co_filename = ''
    if obfuscate_code_name:co.co_name = ''
    if obfuscate_bytecode and \
        co.co_code[-len(RET_INSTRUCTION)*2:]!=RET_INSTRUCTION*2:
        co.co_code += RET_INSTRUCTION # 增加一个无用的返回指令，用于干扰反编译器的解析

    # 混淆局部变量名
    argcount = co.co_argcount+co.co_kwonlyargcount \
               if not obfuscate_argname else 0 # 无需加上co_posonlyargcount的值 (Python 3.8+中)
    if closure_vars:delta=max(closure_vars.values())+1 # 避开已有的变量名
    else:delta=0 # delta: 当前可用的下一个变量序号
    new_closure_vars=closure_vars.copy() # 定义新的混淆表 (用int是为了能用max() )
    closure_var_in_varnames=[]
    for var in co.co_cellvars:
        if is_magicname(var):continue # 修复RuntimeError: super(): __class__ cell not found的bug
        if var in co.co_varnames: # 在co_varnames中，用co_varnames的名称
            if co.co_varnames.index(var)>=argcount:
                closure_var_in_varnames.append(var)
        else:
            new_closure_vars[var]=delta
            delta+=1
    for var in closure_var_in_varnames:
        new_closure_vars[var]=co.co_varnames.index(var)+delta

    co.co_freevars=tuple(f"l{closure_vars[name]}" if name in closure_vars else name
                         for name in co.co_freevars)
    co.co_cellvars=tuple(f"l{new_closure_vars[name]}" if name in new_closure_vars else name
                         for name in co.co_cellvars)

    co.co_varnames = co.co_varnames[:argcount] + \
                     tuple(f"l{i}" for i in range(argcount+delta,
                                                 len(co.co_varnames)+delta))

    # 混淆全局变量，跳过导入的名称以及内置函数
    new_globalvars=globalvars.copy()
    if obfuscate_global: # 只有是全局的字节码，才能新定义混淆表
        insts=list(get_instructions(co._code))
        ignores=[];available_names=[] # ignores: 不能混淆的变量名, available_names: 可以混淆的
        for i,inst in enumerate(insts):
            if inst.opname in ["IMPORT_NAME","IMPORT_FROM","LOAD_ATTR",
                               "STORE_ATTR","DELETE_ATTR","LOAD_METHOD",
                               "LOAD_FROM_DICT_OR_GLOBALS"]: # 遇到依赖co_names的指令
                ignores.append(inst.argval)
            elif inst.opname == "IMPORT_STAR": # 排除所有import *语句导入的名称
                if i == 0:
                    raise ValueError(f"{old_co.co_name}: IMPORT_STAR shouldn't be at offset 0")
                mod_name=insts[i-1].argval
                try:
                    print(f"Processing import *: {mod_name!r}")
                    mod=__import__(mod_name) # 导入模块
                except ImportError:
                    raise ValueError(f"{old_co.co_name}: Cannot handle IMPORT_STAR (missing {mod_name})")
                names=getattr(mod,"__all__",None) # 解析模块的变量名
                if names is None:
                    names=[name for name in dir(mod) if not name.startswith("_")]
                ignores.extend(names)
            elif inst.opname == "STORE_NAME":
                available_names.append(inst.argval) # 仅混淆STORE_NAME定义的变量名

        available_names=[name for name in available_names \
                         if name not in ignores and \
                         not is_builtin(name) and not is_magicname(name)] # 过滤available_names
        for i,var in enumerate(co.co_names):
            if var in available_names:
                new_globalvars[var]=f"g{i}" # 生成全局变量的序号

    co.co_names=tuple(new_globalvars.get(name,name) for name in co.co_names)

    # 递归处理自身包含的字节码
    co_consts = co.co_consts
    for i,obj in enumerate(co_consts):
        if iscode(obj):
            data=process_code(Code(obj),new_closure_vars,new_globalvars,
                              obfuscate_global=False) # 不再混合内层的全局变量
            co_consts = co_consts[:i] + (data._code,) + co_consts[i+1:]
    co.co_consts = co_consts
    return co

if len(sys.argv) == 1:
    print('Usage: %s [filename]' % sys.argv[0])

for file in sys.argv[1:]:
    print('Processing:',file)
    data=open(file,'rb').read()
    if data[16] in (0x63,0xe3): # 0xe3为cpython，0x63为pypy
        old_header=data[:16];data=data[16:]
    else:
        old_header=data[:12];data=data[12:] # 兼容不同Python版本
    co = Code(marshal.loads(data))

    process_code(co)
    dump_to_pyc(file,co,pycheader=old_header)
    print(f"Completed: {file}\n")
