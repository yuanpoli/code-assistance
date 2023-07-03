import re
import difflib
import subprocess as sbp
def mapall(pairPattern, d):
    if type(d) == type(""):
        return {
            item.group(1):item.group(2)
            for item in re.finditer(pairPattern, d)           
        }
    elif type(d) == type({}):
        return {
            k:mapall(pairPattern, d[k])
            for k in d}

def close_matchesof(words, selections, w_cutoff=0.2):
    for w in words:
        clm=difflib.get_close_matches(
            [w]+re.split("(0x[A-F0-9]|[A-Z][a-z]+)",w)
            ,[
                [cw]+re.split("\sE[A-Z]\_|(0x[A-F0-9])|([A-Z][a-z]+)", cw) for cw in selections
            ]
            ,n=1
            , cutoff=w_cutoff)
        if len(clm):
            yield w,clm[0][0]
        else:
            yield w,None
def runcmd(cmds):
    p=sbp.Popen(cmds,shell=True, stdout=sbp.PIPE, stderr=sbp.PIPE)
    err = ''.join(p.communicate())
    p.wait()
    del p
    return err
#split a c source file by re patterns
def split_f(pattA, pattB):
    pass
def comment_lines(code, patt):
    mklines=list(re.finditer(patt , code))
    mklines.reverse()
    for ml in mklines:
        code=code[:ml.start()]+"//"+ml.group(0)+code[ml.start():]
    return code
