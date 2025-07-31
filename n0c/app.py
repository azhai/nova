#!/usr/bin/env python3

"""
- 创建了核心数据结构文件：
- `alic.py` ：定义了编译器所需的枚举、类型和全局变量

- 实现了编译器各模块：
- `lexer.py` ：词法分析器
- `parser.py` ：语法分析器
- `astnodes.py` ：AST节点操作
- `cgen.py` ：QBE代码生成器
- `expr.py` ：表达式处理
- `funcs.py` ：函数处理
- `typs.py` ：类型系统
- `stmts.py` ：语句处理
- `syms.py` ：符号表管理
- `genast.py` ：AST代码生成
- `strlits.py` ：字符串字面量管理

- 创建了编译器入口文件：
- `main.py` ：实现命令行参数解析和编译流程控制
"""

import argparse

from defs import ASTNode, Output
from lexer import Lexer
# from parser import Parser
# from syms import gen_glob_syms
# from cgen import codegen
# from astnodes import dump_ast, free_ast


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Alic Compiler')
    parser.add_argument('input_file', help='Input source file')
    parser.add_argument('-o', '--output', help='Output file (default: out.q)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    output_file = args.output or 'out.q'
    output = Output(output_file)
    input_file = args.input_file or "tests/test001.al"

    lexer = Lexer(input_file)
    print("\nTokens in {}:".format(input_file), file=output.log)
    lexer.dump_tokens(output.log)
    print("\nTokens end", file=output.log)
    return

    # 生成代码
    print("\nParsing...", file=output.log)
    codegen.cg_file_preamble()
    ast = parse_program(input_file, output)
    codegen.cg_file_postamble()
    codegen.write_all(output.out)
    if ast:
        print("\nAST nodes in {}:\n".format(input_file), file=output.log)
        dump_ast(output.log, ast)
    print("\nGenerating code...\n", file=output.log)
    codegen.write_all(output.log)

    # 清理
    free_ast(ast)
    output.close()
    return


def parse_program(filename: str, output: Output) -> ASTNode | None:
    lexer = Lexer(filename)
    print("\nTokens in {}:".format(filename), file=output.log)
    lexer.dump_tokens(output.log)

    parser = Parser(lexer)
    ast = parser.parse_program()
    # 添加类型信息
    # print("Adding type information...", file=sys.stderr)
    # add_type(ast)
    gen_glob_syms()
    return ast


if __name__ == '__main__':
    main()
