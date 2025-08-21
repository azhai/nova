#!/usr/bin/env python3

"""
- 创建了核心数据结构文件：
- `defs.py` ：定义了编译器所需的枚举、类型和全局变量
- `utils.py` ：工具性质的辅助类或函数
- `enum_v3_11.py` 为 Python3.10 及以下版本增加 StrEnum

- 实现了编译器各模块：
- `asts.py` ：AST节点操作
- `cgen.py` ：QBE代码生成器
- `lexer.py` ：词法分析器
- `parser.py` ：语法分析器
- `stmts.py` ：语句处理
- `syms.py` ：符号表管理

- 创建了编译器入口文件：
- `app.py` ：实现命令行参数解析和编译流程控制
"""

from utils import Output, config, sh_exec
from asts import dump_ast, gen_ast
from lexer import Lexer
from parser import Parser
from cgen import codegen


def main():
    out_file = config.output or "bin"
    tmp_file = config.temp or "out.q"
    log_file = "stdout" if config.debug else "/dev/null"
    output = Output(tmp_file, log_file)
    in_file = config.input or "tests/test001.al"

    gen_qbe_code(in_file, output=output)
    if config.assemble or config.compile:
        sh_exec(f"qbe {tmp_file} > out.s")
    if config.compile:
        sh_exec(f"cc -o {out_file} out.s")


def gen_qbe_code(filename, output):
    """ 生成qbe代码 """
    # 生成代码
    print("\nParsing...", file=output.logFp)
    lexer = Lexer(filename)
    parser = Parser(lexer)
    print("\nTokens in {}:".format(filename), file=output.logFp)
    parser.queue.dump_tokens(output.logFp)

    ast = parser.parse_program()
    if ast:
        print("\nAST nodes in {}:\n".format(filename), file=output.logFp)
        dump_ast(ast, out=output.logFp)

    codegen.cg_file_preamble()
    gen_ast(ast)
    codegen.cg_file_postamble()
    print("\nGenerating code...\n", file=output.logFp)
    codegen.write_all(output.logFp)

    codegen.write_all(output.tmpFp)

    # 清理
    output.close()
    return


if __name__ == "__main__":
    main()
