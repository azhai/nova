import sys
from typing import Optional, Iterator, List, Union

from utils import config, fatal
from defs import (
    TokType, OpCode, Token, Operator, create_keyword_token
)

NumberMaxLen = 30
OperatorMaxLen = 3


class Lexer:
    delimiters = {"(%": "%)", "%%": "\n", "'": "'",
                  "\"": "\"", "\"\"\"": "\"\"\""}
    operators = {
        '!': [("!=", OpCode.NE), ("!", OpCode.NOT)],
        '$': [("$", OpCode.DOLLAR)],
        '%': [("%=", OpCode.MOD_AS), ("%", OpCode.MOD)],
        '&': [("&&", OpCode.LOG_AND), ("&", OpCode.AND)],
        '(': [("(", OpCode.LPAREN)],
        ')': [(")", OpCode.RPAREN)],
        '*': [("*=", OpCode.MUL_AS), ("**", OpCode.POW), ("*", OpCode.MUL)],
        '+': [("+=", OpCode.ADD_AS), ("+", OpCode.ADD)],
        ',': [(",", OpCode.COMMA)],
        '-': [("-=", OpCode.SUB_AS), ("-", OpCode.SUB)],
        '.': [("..=", OpCode.RANGE_TOP), ("...", OpCode.ELLIPSES),
              ("..", OpCode.RANGE), (".", OpCode.DOT)],
        '/': [("/=", OpCode.DIV_AS), ("//", OpCode.QUO), ("/", OpCode.DIV)],
        ':': [(":=", OpCode.UNPACK), (":", OpCode.COLON)],
        ';': [(";", OpCode.SEMI)],
        '<': [("<=", OpCode.LE), ("<<", OpCode.LSHIFT), ("<", OpCode.LT)],
        '=': [("==", OpCode.EQ), ("=", OpCode.ASSIGN)],
        '>': [(">>", OpCode.RSHIFT), (">=", OpCode.GE), (">", OpCode.GT)],
        '^': [("^", OpCode.XOR)],
        '_': [("_", OpCode.IT)],
        '{': [("{", OpCode.LBRACE)],
        '|': [("||", OpCode.LOG_OR), ("|", OpCode.OR)],
        '}': [("}", OpCode.RBRACE)],
        '~': [("~", OpCode.INVERT)],
    }
    keywords = {
        'a': ["any", "atom", "abort"],
        'b': ["break", "bool"],
        'c': ["continue", "catch", "case"],
        'd': ["defer", "default", "def"],
        'e': ["extern", "enum", "else"],
        'f': ["for", "fn", "flt64", "flt32", "fallthru", "false"],
        'i': ["int8", "int64", "int32", "int16", "in", "if"],
        'l': ["let"],
        'm': ["match"],
        'n': ["null"],
        'p': ["public", "printf"],
        'r': ["return"],
        's': ["switch", "struct", "sizeof"],
        't': ["type", "try", "true", "throws"],
        'u': ["union", "uint8", "uint64", "uint32", "uint16"],
        'v': ["void"],
        'w': ["while"],
    }

    def __init__(self, filename: str):
        self.filename = filename
        self.file = None
        self.line_no, self.buf = 0, ""

    def open_file(self):
        """ 打开文件 """
        self.line_no, self.buf = 0, ""
        try:
            self.file = open(self.filename, "r", encoding="utf-8")
        except FileNotFoundError:
            fatal(f"File not found: {self.filename}")

    def close_file(self):
        """ 关闭文件 """
        if self.file:
            self.file.close()

    def next_line(self):
        """ 返回下一行 """
        line = self.file.readline()
        if line:
            self.buf += line
            self.line_no += 1
            return True
        return False

    def get_delim(self, temp):
        """ 从左到右，找出temp最长的一个左侧定界符 """
        left, right = "", ""
        if temp == "":
            return left, right
        for i in range(len(temp)):
            key = temp[:i+1]
            val = self.delimiters.get(key)
            if val:
                left, right = key, val
        return left, right

    def scan(self):
        """ 从当前位置继续扫描和读取token """
        self.open_file()
        while True:
            if self.buf == "": # 本行（跨行文本除外）token处理结束
                self.next_line()
                if self.buf == "": # 已处理文件最后一行
                    break
            c = self.buf[0]
            token = self.scan_once(c) # 一次最多获取一个token
            if token:
                yield token
            self.buf = self.buf.lstrip()
        self.close_file()

    def scan_once(self, c: str) -> Optional[Token]:
        """ 尝试查找一个token，注意以下次序不能更换 """
        token = None
        # 尝试数字或者关键词
        if c == '-' or c.isdigit():
            token = self.scan_number(c)
        elif c.islower() and (c in self.keywords):
            token = self.scan_keyword(c)
        # 如果找不到token，尝试查找id
        if token is None and (c == '_' or c.isalpha()):
            token = self.scan_ident(c)
        # 如果找不到token，尝试是否定界符
        if token is None:
            temp = self.buf.lstrip()[:OperatorMaxLen]
            left, right = self.get_delim(temp)
            token = self.scan_until(right, len(left))
        # 如果找不到token，尝试查找操作符
        if token is None and (c in self.operators):
            token = self.scan_operator(c)
        return token

    def scan_number(self, c: str) -> Optional[Token]:
        """ 查找表示整数或浮点数的文本，包括二、八、十六进制和科学记数法 """
        is_float, has_exp = False, False
        negate, zero = c == '-', c == '0'
        size = min(NumberMaxLen, len(self.buf))
        i = 1 # 传入的参数c是数值第一个字符，不需要检查
        for i in range(i, size):
            c = self.buf[i]
            if i == 1 and zero and c in ('b', 'B', 'o', 'O', 'x', 'X'):
                return self.scan_hex_oct(c)
            # 这三个字符只可能在浮点数出现，而且仅一次，但这里未进一步检查次数
            if not is_float and c in ('.', 'e', 'E'):
                is_float, has_exp = True, c != '.'
            # 除了开头，只可能出现在科学记数法中E后面，但这里未进一步检查次数和位置
            elif not has_exp and (c in ('-', '+')):
                i -= 1   # 后面处理时加1，为了和循环正常结束保持一致
                break
            elif not (c == '_' or c.isdigit()):
                i -= 1   # 后面处理时加1，为了和循环正常结束保持一致
                break
        temp = self.buf[:i+1].replace("_", "") # 去除连字符
        try:
            if is_float:
                token = Token(TokType.T_FLOAT, temp)
                token.value = float(temp)
            else:
                token = Token(TokType.T_INTEGER, temp)
                token.value = int(temp)
        except:
            return None
        token.line_no = self.line_no
        self.buf = self.buf[i+1:]
        return token

    def scan_hex_oct(self, c: str) -> Optional[Token]:
        """ 查找二、八、十六进制整数 """
        token, base = None, 16
        valid_chars = "0123456789abcdefABCDEF"
        if c in ('o', 'O'):
            base, valid_chars = 8, "01234567"
        elif c in ('b', 'B'):
            base, valid_chars = 2, "01"
        size = min(NumberMaxLen, len(self.buf))
        i = 2 # 传入的参数c是数值第二个字符，也不需要检查
        for i in range(i, size):
            c = self.buf[i]
            if c != '_' and (c not in valid_chars):
                i -= 1   # 后面处理时加1，为了和循环正常结束保持一致
                break
        temp = self.buf[:i+1].replace("_", "")
        token = Token(TokType.T_INTEGER, temp)
        token.value = int(temp, base) # 转为十进制数值
        token.line_no = self.line_no
        self.buf = self.buf[i+1:]
        return token

    def scan_keyword(self, c: str) -> Optional[Token]:
        """ 查找关键词，贪婪算法，每组关键词已在Lexer定义中倒序列出 """
        words = self.keywords.get(c, [])
        if not words:
            return None
        for word in words:
            if self.buf.startswith(word):
                token = create_keyword_token(word)
                token.line_no = self.line_no
                self.buf = self.buf[len(word):]
                return token
        return None

    def scan_ident(self, _: str) -> Optional[Token]:
        """ 查找标识符，即变量名、函数名、自定义类型名等 """
        i = 0
        for i, c in enumerate(self.buf):
            if c != '_' and not c.isalnum():
                i -= 1  # 后面处理时加1，为了和循环正常结束保持一致
                break
        if i >= 0:
            token = Token(TokType.T_IDENT, self.buf[:i+1])
            token.line_no = self.line_no
            self.buf = self.buf[i+1:]
            return token
        return None

    def scan_until(self, delim, start) -> Optional[Token]:
        """ 查找右侧定界符，其他字符原样收纳其中，用于代码中的字符串或注释 """
        if not delim:
            return None
        while True:
            # 从左定界符之后查找，避免左右定界符一样时死循环
            i = self.buf.find(delim, start)
            if i < 0: # 没找到
                start = len(self.buf)
                if self.next_line(): # 跨行文本
                    continue
                else:
                    break
            # 得到的文本temp中包含有左右定界符
            pos = i + len(delim)
            temp, self.buf = self.buf[:pos], self.buf[pos:]
            if delim in ("\n", "%)"):
                token = Token(TokType.T_COMMENT, temp.strip())
            else:
                token = Token(TokType.T_STRING, temp)
            # 记录行号，在后面环节中报错时使用
            token.line_no = self.line_no
            return token

    def scan_operator(self, c: str) -> Optional[Token]:
        """ 查找已知符号，贪婪算法，即找符合条件最长的一个 """
        items = self.operators.get(c, [])
        if not items:
            return None
        for text, op in items:
            if self.buf.startswith(text):
                token = Operator(text, op.value)
                token.line_no = self.line_no
                self.buf = self.buf[len(text):]
                return token
        return None


class TokenQueue:
    """ token队列，方便进行peek向后看的操作 """
    tokens = []
    offset: int = 0

    def __init__(self, it: Union[Iterator, List, None] = None):
        if it:
            self.tokens = list(it)

    def __len__(self) -> int:
        return len(self.tokens)

    def remain(self) -> int:
        return len(self.tokens) - self.offset

    def get_token(self, ahead = 0) -> Token:
        """ 获取当前或附近的token """
        offset = self.offset + ahead
        if 0 <= offset < len(self.tokens):
            tok = self.tokens[offset]
            config.line_no = tok.line_no # 记录行号
            return tok
        return Token(TokType.T_EOF)

    def curr_token(self) -> Token:
        """ 当前token """
        return self.get_token()

    def peek_token(self) -> Token:
        """ 即将到来的token """
        return self.get_token(ahead=1)

    def next_token(self) -> Token:
        """ 向后移动并返回token """
        self.offset += 1
        return self.get_token()

    def dump_tokens(self, out = None):
        """ 将所有token按所在代码行输出 """
        if not out:
            out = sys.stdout
        line = 0
        for token in self.tokens:
            if token.line_no > line:
                line = token.line_no
                out.write("\n{}: ".format(line))
            out.write("{} ".format(token))
        out.write("\n")
