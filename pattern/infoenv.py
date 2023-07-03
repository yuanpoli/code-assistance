import subprocess as sbp
import re,os
from .codefiles import filesof,read_f,write_f

P_COMPILE_CMDS = "\s*\S+\s+(.+)(\s\-f?c\s.+\.c(?:pp)?)"
P_COMPILE_SRC_FILE = "(\S+\w+\.c(?:pp)?\S*)\s*$"
P_COMPILE_SWITCH = "\-include\s+\".+\"|\-o\s*\S+|\-[A-Za-np-z]\S*"

def runcmd(cmds):
    p=sbp.Popen(cmds,shell=True, stdout=sbp.PIPE, stderr=sbp.PIPE)
    try:
        err = ''.join(res.decode('utf8') for res in p.communicate())
    except:
        err = ''.join(res.decode('cp936') for res in p.communicate())
    p.wait()
    del p
    return err
def grep_code(files, text):
    for fp in files:
        result = runcmd("cat %s |grep %s"%(fp,text))
        if len(result):
            yield fp, result
def cmdsof(make_output):
    return dict(
            (''.join(re.findall(P_COMPILE_SRC_FILE, _compile_files)), re.findall(P_COMPILE_SWITCH, _compile_flags))
            for _compile_flags, _compile_files in re.findall(P_COMPILE_CMDS, make_output)
        )
def cmdsofmake(make_output):
    for _compile_flags, _compile_files in re.findall("\s*\S+\s+(.+)(\s\-o\s.+\.cpp)\n", make_output)+re.findall("\s*\S+\s+(.+)(\s\-o\s.+\.c)\n", make_output):
#         print _compile_flags
#         print _compile_files
#     print ''.join(re.findall("\S+\w+\.c\S*\.o", _compile_files))
#     print ''.join(re.findall("\-c\s+(\S+\w+\.c\S*)", _compile_files))
        yield re.findall("\-\w\S*", _compile_flags),  ''.join(re.findall("\-o\s+(\S+\w+\.\S*\.o)\s", _compile_files)),  ''.join(re.findall("(\S+\w+\.c\S*)\s*$", _compile_files))

def comment_called_line(fn, lineno):
    code = read_f(fn)
    for line in re.finditer(".*\n", code):
        lineno-=1
        if lineno == 0 and not re.match("\/\/.*\n", line.group(0)):
            code = code[:line.start()]+'// '+ code[line.start():]
            print("try comment: %s %s:"%(fn, lineno))
            print(line.group(0))
#            print code
            write_f(fn, code)
            break
def fix_loss_file(err_text, lose_patt, src_dir, dist_dir):
    for m in re.finditer(lose_patt,err_text):
        fn = m.group(4)
        print(fn)
        for fp in filesof(src_dir,"\.c$|\.cpp$|\.h$"):
            fp = os.path.relpath(fp,src_dir)
#             print fp
            if fn in fp:
                cmd =  "cp %s %s -fr"%(os.path.join(src_dir, fp),os.path.join(dist_dir,fp))
                print("try copy file:",cmd)
                if os.system(cmd):
                    print("failed!")
                break
        else:
            fn = m.group(1)
            for fp in filesof(dist_dir,"\.c$|\.cpp$|\.h$"):
                if fn in fp:
                    print(fp,f)
                    comment_called_line(fp, int(m.group(2)))
def fix_loss_incpath(err_text, lose_patt, src_dir):
    for m in re.finditer(lose_patt,err_text):
        fn = m.group(4)
        for fp in filesof(src_dir,"\.c$|\.cpp$|\.h$"):
            if fn in fp:
                print(fp)
        else:
            print("not found: %s!\n"%fn)
def fix_undefined_reference():
    pass
def enter_repo(GITPATH,reponame = None, REPOROOT = "/home/lifang/workspace"):
    if reponame == None:
        reponame = re.search("[\/\\\\]([A-Za-z0-9\_\-]+)\.git",GITPATH).group(1)
    REPOPATH = os.path.join(REPOROOT,reponame)
    if not os.path.abspath(os.curdir) == REPOPATH:
        if not os.path.exists(REPOPATH):
            print(REPOROOT)
            os.chdir(REPOROOT)
            assert(os.path.abspath(os.curdir) == os.path.abspath(REPOROOT))
            print (os.path.abspath(os.curdir))
            CMD = "git clone %s %s"%(GITPATH,reponame)
            print (CMD)
            print (runcmd(CMD))
            print (REPOPATH)
            os.chdir(REPOPATH)
            print (os.path.abspath(os.curdir))
            assert(os.path.abspath(os.curdir) == REPOPATH)
            print (runcmd("git branch"))
    os.chdir(REPOPATH)
    assert(os.path.abspath(os.curdir) == REPOPATH)
USE_OF_UNDECLARED_PATT="use of undeclared identifier\s*[^\w\-\+](.+)\'"     
FILES_NOT_FOUND_ERR_PATT=re.escape("error: 'fieldbase.h' file not found").replace("fieldbase\\.h","(.*)")
NO_SUCH_FILE_ERR_PATT=re.escape("error: no such file or directory: '../")+"(.*)\'"
FATAL_FILE_ERR_PATT=re.escape("feature/iAP2MsgTab.c:5:10: fatal error: 'SVPLog.h' file not found").replace("feature\/iAP2MsgTab\.c","(.+)").replace("SVPLog\\.h","(.+)").replace("\:5","\:(\d+)").replace("\:10","\:(\d+)")

"""
feature/Identification/IdentificationUtilitys.c:(.text+0x7b3): undefined reference to `field_put_none
"""
