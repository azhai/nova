import sys

from defs import TokenType, NumType, Token, Thistoken, fatal, read_file

TextLen = 512
Keywords = {
    'void': TokenType.T_VOID,
    'bool': TokenType.T_BOOL,
    'int8': TokenType.T_INT8,
    'int16': TokenType.T_INT16,
    'int32': TokenType.T_INT32,
    'int64': TokenType.T_INT64,
    'uint8': TokenType.T_UINT8,
    'uint16': TokenType.T_UINT16,
    'uint32': TokenType.T_UINT32,
    'uint64': TokenType.T_UINT64,
    'flt32': TokenType.T_FLT32,
    'flt64': TokenType.T_FLT64,
    'if': TokenType.T_IF,
    'else': TokenType.T_ELSE,
    'false': TokenType.T_FALSE,
    'for': TokenType.T_FOR,
    'printf': TokenType.T_PRINTF,
    'true': TokenType.T_TRUE,
    'while': TokenType.T_WHILE
}


class Lexer:
    LineNo, AtBegin = 1, False
    InComment, MulComment = False, False

    def __init__(self, filename: str):
        self.filename = filename
        self.source = read_file(filename)
        self.reset()

    def reset(self):
        self.pos, self.size = -1, len(self.source)

    @staticmethod
    def slash_char(c: str) -> str:
        if c == 'a': return '\a'
        if c == 'b': return '\b'
        if c == 'f': return '\f'
        if c == 'n': return '\n'
        if c == 'r': return '\r'
        if c == 't': return '\t'
        if c == 'v': return '\v'
        if c in ['"', '\'', '\\']: return c
        return ''

    @staticmethod
    def ord_char(s: str, c: str) -> int:
        for i, char in enumerate(s):
            if char == c:
                return i
        return -1

    def back_pos(self, n: int = 1):
        self.pos -= n

    def hex_char(self) -> str:
        c = self.next_char().lower()
        regular, n = False, 0
        while c != '\0' and (c.isdigit() or 'a' <= c <= 'f'):
            h = self.ord_char("0123456789abcdef", c)
            regular, n = True, n * 16 + h
            c = self.next_char().lower()
        self.back_pos()
        if not regular:
            fatal("missing digits after '\\x'")
        if n > 255:
            fatal("value out of range after '\\x'")
        return chr(n)

    def unquote_char(self, c: str) -> str:
        if c != '\\':
            return c
        c = self.next_char()
        c2 = self.slash_char(c)
        if c2 != '':
            return c2

        if '0' <= c <= '7':
            i, c3 = 0, 0
            while c != '\0' and '0' <= c <= '7' and i < 3:
                c3 = c3 * 8 + (ord(c) - ord('0'))
                i += 1
                c = self.next_char()
            self.back_pos()
            return chr(c3)
        if c == 'x':
            return self.hex_char()
        fatal(f"unknown escape sequence {c}")
        return ''

    def next_char(self, ignore_space=False) -> str:
        self.pos += 1
        if self.pos >= self.size:
            return '\0'
        c = self.source[self.pos]
        if c == '\n':
            self.LineNo += 1
            self.AtBegin = True
            self.InComment = False
            return self.next_char(True)
        # 跳过注释和空白
        while self.InComment or ignore_space and c.isspace():
            c = self.next_char(True)
        return c

    def dump_tokens(self, out=None):
        if not out:
            out = sys.stdout
        line = 0
        self.reset()
        out.write("\nTokens in {}".format(self.filename))
        for token in self.scan_all():
            if self.LineNo > line:
                line = self.LineNo
                out.write("\n{}: ".format(line))
            out.write("{} ".format(token))
        out.write("\n")

    def scan_next(self):
        c = self.next_char(True)
        if c == '\0':  # EOF
            return Token(TokenType.T_EOF)
        if c.isalpha() or c == '_':
            return self.scan_keyword(c)
        elif c == '"' or c == '\'' or c == '\\':
            return self.scan_string(c)
        elif c.isdigit() or c == '.':
            return self.scan_number(c)
        else:
            return self.scan_symbol(c)

    def scan_all(self):
        token = self.scan_next()
        while token.token != TokenType.T_EOF:
            yield token
            token = self.scan_next()
        yield token

    def scan_keyword(self, c: str) -> Token:
        i, buf = 0, []
        while i < TextLen - 1 and (c.isalnum() or c == '_'):
            buf.append(c)
            i += 1
            c = self.next_char()
        self.back_pos()
        word = ''.join(buf)
        tok_type = Keywords.get(word, TokenType.T_IDENT)
        token = Token(tok_type)
        token.tok_str = word
        return token

    def scan_string(self, delim: str) -> Token:
        i, buf = 0, [delim, ]
        c = self.next_char()
        while c != delim and c != '':
            if i >= TextLen - 1:
                fatal("String too long")
            if c == '\\':
                c = self.unquote_char(c)
            buf.append(c)
            i += 1
            c = self.next_char()
        if c == '':
            fatal("Unclosed string")
        else:
            buf.append(delim)
        token = Token(TokenType.T_STRLIT)
        token.tok_str = ''.join(buf)
        return token

    def scan_number(self, c: str) -> Token:
        has_dot, has_e = False, False
        i, buf = 0, []
        if c == '.':
            buf = ['0']
        while i < TextLen - 1 and (c.isdigit() or c == '.' or c.lower() == 'e'):
            if has_dot and c == '.':
                break
            elif has_e and c.lower() == 'e':
                break
            buf.append(c)
            i += 1
            if c == '.':
                has_dot = True
            elif c.lower() == 'e':
                has_e = True
                c = self.next_char()
                if c == '+' or c == '-':
                    buf.append(c)
                    i += 1
            c = self.next_char()
        self.back_pos()

        word = ''.join(buf)
        token = Token(TokenType.T_NUMLIT)
        token.tok_str = word
        if has_dot or has_e:
            token.num_type = NumType.NUM_FLT
            token.num_val = float(word)
        else:
            token.num_type = NumType.NUM_INT
            token.num_val = int(word)
        return token

    def scan_symbol(self, c: str) -> Token | None:
        two_char_ops = {
            '=': {'=': TokenType.T_EQ},
            '!': {'=': TokenType.T_NE},
            '<': {'=': TokenType.T_LE, '<': TokenType.T_LSHIFT},
            '>': {'=': TokenType.T_GE, '>': TokenType.T_RSHIFT},
            '&': {'&': TokenType.T_LOGAND},
            '|': {'|': TokenType.T_LOGOR}
        }
        if c in two_char_ops:
            next_c = self.next_char()
            if next_c in two_char_ops[c]:
                tok_type = two_char_ops[c][next_c]
                return Token(tok_type)
            self.back_pos()

        single_char_ops = {
            '+': TokenType.T_PLUS,
            '-': TokenType.T_MINUS,
            '*': TokenType.T_STAR,
            '/': TokenType.T_SLASH,
            '%': TokenType.T_MOD,
            '=': TokenType.T_ASSIGN,
            '~': TokenType.T_INVERT,
            '!': TokenType.T_LOGNOT,
            '&': TokenType.T_AMPER,
            '|': TokenType.T_OR,
            '^': TokenType.T_XOR,
            ';': TokenType.T_SEMI,
            '{': TokenType.T_LBRACE,
            '}': TokenType.T_RBRACE,
            '(': TokenType.T_LPAREN,
            ')': TokenType.T_RPAREN,
            ',': TokenType.T_COMMA
        }
        if c in single_char_ops:
            tok_type = single_char_ops[c]
            return Token(tok_type)
        fatal(f"Unknown character {c}")
        return None

    def next(self) -> int:
        if self.Putback:
            c = self.Putback
            self.Putback = 0
            return c

        c = self.Infh.read(1)
        if not c:  # EOF
            return 0
        c = ord(c)

        while self.AtBegin and c == ord('#'):
            self.AtBegin = 0
            self.scan(Thistoken)
            if Thistoken.token != TokenType.T_NUMLIT:
                fatal(f"Expecting pre-processor line number, got {Text}")
            l = Thistoken.num_val

            self.scan(Thistoken)
            if Thistoken.token != TokenType.T_STRLIT:
                fatal(f"Expecting pre-processor file name, got {Text}")

            # if Text[0] != '<':
            #     global Infilename
            #     if Text != Infilename:
            #         Infilename = Text
            #     Line = l

            while True:
                c = self.Infh.read(1)
                if not c or c == '\n':
                    break
            c = self.Infh.read(1)
            if not c:
                return 0
            c = ord(c)
            self.AtBegin = 1

        self.AtBegin = 0
        if c == ord('\n'):
            self.LineNo += 1
            self.AtBegin = 1
        return c
