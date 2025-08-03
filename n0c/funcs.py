from typing import List

from cgen import codegen
from defs import Symbol, SymType, ValType, ASTNode, NodeType, fatal
from genast import gen_ast
from syms import add_symbol, find_symbol, set_cur_func


def add_function(node: ASTNode, params: List[Symbol]) -> Symbol:
    name = node.sym.name
    # 检查函数是否已存在
    existing = find_symbol(name)
    if existing:
        if existing.sym_type != SymType.S_FUNC:
            fatal(f"{name} is not a function")
        # 检查参数数量是否匹配
        # existing_params = existing.memb
        # param_count = 0
        # while existing_params:
        #     param_count += 1
        #     existing_params = existing_params.sibling
        # if len(params) != param_count:
        #     fatal(f"Function {name} redefined with different parameter count")
        # # 检查参数类型是否匹配
        # existing_params = existing.memb
        # for i, param in enumerate(params):
        #     if existing_params.type != param.type:
        #         fatal(f"Parameter {i + 1} type mismatch in function {name} redefinition")
        #     existing_params = existing_params.sibling
        return existing

    # 创建新函数符号
    fn_sym = Symbol(name, sym_type=SymType.S_FUNC, val_type=node.val_type)
    fn_sym.params = params
    return fn_sym


def declare_function(node: ASTNode, params: List[Symbol], body: ASTNode) -> ASTNode:
    # 添加函数到符号表
    fn_sym = add_function(node, params)
    # 创建函数节点
    node = ASTNode(NodeType.A_FUNC, left=body)
    node.sym, node.val_type = fn_sym, fn_sym.val_type
    return node


def gen_func_statement_block(fn_sym: Symbol, body: ASTNode) -> None:
    if not fn_sym or not body:
        return
    # 生成函数前导
    codegen.cg_func_preamble(fn_sym)
    # 生成函数体
    gen_ast(body)
    # 生成函数后导
    codegen.cg_func_postamble()
