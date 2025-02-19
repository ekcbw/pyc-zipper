import sys,os,marshal,argparse,traceback
from pyobject import Code
from pyc_zipper import process_code,__version__
from pyc_zipper.utils import compile_to_pyc,dump_to_pyc
from pyc_zipper.unpack import unpack_code

PYC_FILES=[".pyc",".pyo"]
PROG = "python -m pyc_zipper"
USAGE_MSG = "Usage: {prog} [options] [file1 file2 ...]\nDetailed "

class ArgumentParser(argparse.ArgumentParser):
    def __init__(self,usage_msg=None,conj="\n",*args,**kw):
        self.usage_msg=usage_msg
        self.conj=conj # 连接字符
        super().__init__(*args,**kw)
    def format_usage(self,*args,**kw): # 重写默认的帮助格式
        result=super().format_usage(*args,**kw)
        if self.usage_msg is not None:
            result=self.usage_msg+self.conj+result
        return result
    def format_help(self,*args,**kw):
        result=super().format_help(*args,**kw)
        if self.usage_msg is not None:
            result=self.usage_msg+self.conj+result
        return result

def main():
    parser = ArgumentParser(USAGE_MSG.format(prog=PROG),"",prog=PROG) # usage=usage_msg

    # 添加开关参数
    parser.add_argument('--obfuscate', action='store_true', 
        help='Obfuscate pyc files, enables all obfuscation options except --obfuscate-argname')
    parser.add_argument('--obfuscate-global', action='store_true', help='Obfuscate global variables')
    parser.add_argument('--obfuscate-lineno', action='store_true', help='Obfuscate line numbers')
    parser.add_argument('--obfuscate-filename', action='store_true', help='Obfuscate filename')
    parser.add_argument('--obfuscate-code-name', action='store_true', help='Obfuscate code name')
    parser.add_argument('--obfuscate-bytecode', action='store_true', help='Obfuscate bytecode')
    parser.add_argument('--obfuscate-argname', action='store_true', help='Obfuscate argument names')
    parser.add_argument('--no-obfuscation', action='store_true', help="Don't obfuscate")
    parser.add_argument('--unpack', action='store_true', help='Unpack pyc files')
    parser.add_argument('--version', action='store_true', help='Display the version and exit')
    parser.add_argument('--compress-module', type=str, help='Specify module to compress (optional)')

    # 添加位置参数，接受一个或多个文件名
    parser.add_argument('filenames', nargs='*', help='py or pyc files to be processed')

    # 解析命令行参数
    args = parser.parse_args()

    # 处理参数
    if args.version:
        print(f"""pyc-zipper {__version__} on {sys.implementation.name} \
{sys.winver} (pyc file: {sys.implementation.cache_tag})""")
        sys.exit()
    if not args.filenames:
        parser.print_usage()
        print("Error: at least one py or pyc file is required")
        sys.exit(1)

    if args.obfuscate: # 设置默认选项
        args.obfuscate_global^=True
        args.obfuscate_lineno^=True
        args.obfuscate_filename^=True
        args.obfuscate_code_name^=True
        args.obfuscate_bytecode^=True
        args.obfuscate_argname^=False

    if args.compress_module is not None:
        try:
            module=__import__(args.compress_module)
            assert module.decompress(module.compress(b'test')) == b'test'
        except Exception as err: # 主要为AttributeError, AssertionError, ValueError, ImportError等
            parser.print_usage()
            print(f"""{args.compress_module} is expected to have 'compress' and 'decompress'
         methods that are reversible and accept bytes. ({type(err).__name__}: {err})""")
            sys.exit(1)

    for file in args.filenames:
        if os.path.splitext(file.lower())[1] not in PYC_FILES:
            pycfile=compile_to_pyc(file) # 编译.py文件
        else:
            pycfile=file
        data = open(pycfile, 'rb').read()
        if data[16] in (0x63,0xe3,0xc3): # 0xe3,0x63,0xc3分别是cpython,pypy,graalpy
            old_header=data[:16];data=data[16:]
        else:
            old_header=data[:12];data=data[12:] # 兼容旧版Python
        co = Code(marshal.loads(data))

        try:
            if args.unpack:
                data=unpack_code(co,comp_module=args.compress_module)
                dump_to_pyc(pycfile, data, old_header)
            else:
                co=process_code(co,comp_module=args.compress_module,
                                obfuscate_global=args.obfuscate_global,
                                obfuscate_lineno=args.obfuscate_lineno,
                                obfuscate_filename=args.obfuscate_filename,
                                obfuscate_code_name=args.obfuscate_code_name,
                                obfuscate_bytecode=args.obfuscate_bytecode,
                                obfuscate_argname=args.obfuscate_argname)
                dump_to_pyc(pycfile, co, old_header)
        except Exception:
            print('Error processing:',file)
            traceback.print_exc()
            print()
        else:
            print(f"{'Unpacked' if args.unpack else 'Processed'}: {file}")

def main_scripts(): # 从scripts的pyc-zipper命令调用
    global PROG
    PROG="pyc-zipper" # 修改帮助信息显示格式
    main()

if __name__=="__main__":main()