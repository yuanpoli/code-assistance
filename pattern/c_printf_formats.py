general_para_formats={
    'BOOL': '%d',
    'CHAR_S': '%s',
    'ENUM': '%d',
    'INT': '%i',
    'POINTER': '%p',
    'RECORD': '%p',
    'SCHAR': '%s',
    'UCHAR': '%hhu',
    'UINT': '%u',
    'ULONG': '%lu',
    'USHORT': '%hu'
}
svp_service_formats={
    'string':'%s',
#    'const string':'%s',
#    'const std::string':'%s',
    'SVPString':'%s',
    'struct libusb_context': '%p',
    'struct libusb_device': '%p'
}
svp_service_formats.update(general_para_formats)
