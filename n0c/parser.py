from typing import List

from defs import (
    ASTNode, NodeType, DataType, TypeKind, TokType, Token, Litval, SymType, Sym,
    fatal, ty_void, ty_bool, ty_int8, ty_int16, ty_int32, ty_int64,
    ty_uint8, ty_uint16, ty_uint32, ty_uint64, ty_float32, ty_float64
)
from expr import ExprProcessor
from funcs import FuncProcessor
from lexer import Lexer
from stmts import gen_stat_declare
from syms import root
from typs import TypeProcessor


class Parser:
    table = root
    leaves = []

    def __init__(self, lexer: Lexer = None):
        self.lexer = lexer
        self.curr = None

    @staticmethod
    def gen_number_node(token: Token) -> (DataType, Litval):
        node = ASTNode(NodeType.A_NUMLIT)
        node.numlit = Litval()
        if isinstance(token.num_val, float):
            node.type = ty_float64
            node.numlit.dblval = token.num_val
        else:
            node.type = ty_int64
            node.numlit.intval = token.num_val
        return node

    def parse_file(self, filename) -> ASTNode | None:
        self.lexer = Lexer(filename)
        return self.parse_program()

    def parse_program(self) -> ASTNode | None:
        if self.lexer is None:
            fatal("Lexer is not initialized")
        self.lexer.reset()
        self.next_token()
        return self.function_declarations()

    def add_node(self, node: ASTNode | None):
        if node is None:
            return
        self.leaves.append(node)
        # dump_ast(sys.stdout, node)

    def next_token(self) -> Token:
        self.curr = self.lexer.scan_next()
        return self.curr

    def match_type(self, token_type: TokType, throw: bool = True) -> bool:
        if self.curr.tok_type == token_type:
            self.next_token()
            return True
        if throw:
            fatal(f"Unexpected token {self.curr.tok_type}, expected {token_type}")
        return False

    def semi(self, throw: bool = True) -> bool:
        return self.match_type(TokType.T_SEMI, throw)

    def lbrace(self) -> bool:
        return self.match_type(TokType.T_LBRACE)

    def rbrace(self, throw: bool = True) -> bool:
        return self.match_type(TokType.T_RBRACE, throw)

    def lparen(self) -> bool:
        return self.match_type(TokType.T_LPAREN)

    def rparen(self, throw: bool = True) -> bool:
        return self.match_type(TokType.T_RPAREN, throw)

    def comma(self, throw: bool = True) -> bool:
        return self.match_type(TokType.T_COMMA, throw)

    def is_eof(self) -> bool:
        return self.match_type(TokType.T_EOF, False)

    def function_declarations(self) -> ASTNode | None:
        """
        function_declarations= function_declaration*
        """
        node = None
        while not self.is_eof():
            node = self.function_declaration()
            self.add_node(node)
        return node

    def function_declaration(self) -> ASTNode:
        """
        function_declaration= function_prototype statement_block
                            | function_prototype SEMI
        """
        node, params = self.function_prototype()
        if self.semi(False):
            self.add_function(node, params)
            return node
        node.left = self.statement_block()
        self.declare_function(node, params)
        self.gen_func_statement_block(node)
        self.add_node(node)
        return node

    def function_prototype(self) -> (ASTNode, List[Sym]):
        """
        function_prototype= typed_declaration LPAREN typed_declaration_list RPAREN
                          | typed_declaration LPAREN VOID RPAREN
        """
        node, params = self.typed_declaration(), []
        self.lparen()
        if not self.match_type(TokType.T_VOID, False):
            node.left, params = self.typed_declaration_list()
        self.rparen()
        self.add_node(node)
        return node, params

    def typed_declaration_list(self) -> (ASTNode, List[Sym]):
        """
        typed_declaration_list= typed_declaration (COMMA typed_declaration_list)*
        """
        root = self.typed_declaration()
        node, sym_list = root, [root.sym, ]
        while self.comma(False):
            next_node = self.typed_declaration()
            sym_list.append(next_node.sym)
            node.mid = next_node
            node = next_node
        return root, sym_list

    def typed_declaration(self) -> ASTNode:
        """
        typed_declaration= type IDENT
        """
        type_obj = self.get_type()
        node = self.get_id(type_obj)
        self.add_node(node)
        return node

    def declaration_stmts(self) -> ASTNode:
        """
        declaration_stmts= (typed_declaration ASSIGN expression SEMI)+
        """
        node, last = None, None
        while self.is_type_token(self.curr.tok_type):
            decl = self.typed_declaration()
            if self.match_type(TokType.T_ASSIGN, False):
                expr = self.expression()
                decl = self.declaration_statement(decl, expr)
            self.semi()
            if not node:
                node = decl
            else:
                last.right = decl
            last = decl
        self.add_node(node)
        return node

    def procedural_stmts(self) -> ASTNode:
        """
        procedural_stmts= procedural_stmt*
        """
        node, last = None, None
        while 1:
            last = self.procedural_stmt()
            if not last:
                break
            if not node:
                node = last
            else:
                node = ASTNode(NodeType.A_GLUE, left=node, right=last)

        # while self.curr.token not in (TokenType.T_RBRACE, TokenType.T_EOF):
        #     stmt = self.procedural_stmt()
        #     if not node:
        #         node = stmt
        #     else:
        #         last.right = stmt
        #     last = stmt

        self.add_node(node)
        return node

    def procedural_stmt(self) -> ASTNode | None:
        """
        解析单个过程语句，可能返回None
        procedural_stmt= ( print_stmt
                         | assign_stmt
                         | if_stmt
                         | while_stmt
                         | for_stmt
                         | function_call
                         )
        """
        if self.curr.tok_type == TokType.T_RBRACE:
            return None
        if self.curr.tok_type == TokType.T_PRINTF:
            return self.print_statement()
        elif self.curr.tok_type == TokType.T_IF:
            return self.if_stmt()
        elif self.curr.tok_type == TokType.T_WHILE:
            return self.while_stmt()
        elif self.curr.tok_type == TokType.T_FOR:
            return self.for_stmt()
        elif self.curr.tok_type == TokType.T_IDENT:
            if self.match_type(TokType.T_LPAREN, False):
                return self.function_call()
            else:
                return self.assign_stmt()
        return fatal(f"Unexpected token {self.curr.tok_type} in procedural statement")

    def get_type(self) -> DataType:
        """
        type= built-in type | user-defined type
        """
        type_map = {
            TokType.T_VOID: ty_void,
            TokType.T_BOOL: ty_bool,
            TokType.T_INT8: ty_int8,
            TokType.T_INT16: ty_int16,
            TokType.T_INT32: ty_int32,
            TokType.T_INT64: ty_int64,
            TokType.T_UINT8: ty_uint8,
            TokType.T_UINT16: ty_uint16,
            TokType.T_UINT32: ty_uint32,
            TokType.T_UINT64: ty_uint64,
            TokType.T_FLT32: ty_float32,
            TokType.T_FLT64: ty_float64
        }
        if self.curr.tok_type not in type_map:
            fatal(f"Unknown type {self.curr.tok_type}")
        type_obj = type_map[self.curr.tok_type]
        self.next_token()
        return type_obj

    def get_id(self, type_obj: DataType) -> ASTNode:
        id_str = self.curr.tok_str
        self.match_type(TokType.T_IDENT)
        identifier = ASTNode(NodeType.A_IDENT)
        identifier.strlit = id_str
        identifier.type = type_obj
        identifier.sym = Sym(
            name=id_str,
            sym_type=SymType.S_LOCAL,
            val_type=type_obj
        )
        return identifier

    def statement_block(self) -> ASTNode | None:
        """
        statement_block= LBRACE procedural_stmt* RBRACE
                       | LBRACE declaration_stmt* procedural_stmt* RBRACE
        """
        self.lbrace()
        if self.rbrace(False):
            return None
        node = self.declaration_stmts()
        proc = self.procedural_stmts()
        if node is None:
            node = proc
        else:
            node = ASTNode(NodeType.A_GLUE, left=node, right=proc)
        self.rbrace()
        self.add_node(node)
        return node

    def print_statement(self) -> ASTNode:
        self.match_type(TokType.T_PRINTF)
        self.lparen()
        left = self.factor()
        assert left.op == NodeType.A_STRLIT
        self.comma()
        right = self.expression()
        self.rparen()
        self.semi()
        node = ASTNode(NodeType.A_PRINTF)
        if right.type.kind == TypeKind.K_FLT32:
            right = TypeProcessor.widen_expression(right)
        node.left, node.right = left, right
        self.add_node(node)
        return node

    def assign_stmt(self) -> ASTNode:
        """
        assign_stmt= variable ASSIGN expression SEMI
        """
        left = self.expression()
        self.match_type(TokType.T_ASSIGN)
        right = self.expression()
        self.semi()
        node = ASTNode(NodeType.A_ASSIGN)
        node.left = left
        node.right = right
        self.add_node(node)
        return node

    def if_stmt(self) -> ASTNode:
        """
        if_stmt= IF LPAREN relational_expression RPAREN statement_block
                 (ELSE statement_block)?
        """
        self.match_type(TokType.T_IF)
        self.lparen()
        cond = self.expression()
        self.rparen()
        then_stmt = self.statement_block()
        else_stmt = None
        if self.match_type(TokType.T_ELSE, False):
            else_stmt = self.statement_block()
        node = ASTNode(NodeType.A_IF)
        node.left = cond
        node.mid = then_stmt
        node.right = else_stmt
        self.add_node(node)
        return node

    def while_stmt(self) -> ASTNode:
        """
        while_stmt= WHILE LPAREN relational_expression RPAREN statement_block
        """
        self.match_type(TokType.T_WHILE)
        self.lparen()
        cond = self.expression()
        self.rparen()
        body = self.statement_block()
        node = ASTNode(NodeType.A_WHILE)
        node.left = cond
        node.mid = body
        self.add_node(node)
        return node

    def for_stmt(self) -> ASTNode:
        """
        for_stmt= FOR LPAREN assign_stmt relational_expression SEMI
                  short_assign_stmt RPAREN statement_block
        """
        self.match_type(TokType.T_FOR)
        self.lparen()
        init = None if self.semi(False) else self.expression()
        cond = None if self.semi(False) else self.expression()
        incr = None if self.rparen(False) else self.expression()
        body = self.statement_block()
        node = ASTNode(NodeType.A_FOR)
        node.left, node.right = init, incr
        node.mid = cond
        node.mid.right = body
        self.add_node(node)
        return node

    def function_call(self) -> ASTNode:
        """
        function_call= IDENT LPAREN expression_list? RPAREN SEMI
        """
        func_name = self.curr.tok_str
        self.match_type(TokType.T_IDENT)
        self.lparen()
        args = None if self.rparen(False) else self.expression_list()
        self.rparen()
        self.semi()
        node = ASTNode(NodeType.A_FUNCCALL)
        node.strlit = func_name
        node.right = args
        self.add_node(node)
        return node

    def expression_list(self) -> ASTNode:
        """
        expression_list= expression (COMMA expression_list)*
        """
        expr = self.expression()
        node = ASTNode(NodeType.A_GLUE, left=expr)
        while self.comma(False):
            expr = self.expression()
            node = ASTNode(NodeType.A_GLUE, left=expr, right=node)
        return node

    def expression(self) -> ASTNode:
        """
        expression= bitwise_expression
        """
        node = self.bitwise_expression()
        self.add_node(node)
        return node

    def bitwise_expression(self) -> ASTNode:
        """
        bitwise_expression= ( INVERT relational_expression
                            |        relational_expression
                            )
                            ( AND relational_expression
                            | OR  relational_expression
                            | XOR relational_expression
                            )*
        """
        invert = self.match_type(TokType.T_INVERT, False)
        left = self.relational_expression()
        if invert:
            left = ExprProcessor.unary_op(NodeType.A_INVERT, left)
        while self.curr.tok_type in (TokType.T_AND, TokType.T_OR, TokType.T_XOR):
            op = self.map_token_to_ast_op(self.curr.tok_type)
            self.next_token()
            right = self.relational_expression()
            left = ExprProcessor.binary_op(left, op, right)
        return left

    def relational_expression(self) -> ASTNode:
        """
        relational_expression= ( NOT shift_expression
                               |     shift_expression
                               )
                               ( GE shift_expression
                               | GT shift_expression
                               | LE shift_expression
                               | LT shift_expression
                               | EQ shift_expression
                               | NE shift_expression
                               )?
        """
        log_not = self.match_type(TokType.T_LOGNOT, False)
        left = self.shift_expression()
        if log_not:
            left = ExprProcessor.unary_op(NodeType.A_NOT, left)
        while TokType.T_EQ <= self.curr.tok_type <= TokType.T_GE:
            op = self.map_token_to_ast_op(self.curr.tok_type)
            self.next_token()
            right = self.shift_expression()
            left = ExprProcessor.binary_op(left, op, right)
        return left

    def shift_expression(self) -> ASTNode:
        """
        shift_expression= additive_expression
                        ( LSHIFT additive_expression
                        | RSHIFT additive_expression
                        )*
        """
        left = self.additive_expression()
        while self.curr.tok_type in (TokType.T_LSHIFT, TokType.T_RSHIFT):
            op = self.map_token_to_ast_op(self.curr.tok_type)
            self.next_token()
            right = self.additive_expression()
            left = ExprProcessor.binary_op(left, op, right)
        return left

    def additive_expression(self) -> ASTNode:
        """
        additive_expression= ( PLUS? multiplicative_expression
                             | MINUS multiplicative_expression
                             )
                             ( PLUS  multiplicative_expression
                             | MINUS multiplicative_expression
                             )*
        """
        negate = self.match_type(TokType.T_MINUS, False)
        left = self.multiplicative_expression()
        if negate:
            left = ExprProcessor.unary_op(NodeType.A_NEGATE, left)
        while self.curr.tok_type in (TokType.T_PLUS, TokType.T_MINUS):
            op = self.map_token_to_ast_op(self.curr.tok_type)
            self.next_token()
            right = self.multiplicative_expression()
            left = ExprProcessor.binary_op(left, op, right)
        return left

    def multiplicative_expression(self) -> ASTNode:
        """
        multiplicative_expression= l:factor
                                 ( STAR  factor
                                 | SLASH factor
                                 )*

        multiplicative_expression= ( STAR? unary_expression
                                    | SLASH unary_expression
                                    | PERCENT unary_expression
                                    )
                                    ( STAR  unary_expression
                                    | SLASH unary_expression
                                    | PERCENT unary_expression
                                    )*
        """
        left = self.factor()
        while self.curr.tok_type in (TokType.T_STAR, TokType.T_SLASH, TokType.T_MOD):
            op = self.map_token_to_ast_op(self.curr.tok_type)
            self.next_token()
            right = self.factor()
            left = ExprProcessor.binary_op(left, op, right)
        return left

    def factor(self) -> ASTNode | None:
        """
        factor= NUMLIT
              | TRUE
              | FALSE
              | variable
        """
        token = self.curr.tok_type
        if token == TokType.T_LPAREN:
            self.lparen()
            expr = self.expression()
            self.rparen()
            return expr
        elif token == TokType.T_IDENT:
            if self.match_type(TokType.T_LPAREN, False):
                return self.function_call()
            else:
                return self.variable()
        elif token == TokType.T_NUMLIT:
            node = self.gen_number_node(self.curr)
            self.match_type(token)
            return node
        elif token == TokType.T_STRLIT:
            node = ASTNode(NodeType.A_STRLIT)
            node.strlit = self.curr.tok_str
            self.match_type(token)
            return node
        elif token == TokType.T_TRUE or token == TokType.T_FALSE:
            node = ASTNode(NodeType.A_NUMLIT)
            node.numlit.intval = 1 if token == TokType.T_TRUE else 0
            node.type = ty_bool
            self.match_type(token)
            return node
        elif token in (TokType.T_MINUS, TokType.T_PLUS, TokType.T_LOGNOT, TokType.T_INVERT):
            op = self.map_token_to_ast_op(token)
            self.match_type(token)
            child = self.factor()
            node = ASTNode(op)
            node.left = child
            return node
        return fatal(f"Unexpected token {token} in factor")

    def variable(self) -> ASTNode:
        """
        variable= IDENT
        """
        name = self.curr.tok_str
        self.match_type(TokType.T_IDENT)
        node = ASTNode(NodeType.A_IDENT)
        node.strlit = name
        node.sym = self.table.find_symbol(name)
        if not node.sym:
            fatal(f"Unknown variable {name}")
        node.type = node.sym.type
        self.add_node(node)
        return node

    def is_type_token(self, token: TokType) -> bool:
        return token in (
            TokType.T_VOID, TokType.T_BOOL, TokType.T_INT8, TokType.T_INT16,
            TokType.T_INT32, TokType.T_INT64, TokType.T_UINT8, TokType.T_UINT16,
            TokType.T_UINT32, TokType.T_UINT64, TokType.T_FLT32, TokType.T_FLT64
        )

    def map_token_to_ast_op(self, token: TokType) -> NodeType:
        op_map = {
            TokType.T_PLUS: NodeType.A_ADD,
            TokType.T_MINUS: NodeType.A_SUBTRACT,
            TokType.T_STAR: NodeType.A_MULTIPLY,
            TokType.T_SLASH: NodeType.A_DIVIDE,
            TokType.T_MOD: NodeType.A_MOD,
            TokType.T_EQ: NodeType.A_EQ,
            TokType.T_NE: NodeType.A_NE,
            TokType.T_LT: NodeType.A_LT,
            TokType.T_GT: NodeType.A_GT,
            TokType.T_LE: NodeType.A_LE,
            TokType.T_GE: NodeType.A_GE,
            TokType.T_LSHIFT: NodeType.A_LSHIFT,
            TokType.T_RSHIFT: NodeType.A_RSHIFT,
            TokType.T_AND: NodeType.A_AND,
            TokType.T_OR: NodeType.A_OR,
            TokType.T_XOR: NodeType.A_XOR,
            TokType.T_INVERT: NodeType.A_INVERT,
            TokType.T_LOGNOT: NodeType.A_NOT
        }
        return op_map.get(token, NodeType.A_ADD)

    # Placeholder methods that need implementation from other modules
    def add_function(self, func: ASTNode, params: List[Sym]) -> None:
        FuncProcessor.add_function(func.strlit, func.type, params)
        return

    def declare_function(self, func: ASTNode, params: List[Sym]) -> None:
        FuncProcessor.declare_function(func.strlit, func.type, params, func.left)
        self.table = self.table.new_scope(func)
        return

    def gen_func_statement_block(self, func: ASTNode) -> None:
        FuncProcessor.gen_func_statement_block(func.sym, func.left)
        self.table = self.table.end_scope()
        return

    def declaration_statement(self, ident: ASTNode, expr: ASTNode) -> ASTNode:
        return gen_stat_declare(ident, expr)
