from typing import Optional

from cgen import codegen, gen_label, cg_negate, cg_not, cg_invert
from defs import ASTNode, NodeType, ValType, SymType, fatal, is_arithmetic, is_logical, is_comparison
from strlits import get_strlit_label


class ASTCodeGenerator:
    unary_ops = {
        NodeType.A_NEG: cg_negate,
        NodeType.A_NOT: cg_not,
        NodeType.A_INVERT: cg_invert,
    }

    @classmethod
    def gen_ast(cls, node: Optional[ASTNode]) -> int:
        if not node:
            return 0

        # 根据节点类型生成相应的代码
        if node.op == NodeType.A_VALUE and node.string == "":
            return codegen.cg_load_lit(node)
        elif node.op == NodeType.A_IDENT:
            return codegen.cg_load_var(node.sym)
        elif node.op == NodeType.A_ASSIGN:
            right_temp = cls.gen_ast(node.right)
            codegen.cg_stor_var(right_temp, node.right.type, node.left.sym)
            return right_temp
        elif node.op == NodeType.A_CAST:
            right_temp = cls.gen_ast(node.right)
            return codegen.cg_cast(right_temp, node.right.type, node.val_type)
        elif node.op in (NodeType.A_NEG, NodeType.A_NOT, NodeType.A_INVERT):
            return cls.gen_unary(node)
        elif is_arithmetic(node.op.value):
            return cls.gen_arithmetic(node)
        elif is_logical(node.op.value):
            return cls.gen_logical(node)
        elif is_comparison(node.op.value):
            return cls.gen_comparison(node)
        elif node.op == NodeType.A_LOCAL:
            codegen.cg_add_local(node.val_type, node.sym)
            if node.left:
                expr_temp = cls.gen_ast(node.left)
                codegen.cg_stor_var(expr_temp, node.left.type, node.sym)
            return 0
        elif node.op == NodeType.A_IF:
            return cls.gen_if(node)
        elif node.op == NodeType.A_WHILE:
            return cls.gen_while(node)
        elif node.op == NodeType.A_FOR:
            return cls.gen_for(node)
        elif node.op == NodeType.A_CALL:
            return cls.gen_func_call(node)
        elif node.op == NodeType.A_RETURN:
            expr_temp = cls.gen_ast(node.left)
            codegen.cg_ret(expr_temp)
            return expr_temp
        elif node.op == NodeType.A_BLOCK:
            # 处理语句块中的所有语句
            stmt_node = node.left
            last_temp = 0
            while stmt_node:
                last_temp = cls.gen_ast(stmt_node)
                stmt_node = stmt_node.right
            return last_temp
        elif node.op == NodeType.A_PRINTF:
            expr_temp = cls.gen_ast(node.right)
            # 根据类型选择合适的格式字符串
            # if is_integer(node.left.type):
            #     label = get_strlit_label("%d\n")
            # elif is_float(node.left.type):
            #     label = get_strlit_label("%f\n")
            # else:
            #     fatal(f"Unsupported type for print: {node.left.type}")
            label = get_strlit_label(node.left.string)
            codegen.cg_print(label, expr_temp, node.right.val_type)
            return 0
        elif node.op == NodeType.A_GLUE:
            cls.gen_ast(node.left)
            cls.gen_ast(node.right)
            return 0
        else:
            fatal(f"Unknown AST node type: {node.op}")
            return 0

    @classmethod
    def gen_unary(cls, node: ASTNode) -> int:
        op = cls.unary_ops.get(node.op)
        rt = cls.gen_ast(node.right)
        return op(rt, node.val_type)

    @classmethod
    def gen_arithmetic(cls, node: ASTNode) -> int:
        lt, rt = cls.gen_ast(node.left), cls.gen_ast(node.right)
        return codegen.cg_arithmetic(node.op, lt, rt, node.val_type)

    @classmethod
    def gen_logical(cls, node: ASTNode) -> int:
        lt, rt = cls.gen_ast(node.left), cls.gen_ast(node.right)
        return codegen.cg_logical(node.op, lt, rt, node.val_type)

    @classmethod
    def gen_comparison(cls, node: ASTNode) -> int:
        lt, rt = cls.gen_ast(node.left), cls.gen_ast(node.right)
        return codegen.cg_comparison(node.op, lt, rt, node.val_type)

    @classmethod
    def gen_if(cls, node: ASTNode) -> int:
        cond_temp = cls.gen_ast(node.left)
        label_else = gen_label()
        label_end = gen_label()
        codegen.cg_if_false(cond_temp, label_else)
        cls.gen_ast(node.right.left)
        codegen.cg_jump(label_end)
        codegen.cg_label(label_else)
        cls.gen_ast(node.right.right)
        codegen.cg_label(label_end)
        return 0

    @classmethod
    def gen_while(cls, node: ASTNode) -> int:
        label_start = gen_label()
        label_body = gen_label()
        label_end = gen_label()
        codegen.cg_label(label_start)
        cond_temp = cls.gen_ast(node.left)
        codegen.cg_if_false(cond_temp, label_end)
        codegen.cg_label(label_body)
        cls.gen_ast(node.right)
        codegen.cg_jump(label_start)
        codegen.cg_label(label_end)
        return 0

    @classmethod
    def gen_for(cls, node: ASTNode) -> int:
        # 初始化语句
        cls.gen_ast(node.left.left)
        label_start = gen_label()
        label_body = gen_label()
        label_end = gen_label()
        codegen.cg_label(label_start)
        # 条件判断
        if node.left.right:
            cond_temp = cls.gen_ast(node.left.right)
            codegen.cg_if_false(cond_temp, label_end)
        codegen.cg_label(label_body)
        # 循环体
        cls.gen_ast(node.right.left)
        # 更新语句
        if node.right.right:
            cls.gen_ast(node.right.right)
        codegen.cg_jump(label_start)
        codegen.cg_label(label_end)
        return 0

    @classmethod
    def gen_func_call(cls, node: ASTNode) -> int:
        if not node.sym or node.sym.sym_type != SymType.S_FUNC:
            fatal(f"{node.sym.name if node.sym else '?'} is not a function")
        # 处理参数
        args: list[int] = []
        arg_types: list[ValType] = []
        arg_node = node.left
        while arg_node:
            arg_temp = cls.gen_ast(arg_node)
            args.append(arg_temp)
            arg_types.append(arg_node.val_type)
            arg_node = arg_node.right
        # 调用函数
        return codegen.cg_call(node.sym, len(args), args, arg_types)


gen_ast = ASTCodeGenerator.gen_ast
