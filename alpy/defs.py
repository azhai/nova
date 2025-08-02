import sys
from enum import IntEnum
from typing import Optional


def fatal(msg: str):
    raise Exception(f"Fatal error: {msg}")


def notice(msg: str):
    print(f"Notice error: {msg}", file=sys.stderr)


def slash_char(c: str) -> str:
    if c == 'a': return '\a'
    if c == 'b': return '\b'
    if c == 'f': return '\f'
    if c == 'n': return '\n'
    if c == 'r': return '\r'
    if c == 't': return '\t'
    if c == 'v': return '\v'
    if c in ['%', '"', '\'', '\\']: return c
    return ''


def quote_char(c: str) -> str:
    if c == '\a': return '\\a'
    if c == '\b': return '\\b'
    if c == '\f': return '\\f'
    if c == '\n': return '\\n'
    if c == '\r': return '\\r'
    if c == '\t': return '\\t'
    if c == '\v': return '\\v'
    if c == '\\': return '\\\\'
    return c


def quote_string(s: str) -> str:
    return "".join([quote_char(c) for c in s])


def read_file(filename: str) -> str:
    """ 读取文件内容 """
    try:
        fh = open(filename, 'r')
        content = fh.read()
        fh.close()
    except FileNotFoundError:
        content = ""
        fatal(f"File not found: {filename}")
    return content


class Output:

    def __init__(self, outfile: str, logfile: str = ""):
        self.out = self.open(outfile) if outfile else sys.stdout
        self.log = self.open(logfile) if logfile else sys.stderr

    @staticmethod
    def open(filename: str):
        """ 打开文件准备写入 """
        try:
            return open(filename, 'w')
        except FileNotFoundError:
            notice(f"File not found: {filename}")
        except IOError as e:
            notice(f"Cannot open file: {e}")
        return None

    def close(self):
        """ 关闭文件 """
        if self.out:
            self.out.close()
        if self.log:
            self.log.close()


class TokenType(IntEnum):
    T_EOF = 0
    T_AND = 1
    T_OR = 2
    T_XOR = 3
    T_EQ = 4
    T_NE = 5
    T_LT = 6
    T_GT = 7
    T_LE = 8
    T_GE = 9
    T_LSHIFT = 10
    T_RSHIFT = 11
    T_PLUS = 12
    T_MINUS = 13
    T_STAR = 14
    T_SLASH = 15
    T_MOD = 16
    T_ASSIGN = 17
    T_INVERT = 18
    T_LOGNOT = 19
    T_LOGAND = 20
    T_LOGOR = 21
    T_VOID = 22
    T_BOOL = 23
    T_INT8 = 24
    T_INT16 = 25
    T_INT32 = 26
    T_INT64 = 27
    T_UINT8 = 28
    T_UINT16 = 29
    T_UINT32 = 30
    T_UINT64 = 31
    T_FLT32 = 32
    T_FLT64 = 33
    T_IF = 34
    T_ELSE = 35
    T_FALSE = 36
    T_FOR = 37
    T_PRINTF = 38
    T_TRUE = 39
    T_WHILE = 40
    T_NUMLIT = 41
    T_STRLIT = 42
    T_SEMI = 43
    T_IDENT = 44
    T_LBRACE = 45
    T_RBRACE = 46
    T_LPAREN = 47
    T_RPAREN = 48
    T_COMMA = 49


class Token:
    def __init__(self, tok_type: TokenType = TokenType.T_EOF):
        self.token: TokenType = tok_type
        self.tok_str: Optional[str] = None
        self.num_type: NumType = NumType.NUM_INT
        self.num_val = 0

    def __str__(self):
        if self.token == TokenType.T_EOF:
            return "EOF"
        elif self.token is TokenType.T_IDENT:
            return f"{self.token.name}({self.tok_str})"
        elif self.token is TokenType.T_STRLIT:
            return "{!s}({!r})".format(self.token.name, self.tok_str)
        elif self.token in (TokenType.T_BOOL, TokenType.T_NUMLIT):
            return f"{self.token.name}({self.num_val})"
        else:
            return f"{self.token.name}"


class TypeKind(IntEnum):
    TY_VOID = 0
    TY_BOOL = 1
    TY_INT8 = 2
    TY_INT16 = 3
    TY_INT32 = 4
    TY_INT64 = 5
    TY_FLT32 = 6
    TY_FLT64 = 7

    TY_UINT8 = 10
    TY_UINT16 = 11
    TY_UINT32 = 12
    TY_UINT64 = 13

    TY_PTR = 16


class DataType:
    def __init__(self, kind: TypeKind, size: int = 0, align: int = 0, is_unsigned: bool = False):
        self.kind = kind
        self.size = size
        self.align = align
        self.is_unsigned = is_unsigned
        self.sibling: Optional[DataType] = None


class NumType(IntEnum):
    NUM_INT = 1
    NUM_UINT = 2
    NUM_FLT = 3
    NUM_CHAR = 4


class Litval:
    def __init__(self):
        self.intval: int = 0
        self.dblval: float = 0.0


class Strlit:
    def __init__(self, val: str, label: int,
                 sibling: Optional['Strlit'] = None):
        self.val = val
        self.label = label
        self.sibling = sibling


class SymType(IntEnum):
    SYM_VAR = 1
    SYM_LOCAL = 2
    SYM_FUNC = 3


class Sym:
    name: str
    sym_type: SymType
    val_type: DataType

    def __init__(self, name: str, sym_type: SymType, val_type: DataType):
        self.name = name
        self.sym_type = sym_type
        self.has_addr: bool = False
        self.type: DataType = val_type
        self.init_val: Litval = Litval()
        self.params = []
        # self.count: int = 0
        # self.memb: Optional[Sym] = None
        # self.sibling: Optional[Sym] = None


class ASTNodeType(IntEnum):
    A_ASSIGN = 1
    A_CAST = 2
    A_ADD = 3
    A_SUBTRACT = 4
    A_MULTIPLY = 5
    A_DIVIDE = 6
    A_NEGATE = 7
    A_EQ = 8
    A_NE = 9
    A_LT = 10
    A_GT = 11
    A_LE = 12
    A_GE = 13
    A_AND = 14
    A_OR = 15
    A_XOR = 16
    A_LSHIFT = 17
    A_RSHIFT = 18
    A_NOT = 19
    A_INVERT = 20
    A_NUMLIT = 21
    A_IDENT = 22
    A_PRINT = 23
    A_GLUE = 24
    A_IF = 25
    A_WHILE = 26
    A_FOR = 27
    A_TYPE = 28
    A_STRLIT = 29
    A_LOCAL = 30
    A_FUNCTION = 31
    A_FUNCCALL = 32
    A_PRINTF = 33
    A_MOD = 34
    A_RETURN = 35
    A_BLOCK = 36


class ASTNode:
    def __init__(self, op: ASTNodeType, left=None, right=None,
                 type: Optional[DataType] = None, sym: Optional[Sym] = None):
        self.op = op
        self.type: Optional[DataType] = type
        self.rvalue: bool = False
        self.left: Optional[ASTNode] = left
        self.mid: Optional[ASTNode] = None
        self.right: Optional[ASTNode] = right
        self.sym: Optional[Sym] = sym
        self.numlit: Litval = Litval()
        self.strlit: Optional[str] = None


# Global type instances
ty_void = DataType(TypeKind.TY_VOID, 1, 1)
ty_bool = DataType(TypeKind.TY_BOOL, 1, 1)
ty_int8 = DataType(TypeKind.TY_INT8, 1, 1)
ty_int16 = DataType(TypeKind.TY_INT16, 2, 2)
ty_int32 = DataType(TypeKind.TY_INT32, 4, 4)
ty_int64 = DataType(TypeKind.TY_INT64, 8, 8)
ty_uint8 = DataType(TypeKind.TY_INT8, 1, 1, is_unsigned=True)
ty_uint16 = DataType(TypeKind.TY_INT16, 2, 2, is_unsigned=True)
ty_uint32 = DataType(TypeKind.TY_INT32, 4, 4, is_unsigned=True)
ty_uint64 = DataType(TypeKind.TY_INT64, 8, 8, is_unsigned=True)
ty_flt32 = DataType(TypeKind.TY_FLT32, 4, 4)
ty_flt64 = DataType(TypeKind.TY_FLT64, 8, 8)


def get_ast_type(kind: TypeKind, is_unsigned: bool = False) -> DataType:
    if kind == TypeKind.TY_VOID:
        return ty_void
    elif kind == TypeKind.TY_BOOL:
        return ty_bool
    elif kind == TypeKind.TY_FLT32:
        return ty_flt32
    elif kind == TypeKind.TY_FLT64:
        return ty_flt64
    elif kind == TypeKind.TY_INT8:
        return ty_uint8 if is_unsigned else ty_int8
    elif kind == TypeKind.TY_INT16:
        return ty_uint16 if is_unsigned else ty_int16
    elif kind == TypeKind.TY_INT32:
        return ty_uint32 if is_unsigned else ty_int32
    return ty_uint64 if is_unsigned else ty_int64


def cast_node(node: ASTNode, new_type: DataType) -> ASTNode | None:
    if not node or not new_type:
        return None
    # 如果类型已经匹配，不需要转换
    if node.type == new_type:
        return node
    # 创建类型转换节点
    new_node = ASTNode(
        op=ASTNodeType.A_CAST,
        right=node,
        type=new_type
    )
    new_node.rvalue = True
    return new_node
