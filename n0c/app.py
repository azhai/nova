#!/usr/bin/env python3

"""
- 创建了核心数据结构文件：
- `defs.py` ：定义了编译器所需的枚举、类型和全局变量
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

import argparse
from typing import Optional

from defs import parse_cmd_args, ASTNode, Output
from asts import dump_ast, gen_ast
from lexer import Lexer
from parser import Parser
from cgen import codegen
# from syms import gen_global_syms


def main():
    config = parse_cmd_args()
    outfile = config.output or "out.q"
    logfile = "stdout" if config.debug else "/dev/null"
    output = Output(outfile, logfile)
    input_file = config.input_file or "tests/test001.al"

    # 生成代码
    print("\nParsing...", file=output.logFp)
    ast = parse_program(input_file, output)
    if ast:
        print("\nAST nodes in {}:\n".format(input_file), file=output.logFp)
        dump_ast(ast, out=output.logFp)

    codegen.cg_file_preamble()
    gen_ast(ast)
    codegen.cg_file_postamble()
    print("\nGenerating code...\n", file=output.logFp)
    codegen.write_all(output.logFp)

    codegen.write_all(output.outFp)

    # 清理
    output.close()
    return


def parse_program(filename: str, output: Output) -> Optional[ASTNode]:
    lexer = Lexer(filename)
    parser = Parser(lexer)
    print("\nTokens in {}:".format(filename), file=output.logFp)
    parser.queue.dump_tokens(output.logFp)

    ast = parser.parse_program()
    # gen_global_syms()
    return ast


if __name__ == "__main__":
    main()
