#coding=utf8
import re

def decl_mfunc_nodes(node, extpatt):
    for f in node.get_children():
#         print f.location.file.name, f.spelling
        if f.kind.name == 'FUNCTION_DECL' or f.kind.name == 'CXX_METHOD':
#             print f.location.file.name, f.spelling
            if re.search(extpatt,f.location.file.name):
#                 print f.location.file.name, f.spelling
                yield f
def hdecl_nodes(node):
    for c in decl_mfunc_nodes(node, "\.h$|\.hpp$"):
        yield c
def cdecl_nodes(node):
    for c in decl_mfunc_nodes(node, "\.c$|\.cpp$|\.h$"):
        yield c
def code_clean_parts(code, clean_patt):
    clean_lines=list(re.finditer(clean_patt,code))
    for line in clean_lines:
        yield line.start(), line.end(), ''
        
def method_nodes(node):
    for f in node.get_children():
        if f.kind.name == 'CXX_METHOD':
            yield f
def func_nodes(node):
    for f in node.get_children():
        if f.kind.name == 'FUNCTION_DECL':
            yield f
def call_exprs(node):
    for f in node.get_children():
        if f.kind.name == 'CALL_EXPR':
            yield f
        else:
            for result in call_exprs(f):
                yield result
def var_ref_exprs(node):
    for c in node.get_children():
#         print c.kind.name,c.displayname
        if (
            (c.kind.name == 'MEMBER_REF_EXPR' and c.referenced.semantic_parent.kind.name == 'CLASS_DECL' and c.referenced.kind.name == 'FIELD_DECL')
            or ( c.kind.name == 'DECL_REF_EXPR' and c.referenced.semantic_parent.kind.name == 'TRANSLATION_UNIT' and c.referenced.kind.name == 'VAR_DECL')
            ):
#             print c.referenced.semantic_parent.kind.name, c.referenced.kind.name, c.displayname
            yield c
        else:
            for result in var_ref_exprs(c):
                yield result

def cc_branch_reflections(process_trigger, process_paras):
    return {
    #遇到函数，进入待触发状态
    'FUNCTION_DECL':{
        #遇到第一个复合语句（括弧），触发添加跟踪信息
        'COMPOUND_STMT':[process_trigger, process_paras],
#         'CALL_EXPR':[process_trigger],
        'IF_STMT':{
            'COMPOUND_STMT':[process_trigger],
            #第二级条件语句，仍然待触发
            'IF_STMT':{
               'COMPOUND_STMT':[process_trigger],
                'IF_STMT':{
                    'COMPOUND_STMT':[process_trigger],
                     'IF_STMT':{
                          'COMPOUND_STMT':[process_trigger],
                     },
                },
            },
        },
        #遇到 while 语句，使用空字典避免在 while 语句中加代码
        'WHILE_STMT':{
#             'IF_STMT':{
#                 'COMPOUND_STMT':[process_trigger],
#                 'IF_STMT':{
# #                     'COMPOUND_STMT':[process_trigger],
#                 },
#             },
        },
    },
    #遇到函数，进入待触发状态
    'CXX_METHOD':{
        #遇到第一个复合语句（括弧），触发添加跟踪信息
        'COMPOUND_STMT':[process_trigger, process_paras],
#         'CALL_EXPR':[process_trigger],
        'IF_STMT':{
            'COMPOUND_STMT':[process_trigger],
            #第二级条件语句，仍然待触发
            'IF_STMT':{
                'COMPOUND_STMT':[process_trigger],
                'IF_STMT':{
                    'COMPOUND_STMT':[process_trigger],
                     'IF_STMT':{
                          'COMPOUND_STMT':[process_trigger],
                     },
                },
            },
        },
        #遇到 while 语句，使用空字典避免在 while 语句中加代码
        'WHILE_STMT':{
#             'IF_STMT':{
#                 'COMPOUND_STMT':[process_trigger],
#                 'IF_STMT':{
# #                     'COMPOUND_STMT':[process_trigger],
#                 },
#             },
        },
    },
}
