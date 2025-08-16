from typing import Optional

from defs import Symbol, SymType, fatal
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
        """ 在所有作用域中查找符号，从当前作用域向上查找 """
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

    def add_symbol(self, sym: Symbol, is_global: bool = False) -> None:
        """将符号添加到当前作用域"""
        if not sym or not sym.name:
            fatal("Invalid symbol")
        obj = self
        # 如果是全局符号，添加到全局符号列表
        if is_global and sym.sym_type != SymType.S_LOCAL:
            while obj.parent is not None:
                obj = obj.parent
        if sym.name not in obj.sym_table:
            obj.sym_table[sym.name] = sym
        elif is_global and sym.sym_type == SymType.S_FUNC:
            fatal(f"Multiple declarations for {sym.name}()")
        else:
            fatal(f"Symbol {sym.name} already exists")
