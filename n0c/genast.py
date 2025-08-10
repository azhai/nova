from typing import Optional

from cgen import codegen
from defs import (ASTNode, NodeType, ValType, SymType, fatal,
                  is_arithmetic, is_logical, is_comparison)
from stmts import adjust_binary_node
from strlits import get_strlit_label


class UnaryOp(ASTNode):

    def __init__(self, op: NodeType, right):
        super().__init__(op, right)

    def gen(self) -> int:
        right = gen_ast(self.right)
        if self.op == NodeType.A_NEG:
            return codegen.cg_negate(right, self.val_type)
        elif self.op == NodeType.A_NOT:
            return codegen.cg_not(right, self.val_type)
        elif self.op == NodeType.A_INVERT:
            return codegen.cg_invert(right, self.val_type)
        else:
            fatal(f"Unary op {self.op} is not supported")
            return -1


class BinaryOp(ASTNode):

    def __init__(self, left, op: NodeType, right):
        super().__init__(op, left, right)
        adjust_binary_node(self)

    def gen(self) -> int:
        left, right = gen_ast(self.left), gen_ast(self.right)
        if is_arithmetic(self.op.value):
            return codegen.cg_arithmetic(self.op, left, right, self.val_type)
        elif is_logical(self.op.value):
            return codegen.cg_logical(self.op, left, right, self.val_type)
        elif is_comparison(self.op.value):
            return codegen.cg_comparison(self.op, left, right, self.val_type)
        else:
            fatal(f"Binary op {self.op} is not supported")
            return -1


class BlockNode(ASTNode):

    def __init__(self, left = None, right = None):
        super().__init__(NodeType.A_GLUE, left, right)

    def gen(self) -> int:
        # 处理语句块中的所有语句
        stmt_node = self.left
        last_temp = 0
        while stmt_node:
            last_temp = gen_ast(stmt_node)
            stmt_node = stmt_node.right
        return last_temp


class CallNode(ASTNode):

    def __init__(self, name, right = None):
        super().__init__(NodeType.A_CALL, right=right)
        self.string = name

    def gen(self) -> int:
        if not self.sym or self.sym.sym_type != SymType.S_FUNC:
            fatal(f"{self.sym.name if self.sym else '?'} is not a function")
        # 处理参数
        args: list[int] = []
        arg_types: list[ValType] = []
        arg_node = self.left
        while arg_node:
            arg_temp = gen_ast(arg_node)
            args.append(arg_temp)
            arg_types.append(arg_node.val_type)
            arg_node = arg_node.right
        # 调用函数
        return codegen.cg_call(self.sym, len(args), args, arg_types)


class IfNode(ASTNode):
    cond: ASTNode = None

    def __init__(self, cond, left, right = None):
        super().__init__(NodeType.A_IF, left, right)
        self.cond = cond

    def gen(self) -> int:
        label_else = codegen.gen_label()
        label_end = codegen.gen_label()
        cond = gen_ast(self.cond)
        codegen.cg_if_false(cond, label_else)
        gen_ast(self.left)
        codegen.cg_jump(label_end)
        codegen.cg_label(label_else)
        gen_ast(self.right)
        codegen.cg_label(label_end)
        return 0


class ForNode(ASTNode):
    cond: ASTNode = None

    def __init__(self, cond = None, init = None, incr = None, right = None):
        start = ASTNode(NodeType.A_GLUE, left=init, right=incr)
        super().__init__(NodeType.A_FOR, start, right)
        self.cond = cond

    def gen(self) -> int:
        label_start = codegen.gen_label()
        label_body = codegen.gen_label()
        label_end = codegen.gen_label()
        # 初始化语句
        if self.left and self.left.left:
            gen_ast(self.left.left)
        codegen.cg_label(label_start)
        # 条件判断
        if self.cond:
            cond = gen_ast(self.cond)
            codegen.cg_if_false(cond, label_end)
        # 循环体
        codegen.cg_label(label_body)
        gen_ast(self.right)
        # 更新语句
        if self.left and self.left.right:
            gen_ast(self.left.right)
        codegen.cg_jump(label_start)
        codegen.cg_label(label_end)
        return 0


class WhileNode(ForNode):

    def __init__(self, cond, right = None):
        super().__init__(NodeType.A_WHILE, right=right)
        self.cond = cond


class PrintfNode(ASTNode):

    def __init__(self, left = None, right = None):
        super().__init__(NodeType.A_PRINTF, left, right)

    def gen(self) -> int:
        expr_temp = gen_ast(self.right)
        # 根据类型选择合适的格式字符串
        label = get_strlit_label(self.left.string)
        codegen.cg_print(label, expr_temp, self.right.val_type)
        return 0


def gen_ast(node: Optional[ASTNode]) -> int:
    if not node:
        return 0
    if isinstance(node, (UnaryOp, BinaryOp, BlockNode, CallNode,
                         IfNode, ForNode, WhileNode, PrintfNode)):
        return node.gen()

    # 根据节点类型生成相应的代码
    if node.op == NodeType.A_VALUE and node.string == "":
        return codegen.cg_load_lit(node)
    elif node.op == NodeType.A_IDENT:
        return codegen.cg_load_var(node.sym)
    elif node.op == NodeType.A_ASSIGN:
        right_temp = gen_ast(node.right)
        codegen.cg_stor_var(right_temp, node.right.type, node.left.sym)
        return right_temp
    elif node.op == NodeType.A_CAST:
        right_temp = gen_ast(node.right)
        return codegen.cg_cast(right_temp, node.right.type, node.val_type)
    elif node.op == NodeType.A_LOCAL:
        codegen.cg_add_local(node.val_type, node.sym)
        if node.left:
            expr_temp = gen_ast(node.left)
            codegen.cg_stor_var(expr_temp, node.left.type, node.sym)
        return 0
    elif node.op == NodeType.A_RETURN:
        expr_temp = gen_ast(node.left)
        codegen.cg_ret(expr_temp)
        return expr_temp
    elif node.op == NodeType.A_GLUE:
        gen_ast(node.left)
        gen_ast(node.right)
        return 0
    else:
        fatal(f"Unknown AST node type: {node.op}")
        return 0

