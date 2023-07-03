import re, os, popen2

def cc_compile(srcpath, flags):
    compile_cmd="clang -c %s %s"%(flags, srcpath)
    #print compile_cmd
    print srcpath
    child_stdout, child_stdin, child_stderr=popen2.popen3(compile_cmd)
    print ''.join(child_stderr.readlines())
    print
