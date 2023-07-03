import json
import re 
#from c_files import *
from codefiles import *
import sys,os

wordsMap = {
   # "MaxNumberof":"Max",
    "Retransmission":"Retrans",
    'Retransmissions':'Retranss',
    "Acknowledgements":"Ack",
    "Information": "Info", 
    "Group": "Grp", 
    "Network": "Net", 
    "Accelerometer": "Accele", 
    "Keyboard": "Keyb", 
    "Firmware": "Firm", 
    "library": "lib", 
    "Authentication": "Auth", 
    "Version": "Ver", 
    "Identification": "Ident", 
    "Identificationinformation": "IdtInfo", 
    "Assistive": "Assist", 
    "Milliseconds": "Millisec", 
    "Messages": "Msgs", 
    "Identifer": "Id", 
    "Bluetoothcomponentinformation": "Btcompinfo", 
    "Component": "Comp", 
    "Accessory": "Acce", 
    "Connected": "Conn", 
    "External": "Ext", 
    "Address": "Addr", 
    "Report": "Rep", 
    "Configuration": "Config", 
    "Response": "Resp", 
    "Advanced": "Adv", 
    "Received": "Recv", 
    "Function": "Func", 
    "Language": "Lang", 
    "Positioning": "Pos", 
    "Identifiers": "Ids", 
    "Request": "Req", 
    "Maximum": "Max", 
    "Profiles": "Profs", 
    "Device": "Dev", 
    "Descriptor": "Desc", 
    "Connection": "Conn", 
    "Playback": "Play", 
    "Attributes": "Attr", 
    "Distribution": "Distrib", 
    "Identifier": "Id", 
    "Supportsi": "Supp", 
    "Delete": "Del", 
    "Control": "Ctrl", 
    "Selection": "Sel", 
    "Battery": "Batt", 
    "Number": "Num", 
    "Library": "Lib", 
    "Bluetooth": "Bt", 
    "Hardware": "Hw", 
    "Telephony": "Tele", 
    "Minimum": "Min", 
    "Registration": "Reg", 
    "Duration": "Dur", 
    "Message": "Msg", 
    "Transport": "Trans"
}
         
REGMAP = dict(
RegTabForAll = [
                         ('USBAudio', ("0xDA", ),),
                         ('ExtAProtocol', ("0xEA", ),),
                         ('PowerUpdate', ("0xAE", ),),
                         ('BluetoothConn', ("0x4E", ),),
                         ('WiFiInfo', ("0x57", ),),
                         ('LocationInfo', ("0xFF", ),),
                         ('VoiceOver', ("0x56", ),),
                         ('Telephony', ("0x41", ),),
                         ('iPodPlaying', ("0x50","0x4C", ),),
                         ('HIDReport', ("0x68", ),),
                         ('AssistiveTouch', ("0x54", ),),
                         ('Identification', ("0x1D", ),),
                         ('Authentication', ("0xAA", ),),
],
RegTabForTouch=[
                         #('USBAudio', ("0xDA", ),),
                         #('ExtAProtocol', ("0xEA", ),),
                         #('PowerUpdate', ("0xAE", ),),
                         #('BluetoothConn', ("0x4E", ),),
                         #('WiFiInfo', ("0x57", ),),
                         #('LocationInfo', ("0xFF", ),),
                         #('VoiceOver', ("0x56", ),),
                         #('Telephony', ("0x41", ),),
                         #('iPodPlaying', ("0x50","0x4C", ),),
                         ('HIDReport', ("0x68", ),),
                         ('AssistiveTouch', ("0x54", ),),
                         ('Identification', ("0x1D", ),),
                         ('Authentication', ("0xAA", ),),
                         ],
RegTabForMedia = [
                         ('USBAudio', ("0xDA", ),),
                         #('ExtAProtocol', ("0xEA", ),),
                         #('PowerUpdate', ("0xAE", ),),
                         ('BluetoothConn', ("0x4E", ),),
                         #('WiFiInfo', ("0x57", ),),
                         #('LocationInfo', ("0xFF", ),),
                         #('VoiceOver', ("0x56", ),),
                         #('Telephony', ("0x41", ),),
                         ('iPodPlaying', ("0x50","0x4C", ),),
                         #('HIDReport', ("0x68", ),),
                         #('AssistiveTouch', ("0x54", ),),
                         ('Identification', ("0x1D", ),),
                         ('Authentication', ("0xAA", ),),
                         ]
               )

def shortN(token):
    for w in re.split('([A-Z][a-z]+)',token):
        if len(w.strip()) and not w in wordsMap:
            wordsMap.setdefault(w,w)
        if w in wordsMap:
            yield wordsMap[w]
        else:
            yield w

class Token():
    def __init__(self, text):
        name = ''.join(re.split('\W+', text))
        if re.match('[A-Z]\w+',name):
            self.name = name
        else:
            raise ValueError("Not valid for token!") 
    def Intersection(self, token):
        pass

def basePTN(item):
    return item[2]+(re.findall('uint(\d+)',item[4])+[{1:'8',0:''}[int(item[2]=='blob')]])[0]

def paraLVN(item):
    itemName,itemValue,itemType,itemMul,itemNote=item
    itemName = ''.join(re.split(' ', itemName))
    words = [w for w in re.split('([A-Z]+)',
                                 ''.join(shortN(itemName))
                                 ) if len(w.strip())]
    return ''.join([words[0].lower()]+words[1:])
def msgIDN(groupName, sourceName):
    return 'ID%s_%s'%(sourceName[0:1],''.join(shortN(groupName)))
def paraIDN(item):
    itemName = item['Name']
    itemValue = item['ID']
    itemType = item['Type']
    return 'ID_'+''.join(shortN(''.join(re.split('\W',itemName))))+'_'+itemType[:1]+itemValue

def paraIDV(item):
    return '0x%04X'%int(item[1])

def enumDFN(groupName):
    return "E_%s"%groupName
def enumIDN(item,groupName):
    print item
    if 'Description' in item:
        itemName = item['Description']
    else:
        itemName = item['Meaning']
    itemValue = item['Value']
    itemN = ''.join(re.split('\W',itemName))
    if(len(itemName) > 64):
        itemN=''.join([w.capitalize() for w in re.findall("\w+", itemName,) if w in ['will','may','not','prompt','and','but','Find','App']])
    return 'E%s_'%''.join(re.findall('[A-Z]',groupName))[-1:]+itemN+'_'+itemValue.replace('0x','')
def enumIDV(itemValue,tableType):
    if tableType=='msgName' or tableType=='grpName':
#         raise ValueError("ok")
        return '0x%04X'%int(itemValue)
    else:
        return '0x%02X'%int(itemValue)

def recMN(groupName, tableType):
    return "m_%s"%(
                          ''.join(w.lower() for w in re.findall("([A-Z])[a-z]+",groupVTN(groupName, tableType)[:-2]) if len(w))
                          )
def defaultSize(item):
    return "%sSize"%item[0]
def defaultV(item,groupName, tableType):
    if item[2] == 'utf8':
        return '"%s"'%item[0]
    if item[2] == 'blob':
        return "{}"
    if item[2] == 'group':
        return recMN(groupName, tableType)
    return "0"
def groupLVN(groupName, tableType):
    return ''.join(re.findall('[A-Z]', groupName)).lower()+'_'+hex(hash(groupName))[-1:]
def groupVTN(groupName, tableType):
    return ''.join(shortN('%s%s_t'%(groupName, tableType.capitalize())))
def paraLTN(item,sourceName):
    itemName,itemValue,itemType,itemMul,itemNote=item
    if not itemType  in ['enum', 'Traits', 'group']:
        return '%s_t'%basePTN(item)
    linkTitle = re.search('Table\s+(\d+[-]\d+)',item[4])
    if linkTitle == None:
        raise ValueError('link table not found for: %s\n'%item[0])
    for linkT in tables:
        cmpTitle = re.search('Table\s+(\d+[-]\d+)\s+(\w+)', linkT[0])
        if cmpTitle == None or cmpTitle.group(1) != linkTitle.group(1):
            continue
        itemName = cmpTitle.group(2)
    if itemType == 'group':
        return '%s'%groupVTN(itemName, sourceName)
    return "%s_t"%''.join(re.split('\s+',itemName))

def paraCPTN(item,sourceName):
    itemName,itemValue,itemType,itemMul,itemNote=item
    if itemType  in ['utf8', 'blob']:
        return paraLTN(item,sourceName).capitalize()
    return paraLTN(item,sourceName)

def groupCBKN(groupName):
    return groupName
def linkTGN(item):
    return ''.join(
                   re.search('Table\s+\d+[-]\d+\s+(\w+)', linkT[0]).group(1)
                   for linkT in linkTable(item))
                
def inputParas(item):
    if item[2]=='none':
        return ''
    if item[2]=='utf8':
        return ', &msg->'+paraLVN(item)
    elif item[2]=='blob':
        return ', &msg->'+paraLVN(item)
    else:
        return ', &msg->'+paraLVN(item)
def memParas(item):
    if item[2]=='none':
        return ''
    if item[2]=='utf8':
        return ', &m_'+paraLVN(item)
    elif item[2]=='blob':
        return ', &m_'+paraLVN(item)
    else:
        return ', &m_'+paraLVN(item)
def cbkLVN(className):
    return className.lower( )+'Cbk'
def codecTBN(className, itemName):
    return "%s_%s"%(className, itemName)
def codecDECN(className, itemName):
    return "uint8_t Set%s_%s(uint8_t  * field, void * vdata)"%(className, itemName)
def indexION(tableType,className,groupName):
    return "AID_%s"%hex(hash(tableType+className+groupName))[-4:].upper()
def arrayION(tableType,className,groupName):
    return "array_%s"%hex(hash(tableType+className+groupName))[-4:].upper()
# def arrayPLN(tableType,className,groupName):
#     return "array_%s_L"%hex(hash(tableType+className+groupName))[-4:]

def cbkFN(className, groupName,tableType):
    return "uint16_t %s_%s%s(int linkID, const void  * payload)"%(className,groupName,tableType.capitalize())
def cbkFNT0(className, groupName,tableType):
    return "typedef uint16_t (*%s_%s%sCBK)(int linkID)"%(className,groupName,tableType.capitalize(),)
def cbkFNT(className, groupName,tableType):
    return "typedef uint16_t (*%s_%s%sCBK)(int linkID, const %s  * payload)"%(className,groupName,tableType.capitalize(), groupVTN(groupName, tableType))
def cbkImplFNT0(className, groupName,tableType):
    return "uint16_t %s%sResp(int linkID)"%(groupName,tableType.capitalize(),)
def cbkImplFNT(className, groupName,tableType):
    return "uint16_t %s%sResp(int linkID, const %s  * resp)"%(groupName,tableType.capitalize(), groupVTN(groupName, tableType))
def reqFN0(className, groupName,tableType):
    return "uint16_t %s_%s%s(int linkID)"%(className, groupName,tableType.capitalize(), )
def reqFN(className, groupName,tableType):
    return "uint16_t %s_%s%s(int linkID, const %s * input)"%(className, groupName,tableType.capitalize(), groupVTN(groupName, tableType))
def hidFN(className, itemName):
    return "uint8_t iAP2%s_%s(int linkID)"%(className.replace("HID",""), ''.join(re.findall("\w+",itemName)),)
def EnumDef(varName):
    return """
enum E_%s{%s
};
typedef enum E_%s %s_t;
    """%varName
def C_Interface(className,c_code):
    return """
#ifndef _%s_H
#define _%s_H
#ifdef __cplusplus
extern "C" {
#endif
%s
#ifdef __cplusplus
}
#endif
#endif //_%s_H
"""%(
     className.upper(),
     className.upper(),
     c_code,
     className.upper()
     )


# itemMapTypeID = {
#     'blob' : 'BlobTypeIdentifer',
#     'bool' : 'BoolTypeIdentifer',
#     'enum' : 'EnumTypeIdentifer',
#     'group' : 'GroupTypeIdentifer',
#     'none' : 'NoneTypeIdentifer',
#     'uint16' : 'Uint16TypeIdentifer',
#     'uint32' : 'Uint32TypeIdentifer',
#     'uint64' : 'Uint64TypeIdentifer',
#     'uint8' : 'Uint8TypeIdentifer',
#     'utf8' : 'Utf8TypeIdentifer',
# }
itemMapTypeID = {
    'BlobTypeIdentifer' : '0',
    'BoolTypeIdentifer' : '1',
    'EnumTypeIdentifer' : '2',
    'GroupTypeIdentifer' : '3',
    'NoneTypeIdentifer' : '4',
    'Uint16TypeIdentifer' : '5',
    'Uint32TypeIdentifer' : '6',
    'Uint64TypeIdentifer' : '7',
    'Uint8TypeIdentifer' : '8',
    'Utf8TypeIdentifer' : '9',
}
  
# itemMapIDs = [(itemMapTypeID[n],n) for n in itemMapTypeID]
# itemMapIDs.sort()
# print """
# enum iAP2BasicTypeIdentifer{%s
# };
# """%''.join("""
#     ID_%s,"""%(name.replace('Identifer','')) for value,name in itemMapIDs )

ParaType2IDV = {
'blob' : '0',
'bool' : '1',
'enum' : '2',
'group' : '3',
'none' : '4',
'uint16' : '5',
'uint32' : '6',
'uint64' : '7',
'uint8' : '8',
'utf8' : '9',
}
