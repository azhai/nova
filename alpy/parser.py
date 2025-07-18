from defs import (
    ASTNode, ASTNodeType, DataType, Litval, Sym, TokenType, Token,
    fatal, ty_void, ty_bool, ty_int8, ty_int16, ty_int32, ty_int64,
    ty_uint8, ty_uint16, ty_uint32, ty_uint64, ty_flt32, ty_flt64
)
from lexer import Lexer
from expr import ExprProcessor
from funcs import FuncProcessor
from stmts import gen_stat_declare
from syms import SymProcessor


class Parser:
    finder = SymProcessor()

    def __init__(self, lexer: Lexer = None):
        self.lexer = lexer
        self.curr, self.peek = None, None

    @staticmethod
    def gen_number_node(token: Token) -> (DataType, Litval):
        node = ASTNode(ASTNodeType.A_NUMLIT)
        node.numlit = Litval()
        if isinstance(token.num_val, float):
            node.type = ty_flt64
            node.numlit.dblval = token.num_val
        else:
            node.type = ty_int64
            node.numlit.intval = token.num_val
        return node

    def parse_file(self, filename) -> list[ASTNode]:
        self.lexer = Lexer(filename)
        return self.parse_program()

    def parse_program(self) -> list[ASTNode]:
        if self.lexer is None:
            fatal("Lexer is not initialized")
        self.lexer.reset()
        self.next_token()
        return self.function_declarations()

    def next_token(self) -> Token:
        if self.peek is not None:
            self.curr, self.peek = self.peek, None
        else:
            self.curr = self.lexer.scan_next()
        return self.curr

    def peek_is(self, token_type: TokenType) -> bool:
        self.peek = self.lexer.scan_next()
        if self.peek.token == TokenType.T_EOF:
            self.peek = self.lexer.scan_next()
        return self.peek == token_type

    def match(self, token_type: TokenType, get_next: bool = True) -> bool:
        ok = (self.curr.token == token_type)
        if not ok:
            fatal(f"Unexpected token {self.curr.token}, expected {token_type}")
        if get_next:
            self.next_token()
        return ok

    def semi(self) -> None:
        self.match(TokenType.T_SEMI)

    def lbrace(self) -> None:
        self.match(TokenType.T_LBRACE)

    def rbrace(self) -> None:
        self.match(TokenType.T_RBRACE)

    def lparen(self) -> None:
        self.match(TokenType.T_LPAREN)

    def rparen(self) -> None:
        self.match(TokenType.T_RPAREN)

    def comma(self) -> None:
        self.match(TokenType.T_COMMA)

    def function_declarations(self) -> list[ASTNode]:
        """
        function_declarations= function_declaration*
        """
        nodes = []
        while self.curr.token != TokenType.T_EOF:
            ast = self.function_declaration()
            nodes.append(ast)
        return nodes

    def function_declaration(self) -> ASTNode:
        """
        function_declaration= function_prototype statement_block
                            | function_prototype SEMI
        """
        func = self.function_prototype()
        if self.curr.token == TokenType.T_SEMI:
            self.add_function(func, func.left)
            self.semi()
            return func
        self.declare_function(func)
        s = self.statement_block()
        self.gen_func_statement_block(s)
        return s

    def function_prototype(self) -> ASTNode:
        """
        function_prototype= typed_declaration LPAREN typed_declaration_list RPAREN
                          | typed_declaration LPAREN VOID RPAREN
        """
        func = self.typed_declaration()
        self.lparen()
        if self.match(TokenType.T_VOID, False):
            self.next_token()
        else:
            func.left = self.typed_declaration_list()
        self.rparen()
        return func

    def typed_declaration_list(self) -> ASTNode:
        """
        typed_declaration_list= typed_declaration (COMMA typed_declaration_list)*
        """
        root = self.typed_declaration()
        node = root
        self.next_token()
        while self.curr.token == TokenType.T_COMMA:
            self.comma()
            next_node = self.typed_declaration()
            node.mid = next_node
            node = next_node
        return root

    def typed_declaration(self) -> ASTNode:
        """
        typed_declaration= type IDENT
        """
        type_obj = self.get_type()
        return self.get_id(type_obj)

    def get_type(self) -> DataType:
        """
        type= built-in type | user-defined type
        """
        type_map = {
            TokenType.T_VOID: ty_void,
            TokenType.T_BOOL: ty_bool,
            TokenType.T_INT8: ty_int8,
            TokenType.T_INT16: ty_int16,
            TokenType.T_INT32: ty_int32,
            TokenType.T_INT64: ty_int64,
            TokenType.T_UINT8: ty_uint8,
            TokenType.T_UINT16: ty_uint16,
            TokenType.T_UINT32: ty_uint32,
            TokenType.T_UINT64: ty_uint64,
            TokenType.T_FLT32: ty_flt32,
            TokenType.T_FLT64: ty_flt64
        }
        if self.curr.token not in type_map:
            fatal(f"Unknown type {self.curr.token}")
        type_obj = type_map[self.curr.token]
        self.match(self.curr.token)
        return type_obj

    def get_id(self, type_obj: DataType) -> ASTNode:
        id_str = self.curr.tok_str
        self.match(TokenType.T_IDENT)
        identifier = ASTNode(ASTNodeType.A_IDENT)
        identifier.strlit = id_str
        identifier.type = type_obj
        return identifier

    def statement_block(self) -> ASTNode | None:
        """
        statement_block= LBRACE procedural_stmt* RBRACE
                       | LBRACE declaration_stmt* procedural_stmt* RBRACE
        """
        self.lbrace()
        if self.curr.token == TokenType.T_RBRACE:
            self.rbrace()
            return None
        d = self.declaration_stmts()
        s = self.procedural_stmts()
        if d and s:
            d.right = s
            return d
        self.rbrace()
        return d or s

    def print_statement(self) -> ASTNode:
        self.match(TokenType.T_PRINTF)
        self.lparen()
        expr = self.expression()
        self.rparen()
        self.semi()
        node = ASTNode(ASTNodeType.A_PRINTF)
        node.left = expr
        return node

    def printf_statement(self) -> ASTNode:
        self.match(TokenType.T_PRINTF)
        self.lparen()
        args = self.expression_list()
        self.rparen()
        self.semi()
        node = ASTNode(ASTNodeType.A_PRINTF)
        node.right = args
        return node

    def assign_stmt(self) -> ASTNode:
        """
        assign_stmt= variable ASSIGN expression SEMI
        """
        left = self.expression()
        self.match(TokenType.T_ASSIGN)
        right = self.expression()
        node = ASTNode(ASTNodeType.A_ASSIGN)
        node.left = left
        node.right = right
        return node

    def declaration_stmts(self) -> ASTNode:
        """
        declaration_stmts= (typed_declaration ASSIGN expression SEMI)+
        """
        first, last = None, None
        while self.is_type_token(self.curr.token):
            decl = self.typed_declaration()
            if self.curr.token == TokenType.T_ASSIGN:
                self.match(TokenType.T_ASSIGN)
                expr = self.expression()
                decl = self.declaration_statement(decl, expr)
            self.semi()
            if not first:
                first = decl
            else:
                last.right = decl
            last = decl
        return first

    def procedural_stmts(self) -> ASTNode:
        """
        procedural_stmt= ( print_stmt
                         | assign_stmt
                         | if_stmt
                         | while_stmt
                         | for_stmt
                         | function_call
                         )*
        """
        first, last = None, None
        while self.curr.token not in (TokenType.T_RBRACE, TokenType.T_EOF):
            stmt = self.procedural_stmt()
            if not first:
                first = stmt
            else:
                last.right = stmt
            last = stmt
        return first

    def procedural_stmt(self) -> ASTNode | None:
        """
        解析单个过程语句，可能返回None
        """
        if self.curr.token == TokenType.T_RBRACE:
            return None
        if self.curr.token == TokenType.T_PRINTF:
            return self.printf_statement()
        elif self.curr.token == TokenType.T_IF:
            return self.if_stmt()
        elif self.curr.token == TokenType.T_WHILE:
            return self.while_stmt()
        elif self.curr.token == TokenType.T_FOR:
            return self.for_stmt()
        elif self.curr.token == TokenType.T_IDENT:
            if self.peek_is(TokenType.T_LPAREN):
                return self.function_call()
            else:
                return self.assign_stmt()
        return fatal(f"Unexpected token {self.curr.token} in procedural statement")

    def if_stmt(self) -> ASTNode:
        """
        if_stmt= IF LPAREN relational_expression RPAREN statement_block
                 (ELSE statement_block)?
        """
        self.match(TokenType.T_IF)
        self.lparen()
        cond = self.expression()
        self.rparen()
        then_stmt = self.statement_block()
        else_stmt = None
        if self.curr.token == TokenType.T_ELSE:
            self.match(TokenType.T_ELSE)
            else_stmt = self.statement_block()
        node = ASTNode(ASTNodeType.A_IF)
        node.left = cond
        node.mid = then_stmt
        node.right = else_stmt
        return node

    def while_stmt(self) -> ASTNode:
        """
        while_stmt= WHILE LPAREN relational_expression RPAREN statement_block
        """
        self.match(TokenType.T_WHILE)
        self.lparen()
        cond = self.expression()
        self.rparen()
        body = self.statement_block()
        node = ASTNode(ASTNodeType.A_WHILE)
        node.left = cond
        node.mid = body
        return node

    def for_stmt(self) -> ASTNode:
        """
        for_stmt= FOR LPAREN assign_stmt relational_expression SEMI
                  short_assign_stmt RPAREN statement_block
        """
        self.match(TokenType.T_FOR)
        self.lparen()
        init = self.expression() if self.curr.token != TokenType.T_SEMI else None
        if self.curr.token == TokenType.T_SEMI:
            self.semi()
        cond = self.expression() if self.curr.token != TokenType.T_SEMI else None
        if self.curr.token == TokenType.T_SEMI:
            self.semi()
        incr = self.expression() if self.curr.token != TokenType.T_RPAREN else None
        self.rparen()
        body = self.statement_block()
        node = ASTNode(ASTNodeType.A_FOR)
        node.left = init
        node.mid = cond
        node.right = incr
        node.mid.right = body
        return node

    def function_call(self) -> ASTNode:
        """
        function_call= IDENT LPAREN expression_list? RPAREN SEMI
        """
        func_name = self.curr.tok_str
        self.match(TokenType.T_IDENT)
        self.lparen()
        args = self.expression_list() if self.curr.token != TokenType.T_RPAREN else None
        self.rparen()
        node = ASTNode(ASTNodeType.A_FUNCCALL)
        node.strlit = func_name
        node.right = args
        return node

    def expression_list(self) -> ASTNode:
        """
        expression_list= expression (COMMA expression_list)*
        """
        root = self.expression()
        node = root
        while self.curr.token == TokenType.T_COMMA:
            self.comma()
            next_arg = self.expression()
            node.mid = next_arg
            node = next_arg
        return root

    def expression(self) -> ASTNode:
        """
        expression= bitwise_expression
        """
        return self.bitwise_expression()

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
        left = self.relational_expression()
        while self.curr.token in (TokenType.T_AMPER, TokenType.T_OR, TokenType.T_XOR):
            op = self.map_token_to_ast_op(self.curr.token)
            self.match(self.curr.token)
            right = self.relational_expression()
            left = ExprProcessor.binop(left, op, right)
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
        left = self.shift_expression()
        while self.curr.token in (TokenType.T_EQ, TokenType.T_NE, TokenType.T_LT, TokenType.T_GT, TokenType.T_LE,
                                  TokenType.T_GE):
            op = self.map_token_to_ast_op(self.curr.token)
            self.match(self.curr.token)
            right = self.shift_expression()
            left = ExprProcessor.binop(left, op, right)
        return left

    def shift_expression(self) -> ASTNode:
        """
        shift_expression= additive_expression
                        ( LSHIFT additive_expression
                        | RSHIFT additive_expression
                        )*
        """
        left = self.additive_expression()
        while self.curr.token in (TokenType.T_LSHIFT, TokenType.T_RSHIFT):
            op = self.map_token_to_ast_op(self.curr.token)
            self.match(self.curr.token)
            right = self.additive_expression()
            left = ExprProcessor.binop(left, op, right)
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
        left = self.multiplicative_expression()
        while self.curr.token in (TokenType.T_PLUS, TokenType.T_MINUS):
            op = self.map_token_to_ast_op(self.curr.token)
            self.match(self.curr.token)
            right = self.multiplicative_expression()
            left = ExprProcessor.binop(left, op, right)
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
        while self.curr.token in (TokenType.T_STAR, TokenType.T_SLASH, TokenType.T_MOD):
            op = self.map_token_to_ast_op(self.curr.token)
            self.match(self.curr.token)
            right = self.factor()
            left = ExprProcessor.binop(left, op, right)
        return left

    def factor(self) -> ASTNode | None:
        """
        factor= NUMLIT
              | TRUE
              | FALSE
              | variable
        """
        token = self.curr.token
        if token == TokenType.T_LPAREN:
            self.lparen()
            expr = self.expression()
            self.rparen()
            return expr
        elif token == TokenType.T_IDENT:
            if self.peek_is(TokenType.T_LPAREN):
                return self.function_call()
            else:
                return self.variable()
        elif token == TokenType.T_NUMLIT:
            node = self.gen_number_node(self.curr)
            self.match(token)
            return node
        elif token == TokenType.T_STRLIT:
            node = ASTNode(ASTNodeType.A_STRLIT)
            node.strlit = self.curr.tok_str
            self.match(token)
            return node
        elif token == TokenType.T_TRUE or token == TokenType.T_FALSE:
            node = ASTNode(ASTNodeType.A_NUMLIT)
            node.numlit.intval = 1 if token == TokenType.T_TRUE else 0
            node.type = ty_bool
            self.match(token)
            return node
        elif token in (TokenType.T_MINUS, TokenType.T_PLUS, TokenType.T_LOGNOT, TokenType.T_INVERT):
            op = self.map_token_to_ast_op(token)
            self.match(token)
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
        self.match(TokenType.T_IDENT)
        node = ASTNode(ASTNodeType.A_IDENT)
        node.strlit = name
        node.sym = self.find_symbol(name)
        if not node.sym:
            fatal(f"Unknown variable {name}")
        node.type = node.sym.type
        return node

    def is_type_token(self, token: TokenType) -> bool:
        return token in (
            TokenType.T_VOID, TokenType.T_BOOL, TokenType.T_INT8, TokenType.T_INT16,
            TokenType.T_INT32, TokenType.T_INT64, TokenType.T_UINT8, TokenType.T_UINT16,
            TokenType.T_UINT32, TokenType.T_UINT64, TokenType.T_FLT32, TokenType.T_FLT64
        )

    def map_token_to_ast_op(self, token: TokenType) -> ASTNodeType:
        op_map = {
            TokenType.T_PLUS: ASTNodeType.A_ADD,
            TokenType.T_MINUS: ASTNodeType.A_SUBTRACT,
            TokenType.T_STAR: ASTNodeType.A_MULTIPLY,
            TokenType.T_SLASH: ASTNodeType.A_DIVIDE,
            TokenType.T_MOD: ASTNodeType.A_MOD,
            TokenType.T_EQ: ASTNodeType.A_EQ,
            TokenType.T_NE: ASTNodeType.A_NE,
            TokenType.T_LT: ASTNodeType.A_LT,
            TokenType.T_GT: ASTNodeType.A_GT,
            TokenType.T_LE: ASTNodeType.A_LE,
            TokenType.T_GE: ASTNodeType.A_GE,
            TokenType.T_LSHIFT: ASTNodeType.A_LSHIFT,
            TokenType.T_RSHIFT: ASTNodeType.A_RSHIFT,
            TokenType.T_AMPER: ASTNodeType.A_AND,
            TokenType.T_OR: ASTNodeType.A_OR,
            TokenType.T_XOR: ASTNodeType.A_XOR,
            TokenType.T_INVERT: ASTNodeType.A_INVERT,
            TokenType.T_LOGNOT: ASTNodeType.A_NOT
        }
        return op_map.get(token, ASTNodeType.A_ADD)

    # Placeholder methods that need implementation from other modules
    def add_function(self, func: ASTNode, paramlist: ASTNode) -> None:
        # FuncProcessor.add_function(func.sym.name, func.type, [])
        return

    def declare_function(self, func: ASTNode, body: ASTNode = None) -> None:
        # FuncProcessor.declare_function(func.sym.name, func.type, [], body)
        return

    def gen_func_statement_block(self, s: ASTNode) -> None:
        # FuncProcessor.gen_func_statement_block(s.sym, s)
        return

    def declaration_statement(self, ident: ASTNode, expr: ASTNode) -> ASTNode:
        return gen_stat_declare(ident, expr)

    def find_symbol(self, name: str) -> Sym:
        return self.finder.find_symbol(name)
