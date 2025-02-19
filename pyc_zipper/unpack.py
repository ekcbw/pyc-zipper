import marshal,warnings

DETECTABLE_MODULES=['bz2','lzma','zlib']
def unpack_code(co,comp_module=None): # comp_module: 自定义的模块名称
    for mod_name in co.co_names: # 查找模块名称
        if mod_name == comp_module or \
            mod_name in DETECTABLE_MODULES:
            break
    else:
        raise ValueError("Not a compressed bytecode")

    for data in co.co_consts:
        if isinstance(data,bytes): # 查找压缩的二进制数据
            break
    else:
        raise ValueError("Not a compressed bytecode")

    mod=__import__(mod_name)
    decompressed=mod.decompress(data) # 解压数据
    try:marshal.loads(decompressed) # 测试解压后数据完整性
    except Exception as err:
        warnings.warn("Bad compressed data: %s (%s)" % (
                      type(err).__name__,str(err)))
    return decompressed
