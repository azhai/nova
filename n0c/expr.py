from defs import ASTNode, NodeType
from typs import add_type


class ExprProcessor:

    @staticmethod
    def unary_op(op: NodeType, right: ASTNode) -> ASTNode:
        node = ASTNode(
            op=op,
            right=right,
            type=right.type
        )
        node.rvalue = True
        return node

    @staticmethod
    def binary_op(left: ASTNode, op: NodeType, right: ASTNode = None) -> ASTNode:
        node = ASTNode(
            op=op,
            left=left,
            right=right
        )
        node.rvalue = True
        return add_type(node)
