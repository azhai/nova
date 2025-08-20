from typing import Optional, List

from utils import fatal
from defs import ASTNode, Symbol, SymType, ValType
from cgen import cg_glob_sym


all_scopes = []


def gen_global_syms():
    if not all_scopes:
        return
    sym_table = all_scopes[0].sym_table
    for sym in sym_table.values():
        if sym.sym_type == SymType.S_VAR:
            cg_glob_sym(sym)


class Scope:
    parent = None
    name = ""
    sym_table = {}

    def __init__(self, name: str = "", parent = None):
        self.name, self.parent = name, parent
        self.sym_table = {}
        global all_scopes
        all_scopes.append(self)

    def new_scope(self, name: str):
        """ 创建新的作用域 """
        return Scope(name, self)

    def end_scope(self):
        """ 结束当前作用域，返回上一个 """
        return self.parent if self.parent else self

    def find_symbol(self, name: str) -> Optional[Symbol]:
        """ 在所有作用域中查找符号，从当前作用域向上查找 """
        obj = self
        while obj is not None:
            sym = obj.sym_table.get(name)
            if sym:
                return sym
            obj = obj.parent
        return None

    def get_symbol(self, name: str, sym_type = None) -> Optional[Symbol]:
        """ 在所有作用域中查找符号，并检查符号类型 """
        sym = self.find_symbol(name)
        type_name = "symbol"
        if sym_type == SymType.S_FUNC:
            type_name = "function"
        elif sym_type == SymType.S_VAR:
            type_name = "variable"
        if not sym:
            fatal(f"Unknown {type_name} {name}")
        if sym_type and sym.sym_type != sym_type:
            fatal(f"Symbol {name} is not a {type_name}")
        return sym

    def update_symbol(self, name: str, **kwargs) -> Optional[Symbol]:
        """ 更新符号部分属性 """
        sym = self.sym_table.get(name)
        if not sym:
            fatal(f"Can not find symbol {name}")
            return None
        sym.__dict__.update(kwargs)
        self.sym_table[name] = sym
        return sym

    def add_symbol(self, sym: Symbol, is_global: bool = False):
        """ 将符号添加到当前作用域 """
        if not sym or not sym.name:
            fatal("Invalid symbol")
        obj, global_func = self, False
        # 如果是全局符号，添加到全局符号列表
        if is_global and sym.sym_type != SymType.S_LOCAL:
            if sym.sym_type == SymType.S_FUNC:
                global_func = True
            while obj.parent is not None:
                obj = obj.parent
        old = obj.sym_table.get(sym.name)
        if old is None or global_func and (old.has_body is False):
            obj.sym_table[sym.name] = sym
            return
        if global_func:
            fatal(f"Multiple declarations for {sym.name}()")
        else:
            fatal(f"Symbol {sym.name} already exists")

    @staticmethod
    def check_func_params(sym: Symbol, val_type: ValType, params: List[Symbol]):
        """ 检查函数原型和实现的参数、返回是否一致 """
        if val_type != sym.val_type:
            fatal(f"{sym.name}() declaration has different type than previous: {val_type} vs {sym.val_type}")
        if len(sym.args) != len(params):
            fatal(f"{sym.name}() declaration: # params different than previous")
        for i, arg in enumerate(sym.args):
            try:
                param = params[i]
            except IndexError:
                fatal(f"{sym.name}() declaration: # params different than previous")
                break
            if param.name != arg.name:
                fatal(f"{sym.name}() declaration: param name mismatch {param.name} vs {arg.name}")
            elif param.val_type != arg.val_type:
                fatal(f"{sym.name}() declaration: param {arg.name} type mismatch {param.val_type} vs {arg.val_type}")

    @staticmethod
    def check_call_params(sym: Symbol, params: List[ASTNode]):
        """ 检查函数原型和调用的参数是否符合 """
        if len(sym.args) > len(params):
            fatal(f"{sym.name}() declaration: # params different than previous")
        for i, arg in enumerate(sym.args):
            try:
                param = params[i]
            except IndexError:
                fatal(f"{sym.name}() declaration: # params different than previous")
                break
            if param.val_type != arg.val_type:
                fatal(f"{sym.name}() declaration: param {arg.name} type mismatch {param.val_type} vs {arg.val_type}")
