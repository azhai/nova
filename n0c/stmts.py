from typing import Optional, Union

from defs import (
    ASTNode, NodeType, ValType, SymType, fatal,
    is_comparison, is_arithmetic, is_logical
)


def cast_node(node: ASTNode, new_type: ValType) -> Optional[ASTNode]:
    if not node or not new_type:
        return node
    # 创建类型转换节点
    if 0 < node.val_type.bytes() < 4:
        if node.val_type.is_unsigned():
            node.val_type = ValType.UINT32
        else:
            node.val_type = ValType.INT32
    if node.val_type == new_type:
        return node # 如果类型已经匹配，不需要转换
    new_node = ASTNode(NodeType.A_CAST, right=node)
    new_node.val_type = new_type
    return new_node


def widen_type(node: ASTNode, new_type: ValType) -> Optional[ASTNode]:
    if node.val_type == new_type:
        return node
    if node.val_type == ValType.VOID:
        fatal("cannot widen anything of type void")
    if new_type == ValType.BOOL:
        return None
    val_type = node.val_type
    # 整数和浮点数比较，使用浮点数的类型
    if new_type.is_float() and (val_type.is_integer() or val_type.is_unsigned()):
        return cast_node(node, new_type)
    bs1, bs2 = val_type.bytes(), new_type.bytes()
    if bs1 == 0 or bs2 == 0: # 有一个不能拓宽的类型
        return None
    if bs2 < bs1:
        return node
    if node.op == NodeType.A_LITERAL:
        if new_type.is_unsigned() and node.number < 0:
            fatal(f"Cannot cast negative literal value {node.number} to be unsigned")
        node.val_type = new_type
        return node
    if val_type.is_unsigned() != new_type.is_unsigned():
        return None
    return cast_node(node, new_type)


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

    left = widen_type(node.left, node.right.val_type)
    if left is not None:
        node.left = left
    right = widen_type(node.right, node.left.val_type)
    if right is not None:
        node.right = right
    node.val_type = node.left.val_type
    return node

    # if is_arithmetic(node.op.value) or is_logical(node.op.value):
    #     if node.right and node.right.val_type:
    #         node.val_type = node.right.val_type
    # elif node.op == NodeType.A_ASSIGN and node.right:
    #     node.val_type = node.right.val_type
    # elif node.op == NodeType.A_IDENT and node.sym:
    #     node.val_type = node.sym.val_type
    # elif node.op == NodeType.A_CALL and node.sym:
    #     if node.sym.sym_type == SymType.S_FUNC:
    #         node.val_type = node.sym.val_type
    # elif node.op == NodeType.A_LITERAL:
    #     if node.string == "" and isinstance(node.number, int):
    #         node.val_type = fit_int_type(node.number)
    # elif node.op == NodeType.A_CAST and node.right:
    #     if node.right.string == "" and isinstance(node.right.number, int):
    #         node.right.val_type = fit_int_type(node.right.number)
    # return node


def adjust_type(t1, t2: ValType) -> Optional[ValType]:
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


def parse_number(num: str) -> Union[int, float]:
    if num.startswith('0x') or num.startswith('0X'):
        return int(num, 16)
    elif num.startswith('0') and len(num) > 1:
        return int(num, 8)
    elif num.replace('.', '', 1).isdigit():
        return float(num)
    return int(num)
