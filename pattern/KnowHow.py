#coding=utf8
#######################################################
#
# KnowHow.py
# Python implementation of the Class KnowHow
# Original author: LiFang
#
#######################################################
import os
import re
import json
from pattern.codefiles import read_b,read_f, write_f, filesof, foldersof
from pattern.infoenv import runcmd
#from pattern.codeform import nodesof,subnodesof

class KnowHow(object):
    """ store useful objects for knowlege	"""
    P_INCCFG="\.c$|\.h$|\.txt$|\.MK$|\.mk$"
    dumpfile="./knowhow/KnowHow.yaml"
    Prms = {}
    Vals={}
    def __init__(self, srcpath, P_INCCFG=r"\.c$|\.h$|\.txt$|\.MK$|\.mk$"):
        setattr(self, 'srcpath', srcpath)
        self.VSDK_ROOT = re.search("(.+\w+)(?=[\/\\\\]vision_sdk)", srcpath).group(1)
        self.VSDK_UCGEN = "%s/vision_sdk/tools/vision_sdk_usecase_gen/bin/vsdk_linux.out"%self.VSDK_ROOT
        if not os.path.isfile(self.VSDK_UCGEN):
            self.VSDK_UCGEN = "%s/vision_sdk/apps/tools/vision_sdk_usecase_gen/bin/vsdk_linux.out"%self.VSDK_ROOT
    def load_files(self):
        for filepath in filesof(self.srcpath, self.P_INCCFG):
            name, ext = os.path.splitext(os.path.basename(filepath))
            name += ext.replace('.', '_')
            rpl = re.search(r"chains(\_[A-Za-z0-9]+)\_.+", name)
            if rpl:
                name = name.replace(rpl.group(1), "")
            setattr(self, name, filepath)
            # code = read_f(filepath)
            setattr(self, 'code_' + name, read_b(filepath).decode("gbk").encode("utf8").decode("utf8"))
    def gen_chains_txt(self, chains_txt):
        self.chains_txt = re.search("UseCase\s*\:\s*(\w+)", chains_txt).group(1)+'.txt'
        self.chains_txt = os.path.join(self.srcpath, self.chains_txt)
        write_f(self.chains_txt, chains_txt)
        return read_f(self.chains_txt)
    def gen_priv_files(self):
        print(runcmd("""
            %s -file -img %s -path %s"""%(
                self.VSDK_UCGEN,
                self.chains_txt,
                self.srcpath
            )
        ))
        self.load_files()
    def gen_cfg_mk(self):
        self.cfg_mk = os.path.join(self.srcpath, 'cfg.mk')
        self.Algs = list(set((alg,name) for alg,name in re.findall("(Alg\_)(\w+)",read_f(self.chains_img_txt))))
        self.Algs.sort()
        self.Cores = list(set(re.findall("([A-Z]+\d(?:\_\d)?)\_\d\s",read_f(self.chains_img_txt))))
        self.Cores.sort()
        self.Cores.reverse()
        code =('\n'.join("%s%s=yes"%(alg.upper(),name.lower()) for alg,name in self.Algs if name !="ObjectDraw")
              +"\n\n"+'\n'.join("NEED_PROC_%s=yes"%core for core in self.Cores))
        write_f(self.cfg_mk, code)
        self.load_files()
        return read_f(self.cfg_mk)
    def gen_src_mk(self):
        self.SRC_FILES_MK = os.path.join(self.srcpath, 'SRC_FILES.MK')
        srcfiles=list(filesof(self.srcpath, '\.c$|\.k$'))
        srcfiles.sort()
        srcfiles.reverse()
        write_f(
            self.SRC_FILES_MK, """
SRCDIR += $(vision_sdk_PATH)%s

SRCS_$(IPU_PRIMARY_CORE) += \\
"""%os.path.abspath(self.srcpath)[self.srcpath.find("/examples"):]+' \\\n'.join("""\t\t%s"""%os.path.basename(fp) for fp in srcfiles)+"\n\n"
        )
        self.load_files()
        return read_f(self.SRC_FILES_MK)
    def gen_plg_src_mk(self, support_cores=[
            'dsp_1',
            'dsp_2',
            'arp32_1',
            'ipu0',
            'ipu1'
#            'SRCS_ASM_a15_0',
        ]):
        
        for any_srcpath in list(foldersof(self.srcpath))+[self.srcpath]:
            SRC_FILES_MK = os.path.join(any_srcpath, 'SRC_FILES.MK')
            if any_srcpath == self.srcpath:
                self.SRC_FILES_MK = SRC_FILES_MK
            srcfiles=list(fp for fp in filesof(any_srcpath, '\.c$|\.k$|\.cpp$') if os.path.dirname(fp) == any_srcpath)
            print (any_srcpath)
            print (len(srcfiles))
            if len(srcfiles) == 0:
                continue
            srcfiles.sort()
            srcfiles.reverse()
            core_mk={}
            #确认.k文件
            core_mk.update({'SRCS_K_arp32_0':[fp 
                                              for fp in srcfiles 
                                              if os.path.splitext(fp)[1]=='.k']})
            #设定.k文件所在目录，其下所有c代码运行于eve框架
            k_paths= list(set(os.path.dirname(fp) 
                              for fp in core_mk['SRCS_K_arp32_0']))
            core_mk.update({'SRCS_arp32_0':[fp 
                                            for fp in srcfiles 
                                            if os.path.dirname(fp) in k_paths 
                                            and os.path.splitext(fp)[1]=='.c']})
            #设定非.k文件所在目录，其下所有c代码运行于dsp框架,可选如：SRCS_a15_0, SRCS_ipu1_1,SRCS_COMMON
            core_mk.update({'SRCS_c66xdsp_0':[fp 
                                              for fp in srcfiles 
                                              if os.path.splitext(fp)[1]=='.c' 
                                              and not os.path.dirname(fp) in k_paths]})
            #设定非.k文件所在目录，其下所有cpp代码运行于common框架, 其他可选如：SRCS_CPP_a15_0， SRCS_CPP_c66xdsp_0
            core_mk.update({'SRCS_CPP_COMMON':[fp 
                                               for fp in srcfiles 
                                               if os.path.splitext(fp)[1]=='.cpp' 
                                               and not os.path.dirname(fp) in k_paths]})

            #整理文件对应运行的核
            #可选如：'SRCS_arp32_1','SRCS_arp32_2', 'SRCS_arp32_3','SRCS_arp32_4',
            if 'arp32_1' in support_cores:
                core_mk.update({'SRCS_arp32_1':core_mk['SRCS_arp32_0']})
                core_mk.update({'SRCS_K_arp32_1':core_mk['SRCS_K_arp32_0']})
            #可选如：SRCS_c66xdsp_1, SRCS_c66xdsp_2
            if 'dsp_1' in support_cores:
                core_mk.update({'SRCS_c66xdsp_1':core_mk['SRCS_c66xdsp_0']})
            if 'dsp_2' in support_cores:
                core_mk.update({'SRCS_c66xdsp_2':core_mk['SRCS_c66xdsp_0']})
            if 'ipu0' in support_cores:
                core_mk.update({'SRCS_ipu0_0':core_mk['SRCS_c66xdsp_0']})
            if 'ipu1' in support_cores:
                core_mk.update({'SRCS_ipu1_0':core_mk['SRCS_c66xdsp_0']})
            del core_mk['SRCS_arp32_0']
            del core_mk['SRCS_K_arp32_0']
            del core_mk['SRCS_c66xdsp_0']
            core_keys = list(core_mk.keys())
            core_keys.sort()
            #os.path.relpath(any_srcpath, os.path.dirname(self.srcpath))
            write_f(
                SRC_FILES_MK, """
SRCDIR += $(vision_sdk_PATH)%s
    """%os.path.abspath(any_srcpath)[any_srcpath.find("/examples"):]+''.join(
                    """
%s += \\
%s
    """%(
            core,
            ' \\\n'.join("""\t\t%s"""%os.path.relpath(
                                os.path.abspath(fp), any_srcpath) for fp in core_mk[core])
        )
            for core in core_keys if len(core_mk[core]))
            )
            self.load_files()
            print (SRC_FILES_MK)
            print (read_f(SRC_FILES_MK))
        return

    def load_setfuncs(self):
        """ store calls for SetPrms"""
        matched = re.search(r"(.+examples\/tda\w+\/src)\/usecases", self.srcpath)
        if matched != None:# and len(self.Prms) == 0
            srcpath = matched.group(1)
            self.Vals['#define']=[]
            self.Vals['=']=[]
            return [(codepath, func, body)
            for codepath in filesof(srcpath, r"chains\_.+\.c$")
                for func, body in self.find_setprms(codepath)
                    for alg,name in self.Algs
                        if func.find("Set"+name)!= -1
            ]               
        return []
    def load_setprms(self):
        """ store calls for SetPrms"""
        matched = re.search(r"(.+examples\/tda\w+\/src)\/usecases", self.srcpath)
        if matched != None:# and len(self.Prms) == 0
            srcpath = matched.group(1)
            self.Vals['#define']=[]
            self.Vals['=']=[]
            for codepath in filesof(srcpath, r"chains\_.+\.c$"):
                for func, body in self.find_setprms(codepath):
                    for alg,name in self.Algs:
                        if func.find("Set"+name)!= -1:
                            self.Prms[func] = body

    def find_setprms(self, codepath):
        code = read_f(codepath)
        """find functions for Set Prms"""
        for k,v in re.findall("\#define\s+([A-Z]\w+)\s+(.+)", code):
            self.Vals['#define'].append((k, v))
        for k,v in re.findall("(<!\".+)\s+([A-Z]\w+)\s*\=\s*(.+)", code):
            self.Vals['='].append(k, v)
               
        for matched in re.finditer(r"\w+\s+(.*Prm)\s*\([^\{\}]+\)\s*\{", code):
            begin, end = matched.span()
            end += re.search(r"\n\}", code[end:]).end()
            yield matched.group(1), code[begin:end]

    def find_assigns(self, make_info, KINDS=['UNEXPOSED_EXPR', 'MEMBER_REF_EXPR', 'DECL_REF_EXPR'], SPELL_HAS='Set'):
        for fp in set(cp for cp, fc, bd in self.load_setfuncs()):
            if fp in make_info:
                for node in nodesof([fp], make_info[fp]):
                    code= read_f(fp)
                    for subn in subnodesof(
                        node, 
                        kindslimit=None#['CLASS_DECL','TRANSLATION_UNIT','FUNCTION_DECL', 'CXX_METHOD', 'UNEXPOSED_DECL']
                    ):
                        if subn.location.file == None:
                            continue
                        if subn.location.file.name.find(fp) !=-1 and subn.kind.name in KINDS:
                            if re.search(SPELL_HAS, subn.spelling)!=None:
                                # print subn.kind.name
                                print (code[subn.extent.start.offset:subn.extent.end.offset])
                                pass
                            decln = subn.type.get_declaration()
                            if decln.location.file==None:
                                continue
                            dcode = read_f(decln.location.file.name)
                            #print dcode[decln.extent.start.offset:decln.extent.end.offset]
            else:
                raise ValueError("file not build %s"%fp)
        
    def dump(self):
        write_f(self.dumpfile, json.dumps(self.Prms, indent=4))