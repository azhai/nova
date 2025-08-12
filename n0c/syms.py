from typing import Optional

from defs import Symbol, SymType, fatal
from cgen import cg_glob_sym

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
        global curr_scope
        curr_scope = Scope(name, self)
        return curr_scope

    def end_scope(self):
        """ 结束当前作用域，返回上一个 """
        global curr_scope
        curr_scope = self.parent if self.parent else self
        return curr_scope

    def find_symbol(self, name: str, sym_type = None) -> Optional[Symbol]:
        """ 在所有作用域中查找符号，从当前作用域向上查找 """
        obj = self
        while obj is not None:
            sym = obj.sym_table.get(name)
            if sym:
                if sym_type and sym.sym_type != sym_type:
                    fatal(f"{name} is not a {sym_type.name}")
                return sym
            obj = obj.parent
        return None

    def add_symbol(self, sym: Symbol, is_global: bool = False) -> None:
        """将符号添加到当前作用域"""
        if not sym or not sym.name:
            fatal("Invalid symbol")
        obj = self
        # 如果是全局符号，添加到全局符号列表
        if is_global and sym.sym_type != SymType.S_LOCAL:
            while obj.parent is not None:
                obj = obj.parent
        if sym.name in obj.sym_table:
            fatal(f"Symbol '{sym.name}' already declared in current scope")
        obj.sym_table[sym.name] = sym


all_scopes = []
curr_scope = Scope("global")
