"""

 Opcode values in message header. RFC 1035, 1996, 2136.
"""



QUERY = 0
IQUERY = 1
STATUS = 2
NOTIFY = 4
UPDATE = 5

# Construct reverse mapping dictionary

_names = dir()
opcodemap = {}
for _name in _names:
    if _name[0] != '_': opcodemap[eval(_name)] = _name

def opcodestr(opcode):
    if opcodemap.has_key(opcode): return opcodemap[opcode]
    else: return repr(opcode)


