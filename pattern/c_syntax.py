from syntax import *



# print """\n""".join('\"'+p+'\": '+p+',' for p in re.findall('(C\_\w+)\s*\=\s*',  '''
CPP_SRC_FILE_EXT = "\.h$|\.c$|\.cpp$"
CPP_FILE_EXT = "[.]cpp$"
C_SRC_FILE_EXT = "[.]c$|[.]h$"

STRUCT_PATT = "(typedef\s+struct\s*(?:\w+\s*)?\{[^\}]+\}\s*(\w+)\s*\;)"
INC_LINE_PATT = '\#include\s+[\<\"]([^\>\"]+)[\>\"]'

PARTMAP={
    'caseimpl':re.compile('case\s+\w+\:(?:.(?!break\;))+.break\;', re.DOTALL),
    'funcimpl':r"%s\s+%s\s*\([^\(\)\{\}]*\)\s*\{(?:[^\}]|(?<!\n)\})+\n\}"
}
C_SYNTAX_MAP = dict(
            C_keywords = """(?<=\W)(?:struct|void|int|enum|const|static|unsigned|if|while|for|case|switch|__declspec)(?=\W)""",
            C_commentSL = """(?P<commentSL>\/\/.*\n)""",
            C_commentML = """(?P<commentML>\/\*    (?:  [^*]|(\*(?!\/))  )*    \*\/)""",
            C_string ="""(?P<string>\"  (?:  [^"](  (?<=\\\\)\")?  )*  \")""",
            C_char = """(?P<char>\'(?:[^']((?<=\\\\)\')?)*\')""",
            C_include = """(?:^|(?<=\s))(?P<include>\#include\s+["<](?P<incfile>.*)[">].*\n)""",
            C_define = """(?<=\s)(?P<define>\#define[^\n\\\\]*(?:\\\\\\s*[^\n\\\\]*)*\n)""",
            C_cmd_if = """(?<=\s)(?P<cmd_if>\#if[^\n\\\\]*(?:\\\\\\s*[^\n\\\\]*)*\n)""",
            C_refExpr = """(?P<refExpr>(?!${C_keywords})\w+(?:\.\w+|\-\>\w+|\s*\[\s*\w+\s*\])*)""",
            C_ret=""" (?<=\W) (?P<ret>return\s+(.*)\;)""",
            C_switch="""(?<=\W)(?P<switch>(switch)\s*\(?(?P<expr>.*)\)?\s*\{)""",
            C_caseBranch="""(?<=\W)(?P<caseBranch>(?:case|default)\s+(?P<caseExpr>.*)
                \:(?:\s*\{)?
                )""",
            C_ifBranch="""(?<=\W)
                (?P<ifBranch>(?:else\s*if|if)\s*
                    \( (?P<compare>[^{};\(]+|(?<!switch)\() \)
                    \s*\{
                )""",
            C_elseBranch="""(?<=\W)(?P<elseBranch>else\s*
                \{ )""",
            C_cycle="""(?<=\W)(?P<cycle>(?:while|for)\s*
                \(
                (?P<cycleCondition>[^{}]*)
                \)
                \s*\{
                )""",
            C_freeExec = """ (?<=\W) (?P<freeExec>
                free\s*\(\s*(?P<freeAddr>.*)\s*\)\s*\;
                )""",
            C_mallocExec=""" (?<=\W) (?P<mallocExec>
                 (?P<mallocAddr>${C_refExpr})
                 \s*\=\s*(?P<mallocPtType>.*)
                 malloc\s*\(\s*(?P<mallocSize>.+)\s*\)\s*\;
                 )""",
#                     (?P<declsAfterImpl1>
#                         (?:\s*${C_kwds}\s+)?
#                         (?:
#                             (?!${C_kwds})\(?\w+ 
#                             [\*\s\)]+
#                         )+
#                         \w+\s* 
#                         (?:[\[\,\=][^\;]+)?
#                         \;.*\n
#                     )+
            C_declsImpl = """
            (?P<declsImpl>
                (?:
                (?:
                    \(?
                       (?!(?:return|if|while|for))\w+
                       (?:\s*\*+\s*|\s+|\s*\)\s*)
                 )
                )+
                \w+\s*
                (?:[\[\,\=][^\;]+)?
                \;
#                 [^{}\n]*\n
            )
            """,
            C_funcPara = """(?P<funcPara>\(  (?:[^\{\}\;\=\"]+\s+[^\{\}\;\=\"]+|\s*void\s*|\s+)? \) )""",
            C_retType = """(?P<retrunType>\w+  (?:    \s*[<][^\>\{\}]+[>]\s*    |     \s*\*\s*     |     \s+  )   )*""",
            C_funcImpl = """(?<=[\s\/\*\&])(?P<funcImpl>
                   ${C_retType}
                   (?P<funcName>
                       (?P<baseName>(?<!\-\>)(?<!\.)\w+\:\:)?  
                       [~]?(?!${C_keywords})\w+  
                     )\s*
                   ${C_funcPara}
                    (?:
                    |\s+${C_commentSL}
                    |\s+${C_commentML}
                    )    
                    \s*
                    (?:\:[^{]+)?
                    \{
                    )""",
                    
            C_funcImplM = """(?<=[\s\/\*\&])(?P<funcImpl>
                   ${C_retType}
                   (?P<funcName>
                       (?P<baseName>(?<!\-\>)(?<!\.)\w+\:\:)?  
                       [~]?(?!${C_keywords})\w+  
                     )\s*
                   ${C_funcPara}
                    (?:
                    |\s+${C_commentSL}
                    |\s+${C_commentML}
                    )    
                    \s*
                    (?:\:[^{]+)?
                    \{
                    (?:
                        \s*${C_declsImpl}*\s*
#                             |(?:
#                                 \s*\#(?:ifdef|if)\s+.*\n
#                                 ${C_declsImpl}+
#                                 \s*\#endif\s+.*\n
#                              )
                            |\s*${C_commentSL}
                            |\s*${C_commentML}
                        )*
                    )
                    """,
            C_funcDecl="""(?<=\W)(?P<funcDecl>
                   (?P<returnTypeDecl>\w+  (?:    \s*[<][^>]+[>]\s*    |     \s*[*]\s*     |     \s+  )   )?
                   (?P<funcNameDecl>
                       (?P<baseNameDecl>\w+\:\:)?  
                       [~]?\w+  
                     )\s*
                   (?P<funcParaDecl>\(  (?:[^{};=]+\s+[^{};=]+|void)? \) )\s*
                   \;)
            """,
            C_PointerRef = """
                (?P<pointerRef>(?:\*+\s*\w+|\w+\-\>).*
            """
)

# '''))
