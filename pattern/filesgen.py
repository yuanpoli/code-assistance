import os
import re
import json
import pandas as pd
import difflib


T_LINE_PATT = re.compile(
    '''
    (?P<date>\w\w\w\s+\d+)
    \s+(?P<clock>\d\d:\d\d:\d\d)
    \s+G5
    \s+(?P<module>\S+)
    \s+(?P<pn>\w+)\:
    (?:\s+\[[^\]]*\])?
    (?:\s+TID\s=\s(?P<tid>.?\d+))?
    (?:\s+TICK=(?P<tick>\d+))?
    (?:\s*(?P<index>\$\d+\s+\:))?
    \s+(?P<any>(?:
        (?P<act>malloc|free)\s+addr\s+\=\s+(?P<addr>0x[a-f0-9]+))?
        .*)
    ''',
       re.VERBOSE
)

columns = ['clock','pn','module','tid','tick','index','any']
def test_samples():
    if (
        not re.match(T_LINE_PATT, "Sep 30 10:44:42 G5 user.debug carplayservice: TID = 2832954448 TICK=73412$246055151 : getAudioTypeFlag(me->audio_type)")
        or not re.match(T_LINE_PATT, "Jan  1 08:00:01 G5 user.warn kernel: [    0.452711] $1312224434 : ipv6_offload_init")
        or not re.match(T_LINE_PATT, "Sep 30 10:44:45 G5 daemon.debug mDNSResponder: TID = 0 TICK=20000$2073585800 : AnyLocalRecordReady")
        or not re.match(T_LINE_PATT, "Sep 30 10:44:45 G5 daemon.err mDNSResponder: mDNSPlatformSendUDP got error 99 (Cannot assign requested address) sending packet to FF02:0000:0000:0000:0000:0000:0000:00FB on interface FE80:0000:0000:0000:7C11:59FF:FEC9:B37E/usb0/4")
        ):
        raise ValueError("regular pattern for pick data not match!")

#read trace line as records
def read_trace(tpath):
    tfs = [fn for fn in os.listdir(tpath) if fn == 'messages' or fn == 'messages.0']
    tfs.sort()
    tfs.reverse()
    tcode=''
    for fn in tfs:
        fp=open(os.path.join(tpath,fn)); tcode+=fp.read(); fp.close();del fp;
    for line in re.finditer(T_LINE_PATT, tcode):
        yield line.groupdict()
        

#read diction of trace data
def pdfrm_read(tpath):
    return pd.DataFrame(read_trace(tpath))

#create process filter
def pdfrm_filter(pdfrm):
    return (
    (pdfrm['pn']=='ipodservice')
    |(pdfrm['pn']=='carplayservice')
    |(pdfrm['pn']=='mDNSResponder')
)
#count all traced threads for process
def pdfrm_counts(pdfrm, coln='tid'):
    return pdfrm[pdfrm_filter(pdfrm)][columns][coln].value_counts(normalize=False)

#filter trace of one thread
def pdfrm_thread(pdfrm, tidframe, clns):
    tid = tidframe['tid'].values[0]
    return pdfrm[pdfrm['tid'] == tid][clns]

#filtering last trace line of threads
def pdfrm_last_trace(pdfrm, coln='tid'):
    proc_tid_cnts = pdfrm_counts(pdfrm)
    last_trace_lines=pd.DataFrame(columns=pdfrm.columns)
    for tid in proc_tid_cnts.index:
        tpd = pdfrm[pdfrm.index == pdfrm[pdfrm[coln] == tid].index[-1]]
        last_trace_lines = last_trace_lines.append(tpd)
    last_trace_lines = last_trace_lines.sort_index()
    return last_trace_lines
def pdfrm_ratio(pdlcmp, pdlchk, rate=0.01):
    sm = difflib.SequenceMatcher()
    cmp_ths = pdfrm_last_trace(pdlcmp)
    chk_ths = pdfrm_last_trace(pdlchk)
    for idx_a in cmp_ths.index:
        for idx_b in chk_ths.index:
            sm.set_seqs(
                pdlchk[pdlchk['tid'] == pdlchk['tid'][idx_b]]['any'].values,
                pdlcmp[pdlcmp['tid'] == pdlcmp['tid'][idx_a]]['any'].values
            )
            if sm.ratio() >= rate:
                yield idx_a, idx_b, pdlcmp['tid'][idx_a], pdlchk['tid'][idx_b], sm.ratio()
