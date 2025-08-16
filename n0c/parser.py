"""
Note: You can grep '//-' this file to extract the grammar
"""

from typing import List, Optional, Union

from defs import (
    NodeType, ValType, TokType, OpCode, Keyword,
    Token, SymType, Operator, ASTNode, fatal
)
from asts import (
    UnaryOp, BinaryOp, CallNode, LiteralNode, IdentNode, VariableNode,
    FunctionNode, IfNode, ForNode, WhileNode, PrintfNode, AssignNode
)
from lexer import Lexer, TokenQueue
from stmts import fit_int_type, widen_type
from syms import Scope


class Parser:
    queue: TokenQueue = None
    scope: Scope = None

    def __init__(self, lexer: Lexer = None):
        self.queue = TokenQueue(lexer.scan())
        self.scope = Scope("global")

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

    def peek_ops(self, *op_codes, ahead = 1) -> Optional[Operator]:
        tok = self.queue.get_token(ahead=ahead)
        if isinstance(tok, Operator) and tok.value in op_codes:
            return tok
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
        node = ASTNode(NodeType.A_GLUE)
        while not self.is_eof():
            decl = self.function_declaration()
            node.args.append(decl)
        return node

    def function_declaration(self) -> FunctionNode:
        """
        //- function_declaration= function_prototype statement_block
        //-                     | function_prototype SEMI
        """
        node = self.function_prototype()
        sym = node.new_symbol()
        if not sym:
            return node
        self.scope.add_symbol(sym, is_global=True)
        self.scope = self.scope.new_scope(node.sym.name)
        for i, arg in enumerate(node.args):
            if isinstance(arg, IdentNode):
                arg = VariableNode.from_ident(arg)
                sym = arg.new_symbol()
                self.scope.add_symbol(sym)
                node.args[i] = arg
        if not self.semi(False):
            node.left = self.statement_block()
        self.scope = self.scope.end_scope()
        return node

    def function_prototype(self) -> FunctionNode:
        """
        //- function_prototype= ident_declaration LPAREN ident_declaration_list RPAREN
        //-                   | ident_declaration LPAREN VOID RPAREN
        """
        node = self.ident_declaration(is_func=True)
        self.lparen()
        if not self.match_kw(Keyword.VOID, False):
            node.args = self.ident_declaration_list()
        self.rparen()
        return node

    def type_declaration(self) -> ValType:
        """
        //- type= built-in type | user-defined type
        """
        curr = self.queue.curr_token()
        if curr.tok_type != TokType.T_KEYWORD:
            fatal(f"Unknown type {curr}")
        self.next_token()
        return ValType(curr.text)

    def ident_declaration_list(self) -> List[ASTNode]:
        """
        //- ident_declaration_list= ident_declaration (COMMA ident_declaration_list)*
        """
        nodes = [self.ident_declaration(), ]
        while self.comma(False):
            nodes.append(self.ident_declaration())
        return nodes

    def ident_declaration(self, is_func = False) -> Union[None, IdentNode, FunctionNode]:
        """
        //- ident_declaration= type IDENT
        """
        val_type = self.type_declaration()
        curr = self.queue.curr_token()
        if curr.tok_type != TokType.T_IDENT:
            return None
        self.next_token()
        if is_func:
            return FunctionNode(curr.text, val_type)
        else:
            return IdentNode(curr.text, val_type)

    def declaration_stmt_list(self) -> ASTNode:
        """
        //- declaration_stmt_list= (ident_declaration ASSIGN expression SEMI)+
        """
        node = ASTNode(NodeType.A_GLUE)
        while True:
            curr = self.queue.curr_token()
            if not curr.is_type():
                break
            decl = self.ident_declaration()
            if self.assign(False):
                expr = self.expression()
                decl = VariableNode.from_ident(decl, expr)
                sym = decl.new_symbol(has_addr=True)
                if sym:
                    self.scope.add_symbol(sym)
            self.semi()
            node.args.append(decl)
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
        //-                  | short_assign_stmt
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
            if self.peek_ops(OpCode.LPAREN):
                proc = self.function_call(curr)
            else:
                proc = self.short_assign_stmt()
                self.semi()
            return proc
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
            right = widen_type(right, ValType.FLOAT64)
        return PrintfNode(left, right)

    def short_assign_stmt(self) -> AssignNode:
        """
        //- short_assign_stmt= variable ASSIGN expression
        """
        curr = self.queue.curr_token()
        var = self.variable(curr)
        self.assign()
        right = self.expression()
        return AssignNode.create(var, right)

    def if_stmt(self) -> IfNode:
        """
        //- if_stmt= IF LPAREN relational_expression RPAREN statement_block
        //-          (ELSE statement_block)?
        """
        self.match_kw(Keyword.IF)
        self.lparen()
        cond = self.expression(min_op=OpCode.LOG_OR)
        self.rparen()
        then_stmt = self.statement_block()
        else_stmt = None
        if self.match_kw(Keyword.ELSE, False):
            else_stmt = self.statement_block()
        return IfNode(cond, then_stmt, else_stmt)

    def while_stmt(self) -> WhileNode:
        """
        //- while_stmt= WHILE LPAREN relational_expression RPAREN statement_block
        """
        self.match_kw(Keyword.WHILE)
        self.lparen()
        cond = self.expression(min_op=OpCode.LOG_OR)
        self.rparen()
        body = self.statement_block()
        return WhileNode(cond, body)

    def for_stmt(self) -> ForNode:
        """
        //- for_stmt= FOR LPAREN short_assign_stmt SEMI relational_expression SEMI
        //-           short_assign_stmt RPAREN statement_block
        """
        self.match_kw(Keyword.FOR)
        self.lparen()
        cond, init, incr = None, None, None
        if not self.semi(False):
            init = self.short_assign_stmt()
            self.semi()
        if not self.semi(False):
            cond = self.expression(min_op=OpCode.LOG_OR)
            self.semi()
        if not self.rparen(False):
            incr = self.short_assign_stmt()
            self.rparen()
        body = self.statement_block()
        return ForNode(cond, init, body, incr)

    def expression_list(self) -> ASTNode:
        """
        //- expression_list= expression (COMMA expression_list)*
        """
        expr = self.expression()
        node = ASTNode(NodeType.A_GLUE)
        node.args.append(expr)
        while self.comma(False):
            expr = self.expression()
            node.args.append(expr)
        return node

    def expression(self, min_op = 0) -> ASTNode:
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
            if curr_op.prece < min_op:
                fatal(f"The expression operator {curr_op.name} is out of range.")
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
            if self.peek_ops(OpCode.LPAREN):
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
    def literal(curr: Token) -> Optional[LiteralNode]:
        if curr.tok_type == TokType.T_STRING:
            node = LiteralNode(curr.text)
            return node
        elif curr.tok_type in (TokType.T_INTEGER, TokType.T_FLOAT):
            node = LiteralNode(curr.text)
            node.number = curr.value
            node.val_type = ValType.FLOAT32
            if curr.tok_type == TokType.T_INTEGER:
                node.val_type = fit_int_type(curr.value)
            return node
        elif curr.tok_type in (TokType.T_BOOL, TokType.T_VOID):
            node = LiteralNode(curr.text)
            if curr.text == "null":
                node.val_type = ValType.VOID
            elif curr.text in ("true", "false"):
                node.val_type = ValType.BOOL
                node.number = curr.value
            else:
                fatal(f"Unexpected token {curr} in literal")
            return node
        return None

    def variable(self, curr: Token) -> IdentNode:
        """
        //- variable= IDENT
        """
        self.match_type(TokType.T_IDENT)
        node = IdentNode(curr.text)
        sym = self.scope.get_symbol(node.name, SymType.S_VAR)
        node.set_symbol(sym)
        return node


    def function_call(self, curr: Token) -> CallNode:
        """
        //- function_call= IDENT LPAREN expression_list? RPAREN SEMI
        """
        self.match_type(TokType.T_IDENT)
        self.lparen()
        args = None
        if not self.rparen(False):
            args = self.expression_list()
            self.rparen()
        self.semi()
        node = CallNode(curr.text, args)
        # 获取函数原型
        sym = self.scope.get_symbol(node.name, SymType.S_FUNC)
        node.set_symbol(sym)
        return node
