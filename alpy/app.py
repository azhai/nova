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
import sys
from astnodes import dump_ast
from cgen import cg_file_preamble, cg_file_postamble
from defs import init_global_vars, close_all_files, ASTNode
from lexer import Lexer
from parser import Parser
from strlits import gen_strlits
from syms import gen_glob_syms


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Alic Compiler')
    parser.add_argument('input_file', help='Input source file')
    parser.add_argument('-o', '--output', help='Output file (default: out.q)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    output_file = init_global_vars(args)
    print("Parsing...", file=sys.stderr)
    input_file = args.input_file or "tests/test001.al"

    # 生成代码
    print("Generating code...", file=sys.stderr)
    cg_file_preamble()
    ast = parse_program(input_file)
    print("\nAST nodes:")
    dump_ast(None, ast)
    cg_file_postamble()

    # 清理
    close_all_files(output_file)


def parse_program(filename: str) -> ASTNode|None:
    lexer = Lexer(filename)
    lexer.dump_tokens()
    print("")

    parser = Parser(lexer)
    ast = parser.parse_program()
    gen_strlits()
    gen_glob_syms()

    # 添加类型信息
    # print("Adding type information...", file=sys.stderr)
    # add_type(ast)
    return ast


if __name__ == '__main__':
    main()
