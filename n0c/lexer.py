import sys

from defs import TokType, OpCode, Token, Operator, fatal, create_keyword_token

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
        'a': ["any", "atom"],
        'b': ["bool"],
        'd': ["def"],
        'e': ["enum", "else"],
        'f': ["for", "fn", "float64", "float32", "false"],
        'i': ["int8", "int64", "int32", "int16", "in", "if"],
        'l': ["let"],
        'm': ["match"],
        'n': ["null"],
        'p': ["printf"],
        't': ["true"],
        'u': ["uint8", "uint64", "uint32", "uint16"],
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
            if self.buf == "":
                self.next_line()
                if self.buf == "":
                    break
            c = self.buf[0]
            token = self.scan_once(c)
            if token:
                yield token
            self.buf = self.buf.lstrip()
        self.close_file()

    def scan_once(self, c: str):
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

    def scan_until(self, delim, start):
        """ 查找右侧定界符，其他字符原样收纳其中，用于代码中的字符串或注释 """
        if not delim:
            return None
        while True:
            i = self.buf.find(delim, start)
            if i < 0: # 没找到
                start = len(self.buf)
                if self.next_line():
                    continue
                else:
                    break
            pos = i + len(delim)
            temp, self.buf = self.buf[:pos], self.buf[pos:]
            if delim in ("\n", "%)"):
                token = Token(TokType.T_COMMENT, temp.strip())
            else:
                token = Token(TokType.T_STRING, temp)
            token.line_no = self.line_no
            return token

    def scan_number(self, c: str):
        is_float, has_exp, i = False, False, 1
        negate, zero = c == '-', c == '0'
        size = min(NumberMaxLen, len(self.buf))
        for i in range(i, size):
            c = self.buf[i]
            if i == 1 and zero and c in ('o', 'O', 'x', 'X'):
                return self.scan_hex_oct(c)
            if not is_float and c in ('.', 'e', 'E'):
                is_float, has_exp = True, c != '.'
            elif not has_exp and (c in ('-', '+')):
                i -= 1   # 后面处理时加1，为了和循环正常结束保持一致
                break
            elif not (c == '_' or c.isdigit()):
                i -= 1   # 后面处理时加1，为了和循环正常结束保持一致
                break
        temp = self.buf[:i+1].replace("_", "")
        if is_float:
            token = Token(TokType.T_FLOAT, temp)
            token.value = float(temp)
        elif temp.isnumeric():
            token = Token(TokType.T_INTEGER, temp)
            token.value = int(temp)
        else:
            return None
        token.line_no = self.line_no
        self.buf = self.buf[i+1:]
        return token

    def scan_hex_oct(self, c: str):
        token, i, base = None, 2, 16
        num_chars = "0123456789abcdefABCDEF"
        if c in ('o', 'O'):
            base, num_chars = 8, "01234567"
        size = min(NumberMaxLen, len(self.buf))
        for i in range(i, size):
            c = self.buf[i]
            if c != '_' and (c not in num_chars):
                i -= 1   # 后面处理时加1，为了和循环正常结束保持一致
                break
        temp = self.buf[:i+1].replace("_", "")
        token = Token(TokType.T_INTEGER, temp)
        token.value = int(temp, base)
        token.line_no = self.line_no
        self.buf = self.buf[i+1:]
        return token

    def scan_operator(self, c: str):
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

    def scan_keyword(self, c: str):
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

    def scan_ident(self, _: str):
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


class TokenQueue:
    tokens = []
    offset: int = 0

    def __init__(self, it = None):
        if it:
            self.tokens = list(it)

    def __len__(self):
        return len(self.tokens)

    def remain(self):
        return len(self.tokens) - self.offset

    def curr_token(self):
        if 0 <= self.offset < len(self.tokens):
            return self.tokens[self.offset]
        return Token(TokType.T_EOF)

    def next_token(self):
        self.offset += 1
        return self.curr_token()

    def dump_tokens(self, out=None):
        if not out:
            out = sys.stdout
        line = 0
        for token in self.tokens:
            if token.line_no > line:
                line = token.line_no
                out.write("\n{}: ".format(line))
            out.write("{} ".format(token))
        out.write("\n")
