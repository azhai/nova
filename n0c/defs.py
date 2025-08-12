import os
import sys
from typing import Optional

if sys.version_info >= (3, 11):
    from enum import IntEnum, StrEnum
else:
    from enum_v3_11 import IntEnum, StrEnum


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
    outFp, logFp = None, None

    def __init__(self, outfile: str, logfile: str = ""):
        if outfile:
            self.outFp = self.open(outfile)
        if logfile:
            self.logFp = self.open(logfile)

    @staticmethod
    def open(filename: str):
        """ 打开文件准备写入 """
        if filename in ("stdout", "stderr"):
            return getattr(sys, filename)
        if filename == "/dev/null":
            filename = os.devnull
        try:
            return open(filename, "w", encoding="utf-8")
        except FileNotFoundError:
            notice(f"File not found: {filename}")
        except IOError as e:
            notice(f"Cannot open file: {e}")
        return None

    def close(self):
        """ 关闭文件 """
        if self.outFp:
            self.outFp.close()
        if self.logFp:
            self.logFp.close()


class TokType(IntEnum):
    T_EOF = 0
    T_WHITESPACE = 1
    T_COMMENT = 2
    T_OPERATOR = 3
    T_KEYWORD = 4
    T_IDENT = 5
    T_VOID = 6
    T_BOOL = 7
    T_STRING = 8
    T_INTEGER = 9
    T_FLOAT = 10


class Token:
    tok_type: TokType
    line_no: int
    text, value = "", 0

    def __init__(self, tok_type: TokType, text: str = ""):
        self.tok_type, self.line_no = tok_type, 0
        self.text, self.value = text, 0

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

    def is_type(self) -> bool:
        if self.tok_type != TokType.T_KEYWORD:
            return False
        return self.text in ValType


class OpCode(IntEnum):
    NOOP = 0
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
    DOLLAR = 23

    ASSIGN = 30
    UNPACK = 31
    NEG = 32
    ADD = 33
    SUB = 34
    MUL = 35
    DIV = 36
    MOD = 37
    QUO = 38
    POW = 39
    ADD_AS = 40
    SUB_AS = 41
    MUL_AS = 42
    DIV_AS = 43
    MOD_AS = 44
    EQ = 45
    NE = 46
    LT = 47
    LE = 48
    GT = 49
    GE = 50
    NOT = 51
    LOG_AND = 52
    LOG_OR = 53
    INVERT = 54
    AND = 55
    OR = 56
    XOR = 57
    LSHIFT = 58
    RSHIFT = 59

def is_assignment(code: int) -> bool:
    return (code == OpCode.ASSIGN or
            OpCode.ADD_AS <= code <= OpCode.MOD_AS)

def is_arithmetic(code: int) -> bool:
    return OpCode.ADD <= code <= OpCode.POW

def is_comparison(code: int) -> bool:
    return OpCode.EQ <= code <= OpCode.GE

def is_logical(code: int) -> bool:
    return OpCode.INVERT <= code <= OpCode.RSHIFT


class Operator(Token):
    _prece: int = -1
    _unary: bool = False
    unary_ops = (OpCode.NEG, OpCode.NOT, OpCode.INVERT)
    precedences = {
        OpCode.NOOP: 0,
        OpCode.AND: 10, OpCode.OR: 10, OpCode.XOR: 10,
        OpCode.INVERT: 20,
        OpCode.LOG_OR: 30,
        OpCode.LOG_AND: 40,
        OpCode.NOT: 50,
        OpCode.EQ: 60, OpCode.NE: 60, OpCode.LT: 60, OpCode.LE: 60, OpCode.GT: 60, OpCode.GE: 60,
        OpCode.LSHIFT: 70, OpCode.RSHIFT: 70,
        OpCode.NEG: 80, OpCode.ADD: 80, OpCode.SUB: 80,
        OpCode.MUL: 90, OpCode.DIV: 90, OpCode.MOD: 90, OpCode.QUO: 90,
        OpCode.POW: 100,
    }

    def __init__(self, text: str, value: int):
        super().__init__(TokType.T_OPERATOR, text)
        self.value = value

    @property
    def is_unary(self) -> bool:
        if self._unary:
            return self._unary
        if self.value in self.unary_ops:
            self._unary = True
        return self._unary

    @property
    def prece(self) -> int:
        if self._prece >= 0:
            return self._prece
        self._prece = self.precedences.get(self.value, 0)
        return self._prece


class Keyword(StrEnum):
    PRINTF = "printf"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    FOR = "for"
    IN = "in"
    BREAK = "break"
    CONTINUE = "continue"
    RETURN = "return"
    VOID = "void"

def create_keyword_token(word: str) -> Token:
    if word == "null":
        token = Token(TokType.T_VOID, word)
    elif word == "true" or word == "false":
        token = Token(TokType.T_BOOL, word)
    else:
        token = Token(TokType.T_KEYWORD, word)
    return token


class ValType(StrEnum):
    VOID = "void"
    BOOL = "bool"
    STR = "str"
    PTR = "ptr"
    OBJ = "obj"
    REF = "ref"

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

    def is_integer(self) -> bool:
        return self.name.startswith("INT")

    def is_unsigned(self) -> bool:
        return self.name.startswith("UINT")

    def is_float(self) -> bool:
        return self.name.startswith("FLOAT")

    def bytes(self) -> int:
        if self.name == "BOOL":
            return 1
        elif self.is_integer():
            return int(self.name[3:]) // 8
        elif self.is_unsigned():
            return int(self.name[4:]) // 8
        elif self.is_float():
            return int(self.name[5:]) // 8
        return 0


class SymType(IntEnum):
    S_LOCAL = 1
    S_CONST = 2
    S_VAR = 3
    S_FUNC = 4
    S_CLASS = 5


class Symbol:
    name: str
    sym_type: SymType
    val_type: ValType
    init_val = ""
    params = []

    def __init__(self, name: str, sym_type: SymType, val_type: ValType):
        self.name = name
        self.sym_type = sym_type
        self.val_type = val_type


class NodeType(IntEnum):
    A_GLUE = 0
    A_LOCAL = 1

    A_CAST = 10
    A_CALL = 11
    A_FUNC = 12
    A_CLASS = 13
    A_TYPE = 14
    A_IDENT = 15
    A_LITERAL = 16
    A_BLOCK = 17
    A_GOTO = 18
    A_RETURN = 19
    A_BREAK = 20
    A_CONTINUE = 21
    A_IF = 22
    A_WHILE = 23
    A_FOR = 24

    A_ASSIGN = 30
    A_UNPACK = 31
    A_NEG = 32
    A_ADD = 33
    A_SUB = 34
    A_MUL = 35
    A_DIV = 36
    A_MOD = 37
    A_QUO = 38
    A_POW = 39
    A_ADD_AS = 40
    A_SUB_AS = 41
    A_MUL_AS = 42
    A_DIV_AS = 43
    A_MOD_AS = 44
    A_EQ = 45
    A_NE = 46
    A_LT = 47
    A_LE = 48
    A_GT = 49
    A_GE = 50
    A_NOT = 51
    A_LOG_AND = 52
    A_LOG_OR = 53
    A_INVERT = 54
    A_AND = 55
    A_OR = 56
    A_XOR = 57
    A_LSHIFT = 58
    A_RSHIFT = 59

    A_PRINTF = 60


class ASTNode:
    op: NodeType
    left, right = None, None
    val_type: Optional[ValType]
    sym: Optional[Symbol]
    number, string = 0, ""

    def __init__(self, op: NodeType, left = None, right = None):
        self.op, self.sym, self.val_type = op, None, None
        self.left, self.right = left, right

    def __repr__(self) -> str:
        raise NotImplementedError()

    def gen(self) -> int:
        raise NotImplementedError()
