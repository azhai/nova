import sys

from defs import TokType, OpType, Token, fatal, read_file

TextMaxLen = 512
IdentMaxLen = 100
NumberMaxLen = 30
KeywordMaxLen = 7
OperatorMaxLen = 3


class Lexer:
    line_no, line_end = 1, 0
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
        self.source = read_file(filename)
        self.pos, self.size = 0, len(self.source)
        self.temp = ""

    def incr_line_no(self):
        """ 行号增加 """
        if self.line_end > 0:
            n = self.temp.count('\n')
            self.line_no += (self.line_end - n)
            self.line_end = n

    def next_char(self) -> str:
        """ 返回下一个字符，如果是末尾则返回多次'\0' """
        if self.pos >= self.size:
            return '\0'
        c = self.source[self.pos]
        # 标记一个换行，由于最后一个token可能未解析，行号暂时不能加1
        if c == '\n':
            self.line_end += 1
        self.pos += 1
        return c

    def read_more(self, size = -1, check = None):
        """ 扫描更多的符号，用于注释中的代码 """
        while size < 0 or size > len(self.temp):
            c = self.next_char()
            if c == '\0':
                break
            self.temp += c
            if c.isspace():
                break
            if check and not check(c):
                break

    def check_temp(self, offset: int = 0, check = None):
        size = len(self.temp)
        if not (check and offset < size):
            return size, True
        for i in range(offset, size):
            c = self.temp[i]
            if not check(c):
                return i, False
        return size, True

    def get_temp_char(self, i: int, check = None):
        """ 获取temp中的第i个字符 """
        size, stop = len(self.temp), i
        if 0 - size <= i < 0:
            i += size
        if 0 <= i < size:
            return i, self.temp[i]
        i, c = size - 1, ''
        while i < stop:
            i += 1
            c = self.next_char()
            if c == '\0':
                break
            self.temp += c
            if c.isspace():
                break
            if check and not check(c):
                break
        return i, c

    def get_delim(self, temp):
        """ 从左到右，找出temp最长的一个左侧定界符 """
        if temp == "":
            return ""
        delim, word = "", ""
        for i, c in enumerate(temp):
            word += c
            delim = self.delimiters.get(word, delim)
        return delim

    def scan(self):
        """ 从当前位置继续扫描和读取token """
        while True:
            if self.temp == "":
                # 确保换行之前的token都解析了
                self.incr_line_no()
                # 读取一个不是空白的字符
                c = self.next_char()
                if c == '\0': # 文件末尾并且token已处理完毕
                    break
                elif c.isspace():
                    continue
                self.temp = c
            else:
                c = self.temp[0]
            token = self.scan_once(c)
            if token:
                yield token
            self.temp = self.temp.lstrip()

    def scan_once(self, c: str):
        """ 尝试查找一个token，注意以下三者的次序不能更换 """
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
            self.read_more(OperatorMaxLen, lambda x: not x.isalnum())
            delim = self.get_delim(self.temp)
            token = self.scan_until(delim)
        # 如果找不到token，尝试查找操作符
        if token is None and (c in self.operators):
            token = self.scan_operator(c)
        return token

    def scan_until(self, delim):
        """ 查找右侧定界符，其他字符原样收纳其中，用于代码中的字符串或注释 """
        token, size = None, len(delim)
        if size == 0:
            return token
        while True:
            c = self.next_char()
            if c == '\0':
                if delim == "\n": #等同于最后一个换行
                    break
                else: # 还没有找到定界符就结束了
                    fatal("unexpected end of file")
                    return token
            self.temp += c
            if size == 1 and c == delim:
                break
            elif size > 1 and self.temp.endswith(delim):
                break
        if delim in ("\n", "%)"):
            token = Token(TokType.T_COMMENT, self.temp.rstrip())
        else:
            token = Token(TokType.T_STRING, self.temp)
        self.temp = ""
        return token

    def scan_number(self, c: str):
        is_float, has_exp, i = False, False, 1
        negate, zero = c == '-', c == '0'
        for i in range(i, NumberMaxLen):
            i, c = self.get_temp_char(i)
            if i == 1 and zero and c in ('o', 'O', 'x', 'X'):
                return self.scan_hex_oct(c)
            if not is_float and c in ('.', 'e', 'E'):
                is_float, has_exp = True, c != '.'
            elif not has_exp and (c in ('-', '+')):
                break
            elif not (c == '_' or c.isdigit()):
                break
        temp = self.temp[:i].replace("_", "")
        if temp != "" and c != "-" and temp.isnumeric():
            number = float(temp) if is_float else int(temp)
            token = Token(TokType.T_NUMBER, temp, number)
            self.temp = self.temp[i:]
            return token
        return None

    def scan_hex_oct(self, c: str):
        token, i, base = None, 2, 16
        num_chars = "0123456789abcdefABCDEF"
        if c in ('o', 'O'):
            base, num_chars = 8, "01234567"
        check = (lambda x: x == '_' or (x in num_chars))
        i, ok = self.check_temp(2, check)
        if ok:
            i, _ = self.get_temp_char(NumberMaxLen, check)
        temp = self.temp[:i].replace("_", "")
        # if temp != "" and temp.isnumeric():
        if temp != "":
            number = int(temp, base)
            token = Token(TokType.T_NUMBER, temp, number)
            self.temp = self.temp[i:]
        return token

    def scan_operator(self, c: str):
        items = self.operators.get(c, [])
        if not items:
            return None
        self.read_more(OperatorMaxLen, lambda x: not x.isalnum())
        for text, op in items:
            if self.temp.startswith(text):
                token = Token(TokType.T_OPERATOR, text, op.value)
                self.temp = self.temp[len(text):]
                return token
        return None

    def scan_keyword(self, c: str):
        words = self.keywords.get(c, [])
        if not words:
            return None
        self.read_more(KeywordMaxLen, lambda x: x.islower() or x.isdigit())
        for word in words:
            if self.temp.startswith(word):
                token = Token(TokType.T_KEYWORD, word)
                self.temp = self.temp[len(word):]
                return token
        return None

    def scan_ident(self, _: str):
        check = (lambda x: x == '_' or x.isalnum())
        i, ok = self.check_temp(0, check)
        if ok:
            i, _ = self.get_temp_char(IdentMaxLen, check)
        if i >= 1:
            token = Token(TokType.T_IDENT, self.temp[:i])
            self.temp = self.temp[i:]
            return token
        return None

    def dump_tokens(self, out=None):
        if not out:
            out = sys.stdout
        self.pos, self.size = 0, len(self.source)
        self.temp, line = "", 0
        for token in self.scan():
            if self.line_no > line:
                line = self.line_no
                out.write("\n{}: ".format(line))
            out.write("{} ".format(token))
        out.write("\n")