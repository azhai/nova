from typing import Optional

from defs import (
    ASTNode, NodeType, ValType, Symbol, SymType, fatal,
    is_comparison, is_arithmetic, is_logical
)
from syms import add_symbol


def binary_op(left: ASTNode, op: NodeType, right: ASTNode) -> ASTNode:
    node = ASTNode(op, left=left, right=right)
    return adjust_binary_node(node)


def cast_node(node: ASTNode, new_type: ValType) -> ASTNode | None:
    if not node or not new_type:
        return None
    if node.val_type == new_type:
        return node # 如果类型已经匹配，不需要转换
    # 创建类型转换节点
    node = ASTNode(NodeType.A_CAST, right=node)
    node.val_type = new_type
    return node


def adjust_binary_node(node: ASTNode, force = False) -> ASTNode:
    # 已经有类型的节点，不需要调整
    if node is None or not force and node.val_type:
        return node
    # 比较运算结果为bool类型
    if is_comparison(node.op.value):
        node.val_type = ValType.BOOL
        return node
    # 递归处理子节点
    node.left = adjust_binary_node(node.left)
    node.right = adjust_binary_node(node.right)

    if is_arithmetic(node.op.value) or is_logical(node.op.value):
        if node.right and node.right.val_type:
            node.val_type = node.right.val_type
    elif node.op == NodeType.A_ASSIGN and node.right:
        node.val_type = node.right.val_type
    elif node.op == NodeType.A_IDENT and node.sym:
        node.val_type = node.sym.val_type
    elif node.op == NodeType.A_CALL and node.sym:
        if node.sym.sym_type == SymType.S_FUNC:
            node.val_type = node.sym.val_type
    elif node.op == NodeType.A_VALUE:
        if node.string == "" and isinstance(node.number, int):
            node.val_type = fit_int_type(node.number)
    elif node.op == NodeType.A_CAST and node.right:
        if node.right.string == "" and isinstance(node.right.number, int):
            node.right.val_type = fit_int_type(node.right.number)
    return node


def widen_type(t1, t2: ValType) -> ValType|None:
    if t1 == t2:
        return t1
    if t1 in (ValType.VOID, ValType.BOOL):
        return t2
    if t2 in (ValType.VOID, ValType.BOOL):
        return t1
    bs1, bs2 = t1.bytes(), t2.bytes()
    if bs1 == 0 or bs2 == 0: # 有一个不能拓宽的类型
        return None
    # 整数和浮点数比较，使用浮点数的类型
    if t1 == ValType.FLOAT64 or t2 == ValType.FLOAT64:
        return ValType.FLOAT64
    if t1 == ValType.FLOAT32 or t2 == ValType.FLOAT32:
        return ValType.FLOAT32
    # 同系列整数比较，使用字节数多的类型
    if t1.name[:3] == t2.name[:3]:
        return t1 if bs1 >= bs2 else t2
    return None


def fit_int_type(num: int, unsigned = False) -> ValType:
    if num < 0:
        if num >= 0 - 2**7:
            return ValType.INT8
        if num >= 0 - 2**15:
            return ValType.INT16
        if num >= 0 - 2**31:
            return ValType.INT32
        return ValType.INT64
    elif not unsigned:
        if num <= 2**7 - 1:
            return ValType.INT8
        if num <= 2**15 -1:
            return ValType.INT16
        if num <= 2**31 - 1:
            return ValType.INT32
        return ValType.INT64
    else:
        if num <= 2**8 - 1:
            return ValType.UINT8
        if num <= 2**16 -1:
            return ValType.UINT16
        if num <= 2**32 - 1:
            return ValType.UINT32
        return ValType.UINT64


def set_int_node(node: ASTNode, force = False) -> ASTNode:
    if node.op != NodeType.A_VALUE:
        return node
    if node.val_type.is_integer():
        node.val_type = fit_int_type(node.number, False)
    elif node.val_type.is_unsigned():
        node.val_type = fit_int_type(node.number, True)
    return node


def parse_number(num: str) -> int|float:
    if num.startswith('0x') or num.startswith('0X'):
        return int(num, 16)
    elif num.startswith('0') and len(num) > 1:
        return int(num, 8)
    elif num.replace('.', '', 1).isdigit():
        return float(num)
    return int(num)



class StmtProcessor:
    @staticmethod
    def printf_statement(expr: ASTNode) -> ASTNode:
        if not expr:
            return None

        # 拓宽表达式类型
        expr = set_int_node(expr)

        # 对于float32类型，拓宽为float64
        if expr.val_type == ValType.FLOAT32:
            expr = cast_node(expr, ValType.FLOAT64)

        # 创建打印语句AST节点
        node = ASTNode(NodeType.A_PRINTF, left=expr)
        node.val_type = ValType.VOID
        return node

    @staticmethod
    def assignment_statement(val: ASTNode, expr: ASTNode) -> ASTNode:
        if not val or not expr or val.op != NodeType.A_IDENT:
            fatal("Invalid assignment target")

        # 拓宽表达式类型
        expr = set_int_node(expr)
        # 拓宽左值类型
        val = set_int_node(val)

        # 确保类型兼容
        if val.val_type != expr.val_type:
            new_type = widen_type(val.val_type, expr.val_type)
            if new_type is None:
                fatal(f"Type mismatch in assignment: {val.val_type} and {expr.val_type}")
            # 转换表达式类型以匹配左值类型
            if expr.val_type != new_type:
                expr = cast_node(expr, new_type)
            # 更新左值类型
            val.val_type = new_type

        # 创建赋值语句AST节点
        node = ASTNode(NodeType.A_ASSIGN, left=val, right=expr)
        node.val_type = val.val_type
        return node

    @staticmethod
    def declaration_statement(val_type:ValType, name: str, expr: Optional[ASTNode]) -> ASTNode:
        # 检查符号是否已存在
        from syms import find_symbol
        existing = find_symbol(name)
        if existing:
            fatal(f"Symbol {name} already declared")

        # 创建新符号
        sym = Symbol(name, sym_type=SymType.S_VAR, val_type=val_type)
        # 添加到符号表
        add_symbol(sym)

        # 如果有初始化表达式，处理类型拓宽
        if expr:
            expr = set_int_node(expr)
            # 确保类型兼容
            if val_type != expr.val_type:
                new_type = widen_type(val_type, expr.val_type)
                if new_type is None:
                    fatal(f"Type mismatch in declaration of {name}: {val_type} and {expr.val_type}")
                # 转换表达式类型
                expr = cast_node(expr, new_type)
                # 更新变量类型
                sym.val_type = val_type = new_type
            # 保存初始值
            if expr.op == NodeType.A_VALUE:
                sym.init_val = expr.string if expr.string else expr.number

        # 创建声明语句AST节点
        node = ASTNode(NodeType.A_LOCAL, left=expr, right=None)
        node.val_type, node.sym = val_type, sym
        return node


def gen_stat_assign(val: ASTNode, expr: ASTNode) -> ASTNode:
    """ 创建赋值语句AST节点 """
    expr = cast_node(expr, val.val_type)
    node = ASTNode(
        op=NodeType.A_ASSIGN,
        left=expr,
        right=None
    )
    node.val_type = val.sym.val_type
    node.rvalue = False
    return node


def gen_stat_printf(first: ASTNode, expr: ASTNode) -> ASTNode:
    """ 创建打印语句AST节点 """
    if expr.val_type == ValType.FLOAT32:
        expr = cast_node(expr, ValType.FLOAT64)
    node = ASTNode(NodeType.A_PRINTF, left=first, right=expr)
    return node


def gen_stat_declare(ident: ASTNode, expr: ASTNode) -> ASTNode:
    """ 创建声明语句AST节点 """
    val_type = ident.sym.val_type
    expr = cast_node(expr, val_type)
    # 添加到符号表
    sym = Symbol(ident.sym.name, SymType.S_VAR, val_type=val_type)
    sym.has_addr = True
    add_symbol(sym)
    # 改造ident
    ident.sym, ident.val_type = sym, val_type
    ident.op, ident.left = NodeType.A_LOCAL, expr
    return ident
