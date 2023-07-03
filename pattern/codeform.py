#coding=utf8
import re
import os
import json
from multiprocessing import Pool
from pattern.codefiles import filesof, read_f, write_f
import clang.cindex
clang.cindex.Config.set_library_file("/work/jobnote/clang+llvm-3.8.0/lib/libclang.so")

MACRO_USE_TRACE='''
#include "syslog.h"
#include <pthread.h>
#ifndef INC_COMM_DEBUG
#define INC_COMM_DEBUG 1
#endif
#if INC_COMM_DEBUG
#define COMM_DEBUG(argfmt, ...) syslog(LOG_DEBUG, "TID = %lu" argfmt, pthread_self(), ##__VA_ARGS__);
#else
#define COMM_DEBUG(argfmt, ...)
#endif
'''
#compile_args={}
trigger_form={}
def code_conv(code, convs):
    convs.reverse()
    for start,end,repl in convs:
        code=code[:start]+repl+code[end:]
    return code

def set_macros(macros, form):
    global trigger_form
    global MACRO_USE_TRACE
    trigger_form = form
    if 'LOG_PREDEF' in macros:
        MACRO_USE_TRACE = macros['LOG_PREDEF']
def flags_and_files(mkPath):
    MACRO_PATT=re.compile("(?<=\n)(\w+)\s*\=\s*(.+)")
    mkfpaths = [mkfp for mkfp in filesof(mkPath, 'build\.make$')]
    for mkfPath in mkfpaths:
        _args={}
        if re.search("build\.make$", mkfPath):
            flagPath=os.path.join(os.path.dirname(mkfPath), "flags.make")
            _args.update(dict(
                (macro.strip(),re.findall('\S+',defs))
                for macro,defs in re.findall(MACRO_PATT, read_f(flagPath))
            ))
            mkcode = read_f(mkfPath)
            yield _args, set(re.findall('\.o\:\s*(.*\.(?:c|cc|cpp))\W', mkcode))        
def _used_flag(src_file,compile_args):
    ext=re.search(".*(\.(?:c$|cc$|cpp$))",src_file).group(1)
    flags_map={
        '.c':'C_FLAGS', '.cc':'CXX_FLAGS', '.cpp':'CXX_FLAGS'
    }
#        print flags_map[ext], ext
    used_flags=[]
    if flags_map[ext] in compile_args:
        used_flags=compile_args[flags_map[ext]]
    return used_flags+[
                            "-I/work/sv-g5-system-sdk/sysroots/cortexa15t2hf-vfp-neon-linux-gnueabi/include/c++/4.7.3",
                            "-I/work/sv-g5-system-sdk/sysroots/cortexa15t2hf-vfp-neon-linux-gnueabi/include/c++/4.7.3/arm-linux-gnueabihf/arm-linux-gnueabi",
                            "-I/work/sv-g5-system-sdk/sysroots/cortexa15t2hf-vfp-neon-linux-gnueabi/usr/include",
                            "-Wthread-safety",
                            "-target arm-none-linux-gnueabi",
                        ]#).replace('-std=c++11','')
_triggerMapType = type({})
_triggerFuncType = type(_used_flag)

def used_flag(src_file,compile_args):
    return _used_flag(src_file,compile_args)

def trigger_parse(src_file, node, triggers, cnt=200, pnode=None):
    if(cnt<0):
        return
    cnt-=1
    if type(node)!=type(None):
        for namedkey in triggers:
            if hasattr(node, namedkey):
                attrnode=getattr(node,namedkey)
                result = ' '.join(trigger_parse(src_file, attrnode,triggers[namedkey],cnt,node))
                if len(result):
                    yield result
                        
        if node.kind.name in triggers:
            if src_file==str(node.location.file) and re.match(".*(?:\.cpp$|\.c$|\.cc$)",str(node.location.file)):
                for subexec in triggers[node.kind.name]:
                    if type(subexec) == _triggerFuncType:
                        T_result = subexec(node, pnode)
                        if T_result:
                            yield T_result
                        continue
                    if type(subexec) == _triggerMapType:
                        for c in node.get_children():
                            result = ' '.join(trigger_parse(src_file, c, subexec, cnt, node))
                            if len(result):
                                yield result
                        continue
                    yield subexec
        else:
            for c in node.get_children():
                result = ' '.join(trigger_parse(src_file, c, triggers, cnt, node))
                if len(result):
                    yield result
        
def trigger_info(src_file, node, triggers, trigged=None):
    _triggerType = type({})
    next_triggers=triggers
    if node.kind.name in triggers:
        if type(triggers[node.kind.name]) == _triggerType:
            next_triggers=triggers[node.kind.name]
            trigged=node
        elif type(trigged) != type(None):
            if str(trigged.location.file)==str(node.location.file) and re.match(".*(?:\.cpp$|\.c$|\.cc$)",str(node.location.file)):
                for func in triggers[node.kind.name]:
                    T_result = func(src_file, trigged, node)
                    if T_result:
                        yield T_result
            trigged = None
    for c in node.get_children():
        for result in trigger_info(src_file, c, next_triggers, trigged):
            yield result
def insert_traces(insertions, _code):
    inslist=list(insertions)
    inslist.reverse()
    for ins in inslist:
        tabspace=re.match('\s*', _code[ins['end']:]).group(0)
        _code=_code[:ins['end']]+tabspace+ins['trace']+_code[ins['end']:]
    ins_use_macro = re.search(re.escape(MACRO_USE_TRACE), _code)
    if ins_use_macro == None:
        _code=MACRO_USE_TRACE+_code
    else:
        rpl_use_macro = re.search(re.escape(MACRO_USE_TRACE), MACRO_USE_TRACE)
        _code=_code[:ins_use_macro.start()]+rpl_use_macro.group(0)+_code[ins_use_macro.end():]
    return _code
def parse_cc(src_file, flags):
    _index = clang.cindex.Index.create()
    compile_Flags=_used_flag(src_file,flags)
#     print src_file, compile_Flags
    tu = _index.parse(src_file, args=compile_Flags)
    del _index
    return tu
def process_async(paras):
    global trigger_form
    src_file, flags=paras
    code=read_f(src_file)
    _index = clang.cindex.Index.create()
    print src_file#, flags
    tu = _index.parse(src_file, args=flags)
    trs=list(trigger_info(src_file, tu.cursor, trigger_form))
    code=insert_traces(
        trs, code
    )
    write_f(src_file, code)
    return "write %d trace to: %s"%(len(trs),src_file)

def generate_trace( mkPath, procs=3, skip=None,reset=False):
    decls_mapping={}
    pool=Pool(processes=procs)
    pool_srcs=[]
    for flags,srcFiles in flags_and_files(mkPath):
        #print flags
        for srcPath in srcFiles:
            fpath = os.path.abspath(os.path.join(mkPath, srcPath))
            if skip != None and re.search(skip, fpath)!=None:
                continue
            if os.path.exists(fpath):
                if reset:
                    code = read_f(os.path.abspath(fpath))
                    clean_list=[it.span() for it in re.finditer("\s+COMM_DEBUG\(\"\$\d+.*\).*", code)]
                    clean_list.reverse()
                    for s,e in clean_list:
                        code = code[:s] + code[e:]
#                        if code.find(macros['LOG_PREDEF'])==-1:
#                            code.insert(code[:s].rfind('#include'),macros['LOG_PREDEF'])
                    write_f(fpath, code)
#                print ("processing: %s"%fpath)
#                process_async((fpath,_used_flag(fpath,flags)))
                pool_srcs.append((fpath,_used_flag(fpath,flags)))
            else:
                raise ValueError("file not found: %s"%fpath)
#    print ("\n".join(pool.map( process_async, pool_srcs)))
def thread_safety(mkPath):
    for compile_args,srcFiles in flags_and_files(mkPath):
        for srcPath in srcFiles:
            fpath = os.path.abspath(os.path.join(mkPath, srcPath))
            if os.path.exists(fpath):
                print ("processing: %s"%os.path.abspath(fpath))
                oscmd="clang -c %s %s"%(" ".join(_used_flag(fpath),fpath))
                err=os.system(oscmd)
                if err != 0:
                    print (oscmd)
            else:
                raise ValueError("file not found: %s"%srcPath)

def proc_trigger():
    #do your process here
    pass

#返回节点对应的代码片断
def contentof(node):
    code=read_f(node.location.file.name)
    return code[node.extent.start.offset:node.extent.end.offset]

#检查非本地定义的边量、函数
def ext_declsof(node, start,end):
#     decls=[v.spelling  for v in subnodesof(node, None) if v.kind.name in ['VAR_DECL','PARM_DECL']]
#     print decls
    decls =[]
    offset = node.extent.start.offset
    edecls=None
    for e in subnodesof(node, None):
        print e.location.line,e.type.kind.name,e.spelling,e.kind.name, e.extent.end.offset
        if start >= e.extent.end.offset:
            continue
        if end <= e.extent.start.offset:
            break
        if e.kind.name in ['VAR_DECL']:
            decls.append(e.spelling)
        if not e.kind.name in ['DECL_REF_EXPR','MEMBER_REF_EXPR'] or e.type.kind.name in ['ENUM','FUNCTIONPROTO']:
#             print e.kind.name
            continue
        if offset >= e.extent.end.offset:
            edecls=e
            continue
        offset = e.extent.end.offset
        if e.spelling in decls:
            continue
        if edecls and not edecls.spelling in decls:
            yield edecls
#             print '- :',edecls.spelling, edecls.kind.name
#         print e.spelling, e.location.line, e.kind.name, e.extent.end.offset
        edecls=e
    if edecls and not edecls.spelling in decls:
        yield edecls
#         print '- :',edecls.spelling
#         yield e
def nodepathsof(node, npath=[]):
    npath+=[node.kind.name]
    yield npath
    for c in node.get_children():
        for cpath in nodepathsof(c, npath+[]):
            yield cpath

#解析源代码文件
def nodeof(srcfile, flags):
    if os.path.exists(srcfile):
        _index = clang.cindex.Index.create()
        tu = _index.parse(srcfile, args=flags)
        del _index
#        del tu
        return tu.cursor
    
def nodesof(srcFiles, cFlags):
    for fp in srcFiles:
        _index = clang.cindex.Index.create()
        tu = _index.parse(fp, args=cFlags)
        yield tu.cursor
        del tu
def subnodesof(node, kindslimit=['CLASS_DECL','TRANSLATION_UNIT','FUNCTION_DECL', 'CXX_METHOD', 'UNEXPOSED_DECL'
                                ]):
    for c in node.get_children():
        if kindslimit and not c.kind.name in kindslimit:
            continue
        yield c
        for subc in subnodesof(c, kindslimit):
            yield subc    
def allnodesof(CSrcCompileList, buildpath='./'):
    restorepath= os.path.abspath(os.curdir)
    if os.path.relpath(buildpath, os.curdir) != '.':
        os.chdir(buildpath)

    for flags,objfile,srcfile in CSrcCompileList:
        print srcfile
        yield nodeof(srcfile,flags[11:]+['-c'])
    if os.path.relpath(restorepath, os.curdir) != '.':
        os.chdir(restorepath)

def rescursive_definition(nodes,proc_called=['carplayserver_SetInitMode'], rescursive_max=5):
#     filepaths = []
    proc_found=[]
    cnt = 0
    while len(proc_called) and cnt < rescursive_max:
        cnt += 1
        for node in nodes:
            for c in subnodesof(node):
                if c.spelling in proc_called and 'FUNCTION_DECL' == c.kind.name:
#                     if not c.location.file.name in filepaths:# and c.location.file.name[-4:]=='.cpp':
#                         print c.location.file.name
#                         filepaths.append(c.location.file.name)
                    for b in subnodesof(c, None):
                        if 'DECL_REF_EXPR' == b.kind.name and b.type.kind.name == 'FUNCTIONPROTO':
                            if not b.spelling in proc_called:
                                proc_called.append(b.spelling)
                        elif 'DECL_REF_EXPR' == b.kind.name and 'TYPEDEF' == b.type.kind.name:# and b.spelling =='gInitialModes':
                            print b.kind.name,b.spelling, b.type.kind.name
#                         if 'VAR_DECL' == b.type.kind.name:# and b.type.kind.name == 'FUNCTIONPROTO':
#                             if not b.spelling in proc_called:
#                                 proc_called.append(b.spelling)
                if c.spelling in proc_called:
                    code_piece = contentof(c)
                    if not code_piece in proc_found:
                        if c.is_definition():
                            yield code_piece
                            proc_called.pop(proc_called.index(c.spelling))
                        proc_found.append(code_piece)

def funcnodesof(funcnames, nodes):
    for x in funcnames:
        m = re.search("((?:\w+\:\:)?\w+)\(",x)
        if m:
            x=m.group(1)
    #         continue
    #     else:
    #         if cnt == 0:
    #             break
    #         cnt -= 1
    #     print x
        for node in nodes:
            for c in subnodesof(node, None):
                if c.kind.name == 'CXX_METHOD':
                    cmpname=c.spelling
                    if c.semantic_parent.kind.name == 'CLASS_DECL':
    #                     print c.semantic_parent.kind.name
                        cmpname = c.semantic_parent.spelling+'::'+c.spelling
    #                 print cmpname
                    if x == cmpname:
    #                     print c.semantic_parent.kind.name
                        yield c
#                         print c.spelling
                        break
                elif c.kind.name == 'FUNCTION_DECL':
                    if x == c.spelling:
    #                     print c.semantic_parent.kind.name
#                         print c.spelling
                        yield c
                        break
            else:
                continue
            break
        else:
            print("not found: %s"%x)