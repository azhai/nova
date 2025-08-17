import argparse
import os, sys


def parse_cmd_args() -> argparse.Namespace:
    """ 解析命令行参数 """
    parser = argparse.ArgumentParser(description="Alic Compiler")
    parser.add_argument("input_file", help="Input source file")
    parser.add_argument("-o", "--output", help="Output file (default: out.q)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    cfg = parser.parse_args()
    cfg.line_no = 0 # 增加行号属性
    return cfg

config = parse_cmd_args()


def fatal(msg: str):
    if config.debug:
        raise Exception(f"Fatal error: {msg}")
    else:
        file, line = config.input_file, config.line_no
        print(f"{file} line {line}: {msg}", file=sys.stderr)
        sys.exit(1)


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

