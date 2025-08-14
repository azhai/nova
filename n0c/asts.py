import sys
from typing import Optional

from defs import (
    ASTNode, NodeType, ValType, SymType, Symbol, fatal,
    is_arithmetic, is_logical, is_comparison, quote_string
)
from cgen import codegen, get_str_lit_label
from stmts import adjust_binary_node, widen_type
from syms import curr_scope


class UnaryOp(ASTNode):

    def __init__(self, op: NodeType, right):
        super().__init__(op, right=right)
        self.val_type = self.right.val_type

    def gen(self) -> int:
        right = gen_ast(self.right)
        if self.op in (NodeType.A_NEG, NodeType.A_SUB):
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
        super().__init__(op, left=left, right=right)
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


class AssignNode(ASTNode):

    def __init__(self, left = None, right = None):
        if left and right:
            val_type, new_type = right.val_type, left.sym.val_type
            right = widen_type(right, new_type)
            if right is None:
                fatal(f"Incompatible types {val_type} vs {new_type}")
        super().__init__(NodeType.A_ASSIGN, left, right)

    def gen(self) -> int:
        gen_ast(self.left)
        val_type, sym = self.left.val_type, self.left.sym
        right = gen_ast(self.right)
        codegen.cg_stor_var(right, val_type, sym)
        return right


class BlockNode(ASTNode):

    def __init__(self, left = None, right = None):
        super().__init__(NodeType.A_GLUE, left, right)

    def gen(self) -> int:
        # 处理语句块中的所有语句
        stmt_node = self.left
        last = 0
        while stmt_node:
            last = gen_ast(stmt_node)
            stmt_node = stmt_node.right
        return last


class CallNode(ASTNode):
    sym: Optional[Symbol] = None

    def __init__(self, name, node):
        super().__init__(NodeType.A_CALL)
        self.name, self.args = name, node.args or []

    def __repr__(self) -> str:
        return f"{self.op_name()} {self.name}(...)"

    def gen(self) -> int:
        if not self.sym or self.sym.sym_type != SymType.S_FUNC:
            func_name = self.sym.name if self.sym else "?"
            fatal(f"{func_name} is not a function")
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


class LiteralNode(ASTNode):
    number, string = 0, ""

    def __init__(self, text: str = "", val_type: ValType = ValType.STR):
        super().__init__(NodeType.A_LITERAL)
        self.val_type, self.string = val_type, text

    def __repr__(self) -> str:
        if self.val_type and self.val_type == ValType.STR:
            value = quote_string(self.string)
        else:
            value = self.number
        return f"{self.op_name()} {self.type_name()} ({value})"

    def gen(self) -> int:
        if self.val_type == ValType.STR:
            return codegen.cg_load_lit(self.string, self.val_type)
        else:
            return codegen.cg_load_lit(self.number, self.val_type)


class IdentNode(ASTNode):
    name: str
    node_type: NodeType = NodeType.A_IDENT
    sym_type: SymType = SymType.S_LOCAL
    sym: Optional[Symbol] = None

    def __init__(self, name: str, val_type: Optional[ValType] = None):
        super().__init__(self.node_type)
        self.name, self.val_type = name, val_type

    def __repr__(self) -> str:
        return f"{self.op_name()} {self.type_name()} {self.name}"

    def gen(self) -> int:
        if self.sym:
            return codegen.cg_load_var(self.sym)
        return 0

    def new_symbol(self):
        if not self.name or not self.val_type:
            return None
        if self.sym is None:
            self.sym = Symbol(self.name, self.val_type, self.sym_type)
            self.sym.has_addr = True
            curr_scope.add_symbol(self.sym, self.sym_type == SymType.S_FUNC)
        return self.sym

    def get_symbol(self):
        if not self.name:
            return None
        if not self.sym:
            self.sym = curr_scope.find_symbol(self.name)
            if self.sym:
                # self.sym.has_addr = False
                self.val_type = self.sym.val_type
        return self.sym

    def set_symbol(self, sym):
        self.sym = sym
        if sym and sym.name:
            self.name = sym.name
        if sym and sym.val_type:
            self.val_type = sym.val_type
        return self.sym

    def add_right(self, right: ASTNode):
        if right is None:
            return
        val_type, new_type = right.val_type, self.val_type
        self.right = widen_type(right, new_type)
        if self.right is None:
            fatal(f"Incompatible types {val_type} vs {new_type}")


class VariableNode(IdentNode):
    node_type: NodeType = NodeType.A_LOCAL
    sym_type: SymType = SymType.S_VAR

    @classmethod
    def from_ident(cls, node: IdentNode, right = None):
        obj = cls(node.name, node.val_type)
        if right:
            obj.add_right(right)
        obj.new_symbol()
        return obj

    def gen(self) -> int:
        sym = self.left.sym if self.left else self.sym
        result = codegen.cg_add_local(sym.val_type, sym)
        if self.right:
            right = gen_ast(self.right)
            codegen.cg_stor_var(right, sym.val_type, sym)
        return result


class FunctionNode(IdentNode):
    node_type: NodeType = NodeType.A_FUNC
    sym_type: SymType = SymType.S_FUNC

    def __repr__(self) -> str:
        params = ", ".join([f"{x.type_name()} {x.name}" for x in self.args])
        return f"{self.op_name()} {self.type_name()} {self.name}({params})"

    def gen(self) -> int:
        # 生成函数前导
        curr_scope.new_scope(self.sym.name)
        codegen.cg_func_preamble(self)
        # 生成函数体
        result = gen_ast(self.left)
        # 生成函数后导
        codegen.cg_func_postamble()
        curr_scope.end_scope()
        return result


class IfNode(ASTNode):
    cond: ASTNode = None

    def __init__(self, cond, left, right = None):
        super().__init__(NodeType.A_IF, left, right)
        self.cond = cond

    def gen(self) -> int:
        label_else = codegen.gen_label()
        cond = gen_ast(self.cond)
        codegen.cg_if_false(cond, label_else)
        gen_ast(self.left)
        if self.right:
            label_end = codegen.gen_label()
            codegen.cg_label(codegen.gen_label())
            codegen.cg_jump(label_end)
            codegen.cg_label(label_else)
            gen_ast(self.right)
            codegen.cg_label(label_end)
        else:
            codegen.cg_label(label_else)
        return 0


class WhileNode(ASTNode):
    node_type: NodeType = NodeType.A_WHILE
    cond: ASTNode = None

    def __init__(self, cond, right = None):
        super().__init__(self.node_type, right=right)
        self.cond = cond

    def gen(self) -> int:
        label_start = codegen.gen_label()
        label_end = codegen.gen_label()
        codegen.cg_label(label_start)
        # 条件判断
        if self.cond:
            cond = gen_ast(self.cond)
            codegen.cg_if_false(cond, label_end)
        # 循环体
        gen_ast(self.right)
        codegen.cg_jump(label_start)
        codegen.cg_label(label_end)
        return 0


class ForNode(WhileNode):
    node_type: NodeType = NodeType.A_FOR

    def __init__(self, cond = None, init = None, right = None, incr = None):
        if right is None:
            right = ASTNode(NodeType.A_GLUE)
        super().__init__(cond, right=right)
        self.left, self.right.right = init, incr

    def gen(self) -> int:
        # 初始化语句
        if self.left:
            gen_ast(self.left)
        super().gen()
        return 0


class PrintfNode(ASTNode):

    def __init__(self, left = None, right = None):
        super().__init__(NodeType.A_PRINTF, left, right)

    def gen(self) -> int:
        # 根据类型选择合适的格式字符串
        label = get_str_lit_label(self.left.string)
        expr, val_type = gen_ast(self.right), self.right.val_type
        codegen.cg_print(label, expr, val_type)
        return 0


def gen_ast(node: Optional[ASTNode]) -> int:
    if not node:
        return 0
    if type(node) != ASTNode:
        return node.gen()

    # 根据节点类型生成相应的代码
    if node.op == NodeType.A_GLUE:
        if node.left:
            gen_ast(node.left)
        for arg in node.args:
            gen_ast(arg)
        if node.right:
            gen_ast(node.right)
        return 0
    elif node.op == NodeType.A_CAST:
        right_temp = gen_ast(node.right)
        val_type, new_type = node.right.val_type, node.val_type
        return codegen.cg_cast(right_temp, val_type, new_type)
    elif node.op == NodeType.A_RETURN:
        expr_temp = gen_ast(node.left)
        codegen.cg_ret(expr_temp)
        return expr_temp
    else:
        fatal(f"Unknown AST node type: {node.op}")
        return 0


def dump_ast(node: Optional[ASTNode], level: int = 0, out = "", pre = ""):
    if node is None:
        fatal("NULL AST node")
        return

    # Print indentation
    if out is None:
        out = sys.stdout
    out.write(" " * level)
    # out.write(pre)

    # Print type and operation name
    out.write(repr(node))

    out.write("\n")
    # Adjust level for local nodes
    # new_level = level + 2 if node.op != NodeType.A_LOCAL else level - 2
    new_level = level + 3
    # Recursively dump children
    if node.left:
        dump_ast(node.left, new_level, out=out, pre="->")
    if node.op != NodeType.A_FUNC:
        for arg in node.args:
            dump_ast(arg, new_level, out=out, pre="--")
    if node.right:
        dump_ast(node.right, new_level, out=out, pre="=>")


