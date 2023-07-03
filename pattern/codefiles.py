#coding=utf8
'''
Created on 2014-7-27

@author: weima
'''
import re 
import os
import time
import zipfile as zpf
# from pattern.c_part_log import CP_LOG_PARTS as LOG_PARTS
from difflib import ndiff
from c_syntax import CPP_FILE_EXT,C_SRC_FILE_EXT, CPP_SRC_FILE_EXT, INC_LINE_PATT,STRUCT_PATT

def check_part(part,keyword = 'free'):
    for k in part.groupdict():
        item = part.groupdict()[k]
        if item and item.find(keyword) != -1:
            print(k)


def write_f(fpath, code):
    f = open(fpath,"w", encoding="utf8")
    f.write(code)
    f.close()
    del f
def read_f(fpath):
    f = open(fpath, encoding="utf8")
    #print(fpath)
    code = f.read()
    f.close()
    del f
    return code
def read_b(fpath):
    f=open(fpath, 'rb')
    bytes=bytearray(f.read())
    f.close()
    del f
    return bytes

def read_join(codeFiles, ascending=False):
    if type(codeFiles) != type(''):
        files = list(codeFiles)
        files.sort()
        if not ascending:
            files.reverse()
        return ''.join(read_f(fpath)  for fpath in files)
    elif os.path.isfile(codeFiles):
        return read_f(codeFiles)


def foldersof(src):
    if type(src) == type('') and os.path.exists(src):
        for rd, dl, fl in os.walk(src):
            for dpath in dl:
                yield os.path.join(rd,dpath)
    elif type(src) in [type([]), type(tuple([])), type({})]:
        for path in src:
            foldersof(path)

def rangeof(code, partkey, PATT_PARTS):
    parts = [(part.span(), part) for part in re.finditer(PATT_PARTS, code)
             if partkey == None 
             or part.groupdict()[partkey]  != None]
    parts.sort()
    parts.reverse()
    for sp,part in parts:
#         check_part(part)
        yield part

    
def partsof(src, P=STRUCT_PATT, FTYPE="\.h$"):
    if type(src) == type('') and os.path.exists(src):
        if os.path.isdir(src):
            for fp in filesof(src,FTYPE):
                try:
                    CODE = read_b(fp).decode("utf8")
                except:
                    CODE = read_b(fp).decode("gbk")
                for s,n in re.findall(P, CODE):
                    yield n,s
        if os.path.isfile(src):
            CODE = read_f(src)
            for s,n in re.findall(P, CODE):
                yield n,s
def filesof(src, match = C_SRC_FILE_EXT, exclude = None):
    if type(src) == type('') and os.path.exists(src):
        for rd, dl, fl in os.walk(src):
            for fpath in fl:
                fpath = os.path.normpath(os.path.join(rd,fpath))
                if re.search(match, fpath) and (exclude == None or re.search(exclude, fpath) == None):
                    yield fpath
    elif type(src) in [type([]), type(tuple([])), type({})]:
        for path in src:
            filesof(path)

def pairsof(base_srcpath, change_srcpath, SRC_EXT_PATT = CPP_SRC_FILE_EXT):
    for fa in filesof(base_srcpath, SRC_EXT_PATT):
        for fb in filesof(change_srcpath, SRC_EXT_PATT):
            if os.path.relpath(fa, base_srcpath) == os.path.relpath(fb, change_srcpath):
                yield (fa, fb)

def pairwordsof(codeA, codeB, splitpatt='\n'):
    difflines = re.findall("([+-] .+)", 
                          "\n".join(
                                ndiff(
                                    re.split(splitpatt, codeA),
                                    re.split(splitpatt, codeB),
                                )
                          ))
    for idx in range(len(difflines)-1):
        line_a = difflines[idx]
        line_b = difflines[idx+1]
        if line_a[0]=='-' and line_b[0]=='+':
            yield line_a[2:], line_b[2:]

def wordpairs(codeA, codeB, level=0,split_patt="([A-Z][a-z0-9])"):
    wordpairs = [(a,b)
    for la,lb in pairwordsof(codeA, codeB)
    for a,b in pairwordsof(la,lb,"\_|\W")
    if len(
            set(w for w in re.split(split_patt, a) if len(w) > 0).intersection(
            set(w for w in re.split(split_patt, b) if len(w) > 0))
    ) >= level]
    wpairs = [(len(wa) , wa, wb) for wa,wb in set([
                wp for wp in wordpairs
            ])]
    wpairs.sort()
    wpairs.reverse()
    wpairs = [(wa,wb) for l,wa,wb in wpairs]
    return wpairs

def GenTemplate(code, wkeys, templexpr):
    wkeys = [(len(w), w) for w in wkeys]
    wkeys.sort()
    wkeys.reverse()
    wkeys = [w for l,w in wkeys]
    for w in wkeys:
        if code.find(w)!=-1:
            templexpr[w] = 'MODULE_SYM_%s'%hex(hash(w))[-6:].upper()
#            templexpr[w] = 'MODULE_SYM_%s'%hex(hash(w))[-3:].upper()
            code = code.replace(w, "${%s}"%templexpr[w])
    return code
def C_insert( insertion, front=True ):
    srccode, idx, patt, inscode = insertion
    if front:
        idx = idx+re.search(patt, srccode[idx:]).start()
    else:
        idx = idx+re.search(patt, srccode[idx:]).end()
    srccode = srccode[:idx]+inscode+srccode[idx:]
    return srccode, start
def C_inserts( *control ):
    fpath, write_back = control[0][:2]
    if len(control[0])>2:
        instoend = control[0][2]
    else:
        instoend = False
    code = read_f(fpath)
    idx = 0
    idxs=[]
    for insdesc in control[1:]:
        patt, inscode =insdesc[:2]
        sr = re.search(patt, code[idx:])
        if instoend:
            idxs.append((idx+sr.end(), inscode))
        else:
            idxs.append((idx+sr.start(), inscode))
            if len(insdesc) >2:
                idxs.append((idx+sr.end(), insdesc[2]))
        idx+=sr.end()
    idxs.reverse()
    for idx,inscode in idxs:
        code = code[:idx]+inscode+code[idx:]
    if write_back:
        write_f(control[0][0], code)
    return code
            
def findofname(cmpPath, paths):
    for p in paths:
        if os.path.split(p)[1] ==os.path.split(cmpPath)[1]:
            if os.path.exists(p):
                yield p
                
def findincs(code):
    for relpath in  re.finditer(INC_LINE_PATT, code):
        yield relpath
        
def c_files(path):
    for fpath in filesof(path, C_SRC_FILE_EXT):
        yield fpath
def cpp_files(path):
    for fpath in filesof(path, CPP_FILE_EXT):
        yield fpath

def inc_files(path):
    for rd, dl, fl in os.walk(path):
        for fpath in fl:
            C_SRC_HEADER_EXT = "[.]h$"
            if re.search(C_SRC_HEADER_EXT, fpath):
                yield os.path.join(rd,fpath)

                
def projection_files(path, pattern):
    for fpath in c_files(path):
        print( fpath
)
        
def create_object(hfpath):
    hcode = read_f(hfpath)
    for decl_func in re.finditer(decl_func, hcode):
        print((decl_func.group(0)
))
        
def git_reset(codePath, codeVer):
    if os.path.exists(codePath):
        if 0!=os.system(r"cd %s; git fetch --all; git reset --hard %s"%(codePath, codeVer)):
            raise ValueError("error to reset source code : %s, %s\n"%(codePath, codeVer))
        else:
            print(("%s %s"%(codePath, codeVer)))

def deleteMatched(patt, code):
    delM = re.search(patt, code)
    if delM:
        s,e = delM.span()
        code = code[:s] + code[e:]
    return code

def fileszip(files, targetName='ZipAt'):
    fname = "%s_%s"%(targetName,str(time.ctime()).replace(' ', '_').replace(':','-'))
    z = zpf.ZipFile("./Downloads/%s.zip"%fname,'w')
    for fpath in files:
        if os.path.isfile(fpath):
            z.write(fpath)
    z.close()
