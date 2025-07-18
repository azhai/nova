from typing import Optional
from defs import ASTNode, ASTNodeType, DataType, TokenType, TypeKind, Sym, SymType, cast_node, fatal, ty_flt64
from syms import add_symbol
from typs import TypeProcessor, parse_litval


class StmtProcessor:
    @staticmethod
    def print_statement(expr: ASTNode) -> ASTNode:
        if not expr:
            return None

        # 拓宽表达式类型
        expr = TypeProcessor.widen_expression(expr)

        # 对于float32类型，拓宽为float64
        if expr.type.kind == TypeKind.TY_FLT32:
            target_type = TypeProcessor.get_type(TypeKind.TY_FLT64)
            expr = cast_node(expr, target_type)

        # 创建打印语句AST节点
        node = ASTNode(
            op=ASTNodeType.A_PRINT,
            left=expr,
            right=None,
            type=TypeProcessor.get_type(TypeKind.TY_VOID)
        )
        return node

    @staticmethod
    def assignment_statement(val: ASTNode, expr: ASTNode) -> ASTNode:
        if not val or not expr or val.op != ASTNodeType.A_IDENT:
            fatal("Invalid assignment target")

        # 拓宽表达式类型
        expr = TypeProcessor.widen_expression(expr)
        # 拓宽左值类型
        val = TypeProcessor.widen_expression(val)

        # 确保类型兼容
        if val.type != expr.type:
            new_type = TypeProcessor.widen_type(val.type, expr.type)
            if new_type is None:
                fatal(f"Type mismatch in assignment: {val.type} and {expr.type}")
            # 转换表达式类型以匹配左值类型
            if expr.type != new_type:
                expr = cast_node(expr, new_type)
            # 更新左值类型
            val.type = new_type

        # 创建赋值语句AST节点
        node = ASTNode(
            op=ASTNodeType.A_ASSIGN,
            left=val,
            right=expr,
            type=val.type
        )
        return node

    @staticmethod
    def declaration_statement(val_type: DataType, name: str, expr: Optional[ASTNode]) -> ASTNode:
        # 检查符号是否已存在
        from syms import find_symbol
        existing = find_symbol(name)
        if existing:
            fatal(f"Symbol {name} already declared")

        # 创建新符号
        sym = Sym(
            name=name,
            sym_type=SymType.SYM_VAR,
            val_type=val_type
        )
        # 添加到符号表
        add_symbol(sym)

        # 如果有初始化表达式，处理类型拓宽
        if expr:
            expr = TypeProcessor.widen_expression(expr)
            # 确保类型兼容
            if val_type != expr.type:
                new_type = TypeProcessor.widen_type(val_type, expr.type)
                if new_type is None:
                    fatal(f"Type mismatch in declaration of {name}: {val_type} and {expr.type}")
                # 转换表达式类型
                expr = cast_node(expr, new_type)
                # 更新变量类型
                sym.type = val_type = new_type
            # 保存初始值
            if expr.op == ASTNodeType.A_NUMLIT:
                sym.init_val = parse_litval(TokenType.T_NUMLIT, expr.strlit)
            elif expr.op == ASTNodeType.A_STRLIT:
                sym.init_val = parse_litval(TokenType.T_STRLIT, expr.strlit)

        # 创建声明语句AST节点
        node = ASTNode(
            op=ASTNodeType.A_LOCAL,
            left=expr,
            right=None,
            type=val_type,
            sym=sym
        )
        return node

def gen_stat_assign(val: ASTNode, expr: ASTNode) -> ASTNode:
    """ 创建赋值语句AST节点 """
    expr = cast_node(expr, val.type)
    node = ASTNode(
        op=ASTNodeType.A_ASSIGN,
        left=expr,
        right=None
    )
    node.type = val.sym.type
    node.rvalue = False
    return node

def gen_stat_printf(first: ASTNode, expr: ASTNode) -> ASTNode:
    """ 创建打印语句AST节点 """
    if expr.type.kind == TypeKind.TY_FLT32:
        expr = cast_node(expr, ty_flt64)
    node = ASTNode(
        op=ASTNodeType.A_PRINTF,
        left=first,
        right=expr
    )
    return node

def gen_stat_declare(ident: ASTNode, expr: ASTNode) -> ASTNode:
    """ 创建声明语句AST节点 """
    expr = cast_node(expr, ident.type)
    # 添加到符号表
    sym = add_symbol(ident.strlit, SymType.SYM_VAR, ident.type)
    sym.has_addr = True
    # 改造ident
    ident.sym = sym
    ident.left = expr
    ident.op = ASTNodeType.A_LOCAL
    return ident
