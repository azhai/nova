from typing import Optional

from cgen import (
    cgloadlit, cgloadvar, cgstorvar, cgadd, cgsub, cgmul, cgdiv,
    cgnegate, cgcompare, cgjump, cgjump_if_false, cgnot, cginvert,
    cgand, cgor, cgxor, cgshl, cgshr, cgcall, cgprint, cgaddlocal,
    gen_label, cglabel, cgret
)
from defs import ASTNode, ASTNodeType, DataType, SymType, fatal
from strlits import get_strlit_label


class ASTCodeGenerator:
    @classmethod
    def gen_ast(cls, node: Optional[ASTNode]) -> int:
        if not node:
            return 0

        # 根据节点类型生成相应的代码
        if node.op == ASTNodeType.A_NUMLIT:
            return cgloadlit(node.numlit, node.type)
        elif node.op == ASTNodeType.A_IDENT:
            return cgloadvar(node.sym)
        elif node.op == ASTNodeType.A_ASSIGN:
            right_temp = cls.gen_ast(node.right)
            cgstorvar(right_temp, node.right.type, node.left.sym)
            return right_temp
        elif node.op == ASTNodeType.A_ADD:
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgadd(left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_SUBTRACT:
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgsub(left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_MULTIPLY:
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgmul(left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_DIVIDE:
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgdiv(left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_NEGATE:
            right_temp = cls.gen_ast(node.right)
            return cgnegate(right_temp, node.type)
        elif node.op in (ASTNodeType.A_EQ, ASTNodeType.A_NE, ASTNodeType.A_LT, ASTNodeType.A_GT, ASTNodeType.A_LE,
                         ASTNodeType.A_GE):
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgcompare(node.op, left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_IF:
            cond_temp = cls.gen_ast(node.left)
            label_else = gen_label()
            label_end = gen_label()
            cgjump_if_false(cond_temp, label_else)
            cls.gen_ast(node.right.left)
            cgjump(label_end)
            cglabel(label_else)
            cls.gen_ast(node.right.right)
            cglabel(label_end)
            return 0
        elif node.op == ASTNodeType.A_WHILE:
            label_start = gen_label()
            label_body = gen_label()
            label_end = gen_label()
            cglabel(label_start)
            cond_temp = cls.gen_ast(node.left)
            cgjump_if_false(cond_temp, label_end)
            cglabel(label_body)
            cls.gen_ast(node.right)
            cgjump(label_start)
            cglabel(label_end)
            return 0
        elif node.op == ASTNodeType.A_FOR:
            # 初始化语句
            cls.gen_ast(node.left.left)
            label_start = gen_label()
            label_body = gen_label()
            label_end = gen_label()
            cglabel(label_start)
            # 条件判断
            if node.left.right:
                cond_temp = cls.gen_ast(node.left.right)
                cgjump_if_false(cond_temp, label_end)
            cglabel(label_body)
            # 循环体
            cls.gen_ast(node.right.left)
            # 更新语句
            if node.right.right:
                cls.gen_ast(node.right.right)
            cgjump(label_start)
            cglabel(label_end)
            return 0
        elif node.op in (ASTNodeType.A_PRINT, ASTNodeType.A_PRINTF):
            expr_temp = cls.gen_ast(node.right)
            # 根据类型选择合适的格式字符串
            # if is_integer(node.left.type):
            #     label = get_strlit_label("%d\n")
            # elif is_float(node.left.type):
            #     label = get_strlit_label("%f\n")
            # else:
            #     fatal(f"Unsupported type for print: {node.left.type}")
            label = get_strlit_label(node.left.strlit)
            cgprint(label, expr_temp, node.right.type)
            return 0
        elif node.op == ASTNodeType.A_LOCAL:
            cgaddlocal(node.type, node.sym)
            if node.left:
                expr_temp = cls.gen_ast(node.left)
                cgstorvar(expr_temp, node.left.type, node.sym)
            return 0
        elif node.op == ASTNodeType.A_FUNCCALL:
            if not node.sym or node.sym.sym_type != SymType.SYM_FUNC:
                fatal(f"{node.sym.name if node.sym else '?'} is not a function")
            # 处理参数
            args: list[int] = []
            arg_types: list[DataType] = []
            arg_node = node.left
            while arg_node:
                arg_temp = cls.gen_ast(arg_node)
                args.append(arg_temp)
                arg_types.append(arg_node.type)
                arg_node = arg_node.right
            # 调用函数
            return cgcall(node.sym, len(args), args, arg_types)
        elif node.op == ASTNodeType.A_RETURN:
            expr_temp = cls.gen_ast(node.left)
            cgret(expr_temp)
            return expr_temp
        elif node.op == ASTNodeType.A_BLOCK:
            # 处理语句块中的所有语句
            stmt_node = node.left
            last_temp = 0
            while stmt_node:
                last_temp = cls.gen_ast(stmt_node)
                stmt_node = stmt_node.right
            return last_temp
        elif node.op == ASTNodeType.A_NOT:
            right_temp = cls.gen_ast(node.right)
            return cgnot(right_temp, node.type)
        elif node.op == ASTNodeType.A_INVERT:
            right_temp = cls.gen_ast(node.right)
            return cginvert(right_temp, node.type)
        elif node.op == ASTNodeType.A_AND:
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgand(left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_OR:
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgor(left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_XOR:
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgxor(left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_LSHIFT:
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgshl(left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_RSHIFT:
            left_temp = cls.gen_ast(node.left)
            right_temp = cls.gen_ast(node.right)
            return cgshr(left_temp, right_temp, node.type)
        elif node.op == ASTNodeType.A_CAST:
            from cgen import cgcast
            right_temp = cls.gen_ast(node.right)
            return cgcast(right_temp, node.right.type, node.type)
        else:
            fatal(f"Unknown AST node type: {node.op}")
            return 0


gen_ast = ASTCodeGenerator.gen_ast
