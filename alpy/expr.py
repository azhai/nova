from defs import ASTNode, ASTNodeType, cast_node, fatal
from typs import TypeProcessor


class ExprProcessor:
    @staticmethod
    def binop(left: ASTNode, op: ASTNodeType, right: ASTNode = None) -> ASTNode:
        if not left or not right:
            return None

        # 确保左右操作数类型兼容并拓宽
        left = TypeProcessor.widen_expression(left)
        right = TypeProcessor.widen_expression(right)

        if left.type != right.type:
            # 尝试将一种类型拓宽到另一种类型
            new_type = TypeProcessor.widen_type(left.type, right.type)
            if new_type is None:
                fatal(f"Type mismatch in binary operation: {left.type} and {right.type}")
            if left.type != new_type:
                left = cast_node(left, new_type)
            if right.type != new_type:
                right = cast_node(right, new_type)

        # 创建新的AST节点
        node = ASTNode(
            op=op,
            left=left,
            right=right,
            type=left.type
        )
        node.rvalue = True
        return node

    @staticmethod
    def unarop(op: ASTNodeType, left: ASTNode) -> ASTNode:
        if not left:
            return None

        # 拓宽表达式类型
        left = TypeProcessor.widen_expression(left)

        # 创建新的AST节点
        node = ASTNode(
            op=op,
            left=left,
            right=None,
            type=left.type
        )
        node.rvalue = True
        return node
