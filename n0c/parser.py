"""
Note: You can grep '//-' this file to extract the grammar
"""
import sys
from typing import List, Optional

from defs import (
    NodeType, ValType, TokType, SymType, OpCode, Keyword,
    Token, Operator, Symbol, ASTNode, fatal
)
from funcs import add_function, declare_function, gen_func_statement_block
from lexer import Lexer, TokenQueue
from genast import (UnaryOp, BinaryOp, BlockNode, CallNode,
                    IfNode, ForNode, WhileNode, PrintfNode)
from stmts import cast_node, gen_stat_declare, fit_int_type
from syms import Scope


class Parser:
    queue: TokenQueue = None
    scope: Scope = None

    def __init__(self, lexer: Lexer = None):
        self.queue = TokenQueue(lexer.scan())
        self.scope = Scope()

    def next_token(self) -> Optional[Token]:
        tk = self.queue.next_token()
        while True:
            if tk.tok_type not in (TokType.T_COMMENT, TokType.T_WHITESPACE):
                return tk
            tk = self.queue.next_token()

    def match_type(self, token_type: TokType, throw: bool = True) -> bool:
        curr = self.queue.curr_token()
        if curr.tok_type == token_type:
            self.next_token()
            return True
        if throw:
            fatal(f"Unexpected token {curr}, expected {token_type.name}")
        return False

    def match_kw(self, kw: Keyword, throw: bool = True) -> bool:
        curr = self.queue.curr_token()
        if curr.tok_type == TokType.T_KEYWORD and curr.text == kw.value:
            self.next_token()
            return True
        if throw:
            fatal(f"Unexpected token {curr}, expected {kw.value}")
        return False

    def match_ops(self, *op_codes, **kwargs) -> Optional[Operator]:
        curr = self.queue.curr_token()
        if isinstance(curr, Operator) and curr.value in op_codes:
            self.next_token()
            return curr
        if kwargs.get("throw", False):
            fatal(f"Unexpected token {curr}, expected {op_codes}")
        return None

    def match_infix(self, **kwargs) -> Optional[Operator]:
        curr = self.queue.curr_token()
        if isinstance(curr, Operator) and curr.prece > 0:
            self.next_token()
            return curr
        if kwargs.get("throw", False):
            fatal(f"Unexpected token {curr}")
        return None

    def is_eof(self) -> bool:
        return self.match_type(TokType.T_EOF, False)

    def comma(self, throw: bool = True):
        return self.match_ops(OpCode.COMMA, throw=throw)

    def semi(self, throw: bool = True):
        return self.match_ops(OpCode.SEMI, throw=throw)

    def lbrace(self, throw: bool = True):
        return self.match_ops(OpCode.LBRACE, throw=throw)

    def rbrace(self, throw: bool = True):
        return self.match_ops(OpCode.RBRACE, throw=throw)

    def lparen(self, throw: bool = True):
        return self.match_ops(OpCode.LPAREN, throw=throw)

    def rparen(self, throw: bool = True):
        return self.match_ops(OpCode.RPAREN, throw=throw)

    def assign(self, throw: bool = True):
        return self.match_ops(OpCode.ASSIGN, throw=throw)

    def parse_program(self) -> Optional[ASTNode]:
        if self.queue is None:
            fatal("Lexer or TokenQueue is not initialized")
        return self.function_declarations()

    def function_declarations(self) -> Optional[ASTNode]:
        """
        //- function_declarations= function_declaration*
        """
        node = None
        while not self.is_eof():
            node = self.function_declaration()
        return node

    def function_declaration(self) -> ASTNode:
        """
        //- function_declaration= function_prototype statement_block
        //-                     | function_prototype SEMI
        """
        node, params = self.function_prototype()
        if self.semi(False):
            sym = add_function(node, params)
            self.scope.add_symbol(sym, True) # 添加到符号表
            return node
        body = self.statement_block()
        node = declare_function(node, params, body)
        self.scope = self.scope.new_scope(node.sym.name)
        gen_func_statement_block(node.sym, body)
        self.scope = self.scope.end_scope()
        return node

    def function_prototype(self):
        """
        //- function_prototype= typed_declaration LPAREN typed_declaration_list RPAREN
        //-                   | typed_declaration LPAREN VOID RPAREN
        """
        node, params = self.typed_declaration(), []
        self.lparen()
        if not self.match_kw(Keyword.VOID, False):
            node.left, params = self.typed_declaration_list()
        self.rparen()
        return node, params

    def typed_declaration_list(self):
        """
        //- typed_declaration_list= typed_declaration (COMMA typed_declaration_list)*
        """
        first = self.typed_declaration()
        node, sym_list = first, [first.sym, ]
        while self.comma(False):
            next_node = self.typed_declaration()
            sym_list.append(next_node.sym)
            node.mid = next_node
            node = next_node
        return first, sym_list

    def typed_declaration(self) -> ASTNode:
        """
        //- typed_declaration= type IDENT
        """
        type_obj = self.get_type()
        node = self.get_id(type_obj)
        return node

    def declaration_stmts(self) -> ASTNode:
        """
        //- declaration_stmts= (typed_declaration ASSIGN expression SEMI)+
        """
        node, last = None, None
        while True:
            curr = self.queue.curr_token()
            if not curr.is_type():
                break
            decl = self.typed_declaration()
            if self.assign(False):
                expr = self.expression()
                decl = gen_stat_declare(decl, expr)
            self.semi()
            if not node:
                node = decl
            else:
                last.right = decl
            last = decl
        return node

    def procedural_stmts(self) -> ASTNode:
        """
        //- procedural_stmts= procedural_stmt*
        """
        node, last = None, None
        while True:
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
        return node

    def procedural_stmt(self) -> Optional[ASTNode]:
        """
        解析单个过程语句，可能返回None
        //- procedural_stmt= ( print_stmt
        //-                  | assign_stmt
        //-                  | if_stmt
        //-                  | while_stmt
        //-                  | for_stmt
        //-                  | function_call
        //-                  )
        """
        curr = self.queue.curr_token()
        if curr.tok_type == TokType.T_OPERATOR and curr.value == OpCode.RBRACE:
            return None
        if curr.tok_type == TokType.T_IDENT:
            if self.lparen(False):
                return self.function_call()
            else:
                return self.assign_stmt()
        if curr.tok_type == TokType.T_KEYWORD:
            if curr.text == Keyword.PRINTF.value:
                return self.print_statement()
            elif curr.text == Keyword.IF.value:
                return self.if_stmt()
            elif curr.text == Keyword.WHILE.value:
                return self.while_stmt()
            elif curr.text == Keyword.FOR.value:
                return self.for_stmt()
        return fatal(f"Unexpected token {curr.tok_type}:{curr.text} in procedural statement")

    def get_type(self) -> str:
        """
        //- type= built-in type | user-defined type
        """
        curr = self.queue.curr_token()
        if curr.tok_type != TokType.T_KEYWORD:
            fatal(f"Unknown type {curr}")
        self.next_token()
        return curr.text

    def get_id(self, type_str: str) -> Optional[ASTNode]:
        curr = self.queue.curr_token()
        if curr.tok_type != TokType.T_IDENT:
            return None
        self.next_token()
        node = ASTNode(NodeType.A_IDENT)
        node.sym = Symbol(
            name = curr.text,
            sym_type = SymType.S_LOCAL,
            val_type = ValType(type_str),
        )
        return node

    def statement_block(self) -> Optional[ASTNode]:
        """
        //- statement_block= LBRACE procedural_stmt* RBRACE
        //-                | LBRACE declaration_stmt* procedural_stmt* RBRACE
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
        return node

    def print_statement(self) -> ASTNode:
        self.match_kw(Keyword.PRINTF)
        self.lparen()
        left = self.factor()
        assert left.op == NodeType.A_LITERAL
        assert left.string != ""
        self.comma()
        right = self.expression()
        self.rparen()
        self.semi()
        if right.val_type == ValType.FLOAT32:
            right = cast_node(right, ValType.FLOAT64)
        return PrintfNode(left, right)

    def function_call(self) -> ASTNode:
        """
        //- function_call= IDENT LPAREN expression_list? RPAREN SEMI
        """
        name = self.queue.curr_token().text
        self.match_type(TokType.T_IDENT)
        self.lparen()
        args = None if self.rparen(False) else self.expression_list()
        self.rparen()
        self.semi()
        return CallNode(name, args)

    def assign_stmt(self) -> ASTNode:
        """
        //- assign_stmt= variable ASSIGN expression SEMI
        """
        left = self.expression()
        self.assign()
        right = self.expression()
        self.semi()
        node = ASTNode(NodeType.A_ASSIGN, left=left, right=right)
        return node

    def if_stmt(self) -> ASTNode:
        """
        //- if_stmt= IF LPAREN relational_expression RPAREN statement_block
        //-          (ELSE statement_block)?
        """
        self.match_kw(Keyword.IF)
        self.lparen()
        cond = self.expression()
        self.rparen()
        then_stmt = self.statement_block()
        else_stmt = None
        if self.match_kw(Keyword.ELSE, False):
            else_stmt = self.statement_block()
        return IfNode(cond, then_stmt, else_stmt)

    def for_stmt(self) -> ASTNode:
        """
        //- for_stmt= FOR LPAREN assign_stmt relational_expression SEMI
        //-           short_assign_stmt RPAREN statement_block
        """
        self.match_kw(Keyword.FOR)
        self.lparen()
        init = None if self.semi(False) else self.expression()
        cond = None if self.semi(False) else self.expression()
        incr = None if self.rparen(False) else self.expression()
        body = self.statement_block()
        return ForNode(cond, init, incr, body)

    def while_stmt(self) -> ASTNode:
        """
        //- while_stmt= WHILE LPAREN relational_expression RPAREN statement_block
        """
        self.match_kw(Keyword.WHILE)
        self.lparen()
        cond = self.expression()
        self.rparen()
        body = self.statement_block()
        return WhileNode(cond, body)

    def expression_list(self) -> ASTNode:
        """
        //- expression_list= expression (COMMA expression_list)*
        """
        expr = self.expression()
        node = ASTNode(NodeType.A_GLUE, left=expr)
        while self.comma(False):
            expr = self.expression()
            node = ASTNode(NodeType.A_GLUE, left=expr, right=node)
        return node

    def expression(self) -> ASTNode:
        """
        //- expression= (prefix_op factor
        //-                      | factor)
        //-             (infix_op factor)*
        """
        left, curr_op = None, self.match_ops(*Operator.unary_ops)
        if curr_op is None: # 没有前缀运算符
            left, curr_op = self.factor(), self.match_infix()
        while curr_op is not None: # 表达式未结束
            left, curr_op = self.infix_expression(left, curr_op)
        return left

    def infix_expression(self, left, curr_op):
        right, next_op = self.factor(), self.match_infix()
        while next_op and next_op.prece > curr_op.prece:
            right, next_op = self.infix_expression(right, next_op)
        op = NodeType(curr_op.value)
        if left is None:
            right = UnaryOp(op, right)
        else:
            right = BinaryOp(left, op, right)
        return right, next_op

    def factor(self) -> Optional[ASTNode]:
        """
        //- factor= NUMBER
        //-       | TRUE
        //-       | FALSE
        //-       | variable
        """
        curr = self.queue.curr_token()
        if curr.tok_type == TokType.T_IDENT:
            if self.lparen(False):
                return self.function_call()
            else:
                return self.variable()
        elif curr.tok_type in (TokType.T_INTEGER, TokType.T_FLOAT):
            node = ASTNode(NodeType.A_LITERAL)
            node.number = curr.value
            node.val_type = ValType.FLOAT64
            if curr.tok_type == TokType.T_INTEGER:
                node.val_type = fit_int_type(curr.value)
            self.next_token()
            return node
        elif curr.tok_type == TokType.T_STRING:
            node = ASTNode(NodeType.A_LITERAL)
            node.string = curr.text
            node.val_type = ValType.STR
            self.next_token()
            return node
        elif curr.tok_type == TokType.T_KEYWORD:
            node = ASTNode(NodeType.A_LITERAL)
            if curr.text == "null":
                node.val_type = ValType.VOID
            elif curr.text in ("true", "false"):
                node.val_type = ValType.BOOL
            else:
                fatal(f"Unexpected token {curr} in factor")
            self.next_token()
            return node
        elif curr.tok_type == TokType.T_OPERATOR:
            if curr.value == OpCode.LPAREN:
                self.lparen()
                expr = self.expression()
                self.rparen()
                return expr
            elif curr.value in (OpCode.SUB, OpCode.ADD, OpCode.NOT, OpCode.INVERT):
                self.next_token()
                op = NodeType(curr.value)
                node = ASTNode(op, right = self.factor())
                return node
        return fatal(f"Unexpected token {curr} in factor")

    def variable(self) -> ASTNode:
        """
        //- variable= IDENT
        """
        curr = self.queue.curr_token()
        self.match_type(TokType.T_IDENT)
        node = ASTNode(NodeType.A_IDENT)
        node.string = curr.text
        node.sym = self.scope.find_symbol(node.string)
        if not node.sym:
            fatal(f"Unknown variable {node.string}")
        node.val_type = node.sym.val_type
        return node
