import sys

from defs import TokType, OpType, Token, fatal

TextMaxLen = 512
IdentMaxLen = 100
NumberMaxLen = 30
KeywordMaxLen = 7
OperatorMaxLen = 3


class Lexer:
    delimiters = {"(%": "%)", "%%": "\n", "'": "'",
                  "\"": "\"", "\"\"\"": "\"\"\""}
    operators = {
        '!': [("!=", OpType.NE), ("!", OpType.NOT)],
        '$': [("$", OpType.DOLLAR)],
        '%': [("%=", OpType.MOD_AS), ("%", OpType.MOD)],
        '&': [("&&", OpType.LOG_AND), ("&", OpType.AND)],
        '(': [("(", OpType.LPAREN)],
        ')': [(")", OpType.RPAREN)],
        '*': [("*=", OpType.MUL_AS), ("**", OpType.POW), ("*", OpType.MUL)],
        '+': [("+=", OpType.ADD_AS), ("+", OpType.ADD)],
        ',': [(",", OpType.COMMA)],
        '-': [("-=", OpType.SUB_AS), ("-", OpType.SUB)],
        '.': [("..=", OpType.RANGE_TOP), ("...", OpType.ELLIPSES),
              ("..", OpType.RANGE), (".", OpType.DOT)],
        '/': [("/=", OpType.DIV_AS), ("//", OpType.QUO), ("/", OpType.DIV)],
        ':': [(":=", OpType.UNPACK), (":", OpType.COLON)],
        ';': [(";", OpType.SEMI)],
        '<': [("<=", OpType.LE), ("<<", OpType.LSHIFT), ("<", OpType.LT)],
        '=': [("==", OpType.EQ), ("=", OpType.ASSIGN)],
        '>': [(">>", OpType.RSHIFT), (">=", OpType.GE), (">", OpType.GT)],
        '^': [("^", OpType.XOR)],
        '_': [("_", OpType.IT)],
        '{': [("{", OpType.LBRACE)],
        '|': [("||", OpType.LOG_OR), ("|", OpType.OR)],
        '}': [("}", OpType.RBRACE)],
        '~': [("~", OpType.INVERT)],
    }
    keywords = {
        'a': ["any", "atom"],
        'b': ["bool"],
        'd': ["def"],
        'e': ["enum", "else"],
        'f': ["for", "fn", "float64", "float32", "false"],
        'i': ["int8", "int64", "int32", "int16", "if"],
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
                token = Token(TokType.T_COMMENT, temp.rstrip())
            else:
                token = Token(TokType.T_STRING, temp)
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
        if temp != "" and temp.isnumeric():
            number = float(temp) if is_float else int(temp)
            token = Token(TokType.T_NUMBER, temp, number)
            self.buf = self.buf[i+1:]
            return token
        return None

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
        # if temp != "" and temp.isnumeric():
        if temp != "":
            number = int(temp, base)
            token = Token(TokType.T_NUMBER, temp, number)
            self.buf = self.buf[i+1:]
        return token

    def scan_operator(self, c: str):
        items = self.operators.get(c, [])
        if not items:
            return None
        for text, op in items:
            if self.buf.startswith(text):
                token = Token(TokType.T_OPERATOR, text, op.value)
                self.buf = self.buf[len(text):]
                return token
        return None

    def scan_keyword(self, c: str):
        words = self.keywords.get(c, [])
        if not words:
            return None
        for word in words:
            if self.buf.startswith(word):
                token = Token(TokType.T_KEYWORD, word)
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
            self.buf = self.buf[i+1:]
            return token
        return None

    def dump_tokens(self, out=None):
        if not out:
            out = sys.stdout
        line = 0
        for token in self.scan():
            if self.line_no > line:
                line = self.line_no
                out.write("\n{}: ".format(line))
            out.write("{} ".format(token))
        out.write("\n")