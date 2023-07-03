import re

WRITE_TO_FILE=True

FUNC_DECL='''((?:\w+\s+){1,2}(?!if|while|for|switch)((?:\w+\:\:)?\w+)\s*\([^\#\;\{\}\(\)]*\)\s*\{(\s*))'''
RET_LINE='''((?<=[\}\;])(\s*)(return\s+\S+\;))'''
IF_BRACKET='''((if)\s*\([^\#\;\{\}]*\)\s*\{(\s*))'''
ELSE_BRACKET='''((else)\s*\{(\s*))'''

PRT_LINE ='''((?<=\t)printf\()'''
INC_INS="""(.*\w+\s*\(.*\)\s*\{)"""

T_DET_PATT = '''(?<!\/\/ )((det\-\>\S+)\=.+(\s*))'''
T_QVNUM_PATT = '''(?<!\/\/ )(\w+\(.*\&(qvnum)\,.+(\s*))'''
T_QVNUM_NMS_PATT = '''(?<!\/\/ )(\w+\(.*\&(qvnumNMS)\W.+(\s*))'''
T_LEVEL_PATT = '''(?<!\/\/ )(\w+\(.*(level)\,.+(\s*))'''
T_TID_PATT = r'((\s*)(\w\S+\.tid)\s*\=.+)'

# ASSIGNMENTS = """(?<!\))(\n\s*)(?!for|while|do|if|tmp|result|switch)((\w+[^\s\(\)\+\-]+)\s*(?<!\=)\=(?!\=)(.+)\;)"""
INC_VSDK='''
#include <include/link_api/system.h>
'''
RELEASE_BUF = '''((\s*)AlgorithmLink_release(Input|Output)Buffer\([^\;]+\;)'''
PROCESS_PROC = '''(Int32\s+AlgorithmLink_(\w+)Process\(void\s*\*\s*\w+\)\s*\{)'''
# ALLOC_MEM = '''((\s*)\S*.+qv_memAlloc\(([^\n\;]+)\)\;)'''
# ALLOC_MEM,ALLOC_DEBUG = '''((\s*)\S*.+qvCreateImage\((.+)\,.+\,.+\)\;)''', r'''\2Vps_printf("DEBUG: alloc at %s %d!!!\\n", __FILE__, __LINE__);\1'''
# ALLOC_MEM,ALLOC_DEBUG = '''((\s*)\S*.+qvCreateImageHeader\((.+)\,.+\,.+\)\;)''', r'''\2Vps_printf("DEBUG: alloc at %s %d!!!\\n", __FILE__, __LINE__);\1'''

ALLOC_MEM = '''((\s*)\S*.+qv_memAlloc\(\s*(\S+)\s*\)\;)'''
ALLOC_DEBUG = r'''\2Vps_printf("DEBUG: alloc at %s %d size=%d!!!\\n", __FILE__, __LINE__, \3);\1'''

def T_assignments(FILE):
    CODE = read_f(FILE)
    CODE = re.subn(INC_INS, r'''
#include <include/link_api/system.h>
\1''', CODE, count=1)[0]
    CODE = re.subn(ASSIGNMENTS, r'''\1Vps_printf("F=%%s L=%%d ADDR=%%p!!!\\n", "%s", __LINE__, &\3);\1\2'''%os.path.basename(FILE), CODE)[0]
    if WRITE_TO_FILE:
        with open(FILE, 'w') as fw: fw.write(CODE); fw.close()
    else:
        print (CODE)
def safe_read(FILE):
    with open(FILE, 'rb') as fb:
        codeb = fb.read()
        fb.close()
        try:
            CODE=codeb.decode("utf8")
        except:
            try:
                CODE=codeb.decode("gbk").encode("utf8").decode("utf8")
            except:
                raise ValueError("can't decode!\n")
        return CODE
def T_TriggerLine(FILE, T_Trigger, T_logline):
    CODE=safe_read(FILE)
    CODE = re.subn(T_Trigger, T_logline, CODE)[0]
    if WRITE_TO_FILE:
        with open(FILE, 'w') as fw: fw.write(CODE); fw.close()
    else:
        print (CODE)
def T_ReleaseBuffer(FILE):
    CODE=safe_read(FILE)
    match = re.search(PROCESS_PROC, CODE)
    if not match:
        return
    NAME = match.group(2)    
    CODE = re.subn(RELEASE_BUF, r'''
#ifdef DEBUG_BUF_RELEASE\2t_start   = Utils_getCurGlobalTimeInMsec();
#endif\1
#ifdef DEBUG_BUF_RELEASE\2Vps_printf("%s\3: frameId = %%d, t_start = %%llu", pSysInBuffer->frameId, t_start);
#endif'''%NAME, CODE)[0]
    CODE = re.subn(PROCESS_PROC, r'''\1
#define DEBUG_BUF_RELEASE    
#ifdef DEBUG_BUF_RELEASE
    uint64_t t_start;
#endif''', CODE)[0]
    if WRITE_TO_FILE:
        with open(FILE, 'w') as fw: fw.write(CODE); fw.close()
    else:
        print (CODE)

C_LINE_TRACE=r'''\1printf("DEBUG: %s %d !!!\\n", __FILE__, __LINE__);\3'''
C_NUM_TRACE=r'''\1Vps_printf("DEBUG: %s %d \2 = %d!!!\\n", __FILE__, __LINE__, \2);\3'''
LINE_TRACE=r'''\1Vps_printf("DEBUG: %s %d !!!\\n", __FILE__, __LINE__);\3'''
LINE_TRACE_NUM=r'''\1Vps_printf("DEBUG: %d \2=%d!!!\\n", __LINE__, \2);\3'''
# LINE_TRACE_NUM=r'''\1Vps_printf("DEBUG: %s %d \2=%d!!!\\n", __FILE__, __LINE__, \2);\3'''
LINE_TRACE_NUM_COND=r'''\1if(\2 > 0) Vps_printf("DEBUG: %s %d \2=%d!!!\\n", __FILE__, __LINE__, \2);\3'''
# LINE_TRACE_TIME=r'''\1Vps_printf("DEBUG: %llu: %s %d !!!\\n", Utils_getCurGlobalTimeInUsec(), __FILE__, __LINE__);\3'''

LINE_TRACE_TIME=r'''\1Vps_printf("DEBUG: %s %d usec = %llu!!!\\n", __FILE__, __LINE__, Utils_getCurGlobalTimeInUsec());\3'''
LINE_TRACE_DELAY37=r'''\1Vps_printf("DEBUG: %s %d !!!\\n", __FILE__, __LINE__);Task_sleep(37);\3'''
LINE_TRACE_DELAY100=r'''\1Vps_printf("DEBUG: %s %d !!!\\n", __FILE__, __LINE__);Task_sleep(100);\3'''
LINE_TRACE_DELAY300=r'''\1Vps_printf("DEBUG: %s %d !!!\\n", __FILE__, __LINE__);Task_sleep(300);\3'''
# LINE_TRACE_DELAY100=r'''\1Vps_printf("DEBUG: %s %d !!!\\n", __FILE__, __LINE__);Task_sleep(100);\3'''
RET_TRACE=r'''\2Vps_printf("DEBUG: %s %d !!!\\n", __FILE__, __LINE__);\1'''
C_RET_TRACE=r'''\2printf("DEBUG: %s %d !!!\\n", __FILE__, __LINE__);\1'''
RET_TRACE_DELAY100=r'''\2Vps_printf("DEBUG: %s %d !!!\\n", __FILE__, __LINE__);Task_sleep(100);\1'''


def T_Branchs(FILE, TRACELINE,TRACE_RET):
    CODE=safe_read(FILE)
    CODE = re.subn(INC_INS, r'''
//#include <include/link_api/system.h>
\1''', CODE, count=1)[0]
#    TRACELINE = TRACELINE.replace("__FILE__", '"%s"'%os.path.basename(FILE))
#    TRACE_RET = TRACE_RET.replace("__FILE__", '"%s"'%os.path.basename(FILE))
#     CODE = re.subn(FUNC_DECL, r'''\1Vps_printf("DEBUG: \2 called, ProcId = %d !!!\\n", System_getSelfProcId());\3''', CODE)[0]
    CODE = re.subn(FUNC_DECL, TRACELINE, CODE)[0]
    CODE = re.subn(RET_LINE, TRACE_RET, CODE)[0]
    CODE = re.subn(IF_BRACKET, TRACELINE, CODE)[0]
    CODE = re.subn(ELSE_BRACKET, TRACELINE, CODE)[0]
    if WRITE_TO_FILE:
        with open(FILE, 'w') as fw: fw.write(CODE); fw.close()
    else:
        print (CODE)
