"""
Note: You can grep '//-' this file to extract the grammar
"""

from typing import List, Optional

from defs import (
    NodeType, ValType, TokType, OpCode, Keyword,
    Token, SymType, Operator, ASTNode, fatal
)
from asts import (
    UnaryOp, BinaryOp, CallNode, LiteralNode, IdentNode, VariableNode,
    FunctionNode, IfNode, ForNode, WhileNode, PrintfNode
)
from lexer import Lexer, TokenQueue
from stmts import fit_int_type, cast_node
from syms import curr_scope


class Parser:
    queue: TokenQueue = None

    def __init__(self, lexer: Lexer = None):
        self.queue = TokenQueue(lexer.scan())

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
        return self.function_declaration_list()

    def function_declaration_list(self) -> Optional[ASTNode]:
        """
        //- function_declaration_list= function_declaration*
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
        node = self.function_prototype()
        if not curr_scope.find_symbol(node.sym.name, SymType.S_FUNC):
            curr_scope.add_symbol(node.sym, True) # 添加到符号表
        if self.semi(False):
            return node
        node.left = self.statement_block()
        return node

    def function_prototype(self) -> ASTNode:
        """
        //- function_prototype= ident_declaration LPAREN ident_declaration_list RPAREN
        //-                   | ident_declaration LPAREN VOID RPAREN
        """
        node = self.ident_declaration(SymType.S_FUNC)
        self.lparen()
        if not self.match_kw(Keyword.VOID, False):
            node.args = self.ident_declaration_list()
        self.rparen()
        return node

    def ident_declaration_list(self) -> List[ASTNode]:
        """
        //- ident_declaration_list= ident_declaration (COMMA ident_declaration_list)*
        """
        nodes = [self.ident_declaration(), ]
        while self.comma(False):
            nodes.append(self.ident_declaration())
        return nodes

    def ident_declaration(self, sym_type: SymType = SymType.S_LOCAL) -> Optional[ASTNode]:
        """
        //- ident_declaration= type IDENT
        """
        val_type = self.type_declaration()
        curr = self.queue.curr_token()
        if curr.tok_type != TokType.T_IDENT:
            return None
        self.next_token()
        if sym_type == SymType.S_FUNC:
            return FunctionNode(curr.text, val_type)
        elif sym_type == SymType.S_VAR:
            return VariableNode(curr.text, val_type)
        else:
            return IdentNode(curr.text, val_type)

    def type_declaration(self) -> ValType:
        """
        //- type= built-in type | user-defined type
        """
        curr = self.queue.curr_token()
        if curr.tok_type != TokType.T_KEYWORD:
            fatal(f"Unknown type {curr}")
        self.next_token()
        return ValType(curr.text)

    def declaration_stmt_list(self) -> ASTNode:
        """
        //- declaration_stmt_list= (ident_declaration ASSIGN expression SEMI)+
        """
        node = ASTNode(NodeType.A_GLUE)
        while True:
            curr = self.queue.curr_token()
            if not curr.is_type():
                break
            var = self.ident_declaration(SymType.S_VAR)
            if self.assign(False):
                var.assign(self.expression())
            self.semi()
            node.args.append(var)
        return node

    def procedural_stmt_list(self) -> ASTNode:
        """
        //- procedural_stmt_list= procedural_stmt*
        """
        node = ASTNode(NodeType.A_GLUE)
        while True:
            last = self.procedural_stmt()
            if not last:
                break
            node.args.append(last)
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
                return self.function_call(curr)
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

    def statement_block(self) -> Optional[ASTNode]:
        """
        //- statement_block= LBRACE procedural_stmt* RBRACE
        //-                | LBRACE declaration_stmt* procedural_stmt* RBRACE
        """
        self.lbrace()
        if self.rbrace(False):
            return None
        node = self.declaration_stmt_list()
        proc = self.procedural_stmt_list()
        self.rbrace()
        node.args.extend(proc.args)
        return node

    def print_statement(self) -> ASTNode:
        self.match_kw(Keyword.PRINTF)
        self.lparen()
        left = self.factor()
        assert isinstance(left, LiteralNode) and left.string != ""
        self.comma()
        right = self.expression()
        self.rparen()
        self.semi()
        if right.val_type == ValType.FLOAT32:
            right = cast_node(right, ValType.FLOAT64)
        return PrintfNode(left, right)

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
        elif curr_op.value == OpCode.SUB:
            curr_op.value = OpCode.NEG
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
        //- factor= number
        //-       | string
        //-       | "true"
        //-       | "false"
        //-       | "null"
        //-       | variable
        //-       | call
        """
        curr = self.queue.curr_token()
        node = self.literal(curr)
        if node:
            self.next_token()
            return node
        elif curr.tok_type == TokType.T_IDENT:
            if self.lparen(False):
                return self.function_call(curr)
            else:
                return self.variable(curr)
        elif curr.tok_type == TokType.T_OPERATOR:
            if curr.value == OpCode.LPAREN:
                self.lparen()
                expr = self.expression()
                self.rparen()
                return expr
            elif curr.value in (OpCode.SUB, OpCode.ADD, OpCode.NOT, OpCode.INVERT):
                self.next_token()
                op = NodeType(curr.value)
                node = UnaryOp(op, self.factor())
                return node
        return fatal(f"Unexpected token {curr} in factor")

    @staticmethod
    def literal(curr: Token) -> Optional[ASTNode]:
        if curr.tok_type in (TokType.T_INTEGER, TokType.T_FLOAT):
            node = LiteralNode(curr.text)
            node.number = curr.value
            node.val_type = ValType.FLOAT64
            if curr.tok_type == TokType.T_INTEGER:
                node.val_type = fit_int_type(curr.value)
            return node
        elif curr.tok_type == TokType.T_STRING:
            node = LiteralNode(curr.text)
            return node
        elif curr.tok_type == TokType.T_KEYWORD:
            node = LiteralNode(curr.text)
            if curr.text == "null":
                node.val_type = ValType.VOID
            elif curr.text in ("true", "false"):
                node.val_type = ValType.BOOL
                node.number = 1 if curr.text == "true" else 0
            else:
                fatal(f"Unexpected token {curr} in literal")
            return node
        return None

    def variable(self, curr: Token) -> ASTNode:
        """
        //- variable= IDENT
        """
        self.match_type(TokType.T_IDENT)
        node = VariableNode(curr.text)
        sym = curr_scope.find_symbol(curr.text)
        if not sym:
            fatal(f"Unknown variable {curr.text}")
        node.set_sym(sym)
        return node


    def function_call(self, curr: Token) -> ASTNode:
        """
        //- function_call= IDENT LPAREN expression_list? RPAREN SEMI
        """
        args = None
        if not self.rparen(False):
            args = self.expression_list()
            self.rparen()
        self.semi()
        return CallNode(curr.text, args)
