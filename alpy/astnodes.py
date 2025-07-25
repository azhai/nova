import sys
from typing import Optional

from defs import ASTNode, ASTNodeType, TypeKind, fatal, quote_string
from typs import TypeProcessor

_astname = [
    None,  # 0
    "ASSIGN", "CAST",  # 1-2
    "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "NEGATE",  # 3-7
    "EQ", "NE", "LT", "GT", "LE", "GE", "NOT",  # 8-14
    "AND", "OR", "XOR", "INVERT",  # 15-18
    "LSHIFT", "RSHIFT",  # 19-20
    "NUMLIT", "IDENT", "PRINT", "GLUE", "IF", "WHILE", "FOR",  # 21-27
    "TYPE", "STRLIT", "LOCAL", "FUNCTION", "FUNCCALL",  # 28-32
    "PRINTF", "MOD", "RETURN", "BLOCK",  # 29-36
]


def mk_ast_node(op: ASTNodeType, left: Optional[ASTNode] = None,
                mid: Optional[ASTNode] = None,
                right: Optional[ASTNode] = None) -> ASTNode:
    node = ASTNode(op)
    node.left = left
    node.mid = mid
    node.right = right
    return node


def mk_ast_leaf(op: ASTNodeType, type_: Optional['Type'] = None,
                rvalue: bool = False, sym: Optional['Sym'] = None,
                intval: int = 0) -> ASTNode:
    node = mk_ast_node(op)
    node.type = type_
    node.rvalue = rvalue
    node.sym = sym
    node.numlit.intval = intval
    return node


def free_ast(node: Optional[ASTNode]) -> None:
    if node is None:
        return
    free_ast(node.left)
    free_ast(node.mid)
    free_ast(node.right)
    # Python has garbage collection, so no need to explicitly free memory


def dump_ast(out, node: Optional[ASTNode], level: int = 0) -> None:
    if node is None:
        fatal("NULL AST node")
        return

    # Print indentation
    if out is None:
        out = sys.stdout
    for _ in range(level):
        out.write(" ")

    # Print type if available
    if node.type is not None:
        type_name = TypeProcessor.get_typename(node.type)
        out.write(f"{type_name} ")

    # Print operation name
    op_name = f"Unknown-op({node.op.value})"
    if node.op.value < len(_astname):
        op_name = _astname[node.op.value]
    out.write(f"{op_name} ")

    # Print node-specific information
    if node.op == ASTNodeType.A_IDENT:
        if node.rvalue:
            out.write(f"rval {node.strlit}")
        else:
            out.write(f"{node.strlit}")
    elif node.op == ASTNodeType.A_STRLIT:
        value = quote_string(node.strlit)
        out.write(f"({value})")
    elif node.op == ASTNodeType.A_NUMLIT:
        if node.type and node.type.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            out.write(f"({node.numlit.dblval})")
        else:
            out.write(f"({node.numlit.intval})")
    elif node.op == ASTNodeType.A_ASSIGN:
        out.write(f"{node.left.sym.name} = ")
    elif node.op == ASTNodeType.A_LOCAL:
        out.write(f"{node.sym.name}")
    elif node.op in (ASTNodeType.A_PRINT, ASTNodeType.A_PRINTF, ASTNodeType.A_FUNCCALL):
        if node.left:
            value = quote_string(node.left.strlit)
            out.write(f"\"{value}\"")
        if node.right:
            dump_ast(out, node.right, level + 2)
        return

    out.write("\n")

    # Adjust level for local nodes
    new_level = level + 2 if node.op != ASTNodeType.A_LOCAL else level - 2

    # Recursively dump children
    if node.left:
        dump_ast(out, node.left, new_level)
    if node.mid:
        dump_ast(out, node.mid, new_level)
    if node.right:
        dump_ast(out, node.right, new_level)
