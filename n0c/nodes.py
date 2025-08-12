import sys
from typing import Optional

from defs import ASTNode, NodeType, ValType, fatal, quote_string


def free_ast(_: Optional[ASTNode]):
    # Python has garbage collection, so no need to explicitly free memory
    return


def dump_ast(node: Optional[ASTNode], level: int = 0, out = ""):
    if node is None:
        fatal("NULL AST node")
        return

    # Print indentation
    if out is None:
        out = sys.stdout
    for _ in range(level):
        out.write(" ")

    # Print type if available
    if node.val_type is not None:
        type_name = node.val_type.value
        out.write(f"{type_name} ")

    # Print operation name
    op_name = node.op.name
    out.write(f"{op_name} ")

    # Print node-specific information
    if node.op == NodeType.A_IDENT:
        out.write(f"{node.string}")
    elif node.op == NodeType.A_LITERAL:
        if node.val_type and node.val_type == ValType.STR:
            value = quote_string(node.string)
            out.write(f"({value})")
        else:
            out.write(f"({node.number})")
    elif node.op == NodeType.A_ASSIGN:
        out.write(f"{node.left.sym.name} = ")
    elif node.op == NodeType.A_LOCAL:
        out.write(f"{node.sym.name}")
    elif node.op == NodeType.A_FUNC:
        out.write(f"{node.sym.name}")
    elif node.op in (NodeType.A_PRINTF, NodeType.A_PRINTF, NodeType.A_CALL):
        out.write(f"{node.string}")
        if node.right:
            dump_ast(node.right, level + 2, out=out)
        return

    out.write("\n")

    # Adjust level for local nodes
    new_level = level + 2 if node.op != NodeType.A_LOCAL else level - 2

    # Recursively dump children
    if node.left:
        dump_ast(node.left, new_level, out=out)
    if node.right:
        dump_ast(node.right, new_level, out=out)
