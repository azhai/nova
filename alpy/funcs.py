from typing import List

from defs import Sym, SymType, DataType, ASTNode, ASTNodeType, fatal
from cgen import cg_func_preamble, cg_func_postamble
from genast import gen_ast
from syms import add_symbol, find_symbol, set_cur_func


class FuncProcessor:
    @staticmethod
    def add_function(name: str, val_type: DataType, params: List[Sym]) -> Sym:
        # 检查函数是否已存在
        existing = find_symbol(name)
        if existing:
            if existing.sym_type != SymType.SYM_FUNC:
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
        fn_sym = Sym(
            name=name,
            sym_type=SymType.SYM_FUNC,
            val_type=val_type
        )
        fn_sym.params = params
        # 添加到符号表
        add_symbol(fn_sym, True)
        return fn_sym

    @classmethod
    def declare_function(cls, name: str, val_type: DataType, params: List[Sym], body: ASTNode) -> ASTNode:
        # 添加函数到符号表
        fn_sym = cls.add_function(name, val_type, params)
        # 设置当前函数
        set_cur_func(fn_sym)

        # fn_sym = find_symbol(name)
        fn_sym.init_val.int_val = 1

        # 创建函数节点
        node = ASTNode(
            op=ASTNodeType.A_FUNCTION,
            left=body,
            right=None,
            type=val_type,
            sym=fn_sym
        )
        return node

    @staticmethod
    def gen_func_statement_block(fn_sym: Sym, body: ASTNode) -> None:
        if not fn_sym or not body:
            return
        # 生成函数前导
        cg_func_preamble(fn_sym)
        # 生成函数体
        gen_ast(body)
        # 生成函数后导
        cg_func_postamble()


func_processor = FuncProcessor()
add_function = func_processor.add_function
declare_function = func_processor.declare_function
gen_func_statement_block = func_processor.gen_func_statement_block
