import sys
from enum import IntEnum, StrEnum
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

class NumType(StrEnum):
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    FLOAT32 = "float32"
    FLOAT64 = "float64"

    def is_integer(self):
        return self.value.startswith("int")

    def is_unsigned(self):
        return self.value.startswith("uint")

    def is_float(self):
        return self.value.startswith("float")


class OpType(IntEnum):
    IT = 11
    DOT = 12
    RANGE = 13
    RANGE_TOP = 14
    ELLIPSES = 15
    COMMA = 16
    COLON = 17
    SEMI = 18
    LPAREN = 19
    RPAREN = 20
    LBRACE = 21
    RBRACE = 22
    ASSIGN = 23
    UNPACK = 24
    ADD = 25
    SUB = 26
    MUL = 27
    DIV = 28
    MOD = 29
    QUO = 30
    POW = 31
    ADD_AS = 32
    SUB_AS = 33
    MUL_AS = 34
    DIV_AS = 35
    MOD_AS = 36
    EQ = 37
    NE = 38
    LT = 39
    LE = 40
    GT = 41
    GE = 42
    NOT = 43
    LOG_AND = 44
    LOG_OR = 45
    INVERT = 46
    AND = 47
    OR = 48
    XOR = 49
    LSHIFT = 50
    RSHIFT = 51
    DOLLAR = 52

    def is_assignment(self):
        return (self.value == OpType.ASSIGN or
                OpType.ADD_AS <= self.value <= OpType.MOD_AS)

    def is_arithmetic(self):
        return OpType.ADD <= self.value <= OpType.POW

    def is_comparison(self):
        return OpType.EQ <= self.value <= OpType.GE

    def is_logical(self):
        return OpType.INVERT <= self.value <= OpType.RSHIFT


class TokType(IntEnum):
    T_EOF = 0
    T_COMMENT = 1
    T_KEYWORD = 2
    T_IDENT = 3
    T_BOOL = 4
    T_NUMBER = 5
    T_STRING = 6
    T_OPERATOR = 7



class Token:
    tok_type: TokType
    line_no: int

    def __init__(self, tok_type: TokType, text: str = ""):
        self.tok_type, self.text = tok_type, text
        self.line_no, self.value  = 0, 0

    def __str__(self):
        if self.tok_type is TokType.T_EOF:
            return "EOF"
        name = self.tok_type.name
        if self.tok_type is TokType.T_STRING:
            return "{}({!r})".format(name, self.text)
        elif self.tok_type is TokType.T_OPERATOR:
            return f"{name}(\"{self.text}\")"
        elif self.text != "":
            return f"{name}({self.text})"
        else:
            return f"{name}"


class TypeKind(IntEnum):
    K_VOID = 0
    K_BOOL = 1
    K_INT8 = 2
    K_INT16 = 3
    K_INT32 = 4
    K_INT64 = 5
    K_FLT32 = 6
    K_FLT64 = 7

    K_UINT8 = 10
    K_UINT16 = 11
    K_UINT32 = 12
    K_UINT64 = 13

    K_PTR = 16

class DataType:
    def __init__(self, kind: TypeKind, size: int = 0, align: int = 0, is_unsigned: bool = False):
        self.kind = kind
        self.size = size
        self.align = align
        self.is_unsigned = is_unsigned
        self.sibling: Optional[DataType] = None


class SymType(IntEnum):
    S_LOCAL = 1
    S_VAR = 2
    S_FUNC = 3


class Sym:
    name: str
    sym_type: SymType
    val_type: TypeKind

    def __init__(self, name: str, sym_type: SymType, val_type: TypeKind):
        self.name = name
        self.sym_type = sym_type
        self.val_type = val_type
        self.has_addr: bool = False
        self.params = []
        # self.count: int = 0
        # self.memb: Optional[Sym] = None
        # self.sibling: Optional[Sym] = None


class NodeType(IntEnum):
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
    def __init__(self, op: NodeType, left=None, right=None,
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
ty_void = DataType(TypeKind.K_VOID, 1, 1)
ty_bool = DataType(TypeKind.K_BOOL, 1, 1)
ty_int8 = DataType(TypeKind.K_INT8, 1, 1)
ty_int16 = DataType(TypeKind.K_INT16, 2, 2)
ty_int32 = DataType(TypeKind.K_INT32, 4, 4)
ty_int64 = DataType(TypeKind.K_INT64, 8, 8)
ty_uint8 = DataType(TypeKind.K_INT8, 1, 1, is_unsigned=True)
ty_uint16 = DataType(TypeKind.K_INT16, 2, 2, is_unsigned=True)
ty_uint32 = DataType(TypeKind.K_INT32, 4, 4, is_unsigned=True)
ty_uint64 = DataType(TypeKind.K_INT64, 8, 8, is_unsigned=True)
ty_float32 = DataType(TypeKind.K_FLT32, 4, 4)
ty_float64 = DataType(TypeKind.K_FLT64, 8, 8)


def get_ast_type(kind: TypeKind, is_unsigned: bool = False) -> DataType:
    if kind == TypeKind.K_VOID:
        return ty_void
    elif kind == TypeKind.K_BOOL:
        return ty_bool
    elif kind == TypeKind.K_FLT32:
        return ty_float32
    elif kind == TypeKind.K_FLT64:
        return ty_float64
    elif kind == TypeKind.K_INT8:
        return ty_uint8 if is_unsigned else ty_int8
    elif kind == TypeKind.K_INT16:
        return ty_uint16 if is_unsigned else ty_int16
    elif kind == TypeKind.K_INT32:
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
        op=NodeType.A_CAST,
        right=node,
        type=new_type
    )
    new_node.rvalue = True
    return new_node
