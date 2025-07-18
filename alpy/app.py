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

from defs import fatal, init_global_vars
from astnodes import dump_ast
from cgen import cg_file_preamble
from lexer import Lexer
from parser import Parser
from strlits import gen_strlits
from syms import gen_glob_syms


def main():
    # 初始化全局变量
    init_global_vars()

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Alic Compiler')
    parser.add_argument('input_file', help='Input source file')
    parser.add_argument('-o', '--output', help='Output file (default: out.ssa)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    # 设置输出文件
    output_file = args.output or 'out.ssa'
    try:
        Outfh = open(output_file, 'w')
    except IOError as e:
        fatal(f"Cannot open output file {output_file}: {e}")

    # 设置调试文件
    if args.debug:
        try:
            Debugfh = open('debug.log', 'w')
        except IOError as e:
            fatal(f"Cannot open debug file: {e}")
    else:
        Debugfh = None

    # 解析程序
    print("Parsing...", file=sys.stderr)
    filename = args.input_file or "tests/test001.al"
    lexer = Lexer(filename)
    lexer.dump_tokens()

    parser = Parser(lexer)
    nodes = parser.parse_program()
    print("\nAST nodes:")
    for ast in nodes:
        dump_ast(None, ast)
    # print(repr(ast))
    # genAST(ast)
    # if not ast:
    #     fatal("Parse failed")
    return

    # 添加类型信息
    print("Adding type information...", file=sys.stderr)
    # add_type(ast)

    # 生成代码
    print("Generating code...", file=sys.stderr)
    cg_file_preamble()
    gen_glob_syms()
    gen_strlits()
    gen_func_statement_block(None, ast)

    # 清理
    Outfh.close()
    if Debugfh:
        Debugfh.close()
    print(f"Compilation successful. Output written to {output_file}", file=sys.stderr)


if __name__ == '__main__':
    main()
