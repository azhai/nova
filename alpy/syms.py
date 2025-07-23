from typing import Optional, List, Dict

from alpy.defs import ASTNode
from defs import Sym, SymType, OutFile, TypeKind, fatal

class SymTable:
    """ 符号表节点 """
    scope: str
    parent: Optional['SymTable']
    # children: Dict[str, 'SymTable']
    # sym_dict: Dict[str, Sym]

    def __init__(self, scope: str, parent: Optional['SymTable'] = None):
        self.scope = scope
        self.parent = parent
        self.children = {}
        self.sym_dict = {}


# class SymProcessor:
#     def __init__(self):
#         self.sym_stack: List[Dict[str, Sym]] = [{}]  # 作用域栈，每个作用域是符号字典
#         self.GlobHead: Optional[Sym] = None  # 全局符号列表头
#         self.CurFunc: Optional[Sym] = None  # 当前函数

    def set_cur_func(self, fn_sym: Sym) -> None:
        """设置当前函数"""
        self.CurFunc = fn_sym

    # @staticmethod
    # def add_sym_to(sym: Sym, sym_list: Optional[Sym]) -> Sym:
    #     """将符号添加到符号列表头部"""
    #     if not sym:
    #         return sym_list
    #     sym.sibling = sym_list
    #     return sym

    def add_symbol(self, sym: Sym, is_global: bool = False) -> None:
        """将符号添加到当前作用域"""
        if not sym or not sym.name:
            fatal("Invalid symbol")
        table = self
        # 如果是全局符号，添加到全局符号列表
        if is_global and sym.sym_type != SymType.SYM_LOCAL:
            while table.parent is not None:
                table = table.parent
        if sym.name in table.sym_dict:
            fatal(f"Symbol '{sym.name}' already declared in current scope")
        table.sym_dict[sym.name] = sym

        # 如果是全局符号，添加到全局符号列表
        # if is_global or len(self.sym_stack) == 1 and sym.sym_type != SymType.SYM_LOCAL:
        #     self.GlobHead = self.add_sym_to(sym, self.GlobHead)

    def find_symbol(self, name: str) -> Optional[Sym]:
        """ 在所有作用域中查找符号，从当前作用域向上查找 """
        # for scope in reversed(self.sym_stack):
        #     if name in scope:
        #         return scope[name]
        # return None
        st = self
        while st is not None:
            sym = st.sym_dict.get(name)
            if sym:
                return sym
            st = st.parent
        return None

    def new_scope(self, func: ASTNode):
        """ 创建新的作用域 """
        # self.sym_stack.append({})
        name = func.sym.name
        return SymTable(name, self)

    def end_scope(self):
        """ 结束当前作用域 """
        # if len(self.sym_stack) <= 1:
        #     fatal("Cannot end global scope")
        # self.sym_stack.pop()
        self.parent.children[self.scope] = self
        return self.parent

    def mk_ident(self, name: str) -> Sym:
        """ 创建或查找标识符符号 """
        sym = self.find_symbol(name)
        if sym:
            return sym

        # 创建新的标识符符号（默认为变量类型）
        from typs import get_type
        sym = Sym(
            name=name,
            sym_type=SymType.SYM_VAR,
            val_type=get_type(TypeKind.TY_INT64)  # 默认类型为int64
        )
        self.add_symbol(sym)
        return sym

    def gen_syms(self) -> None:
        """ 生成符号的代码 """
        from cgen import cgglobsym
        for sym in self.sym_dict.values():
            if sym.sym_type == SymType.SYM_VAR and sym.init_val is not None:
                cgglobsym(sym)

    def dump_syms(self) -> None:
        """ 打印符号表内容（调试用） """
        from typs import get_typename
        print(f"Scope {self.scope}:", file=OutFile)
        for name, sym in self.sym_dict.items():
            type_str = get_typename(sym.type)
            print(f"  {name}: type={type_str}, kind={sym.sym_type}", file=OutFile)
        for child in root.children.values():
            child.dump_syms()

def gen_glob_syms() -> None:
    """ 生成全局符号的代码 """
    root.gen_syms()

def dump_syms() -> None:
    """ 打印符号表内容（调试用） """
    print("Symbol table:", file=OutFile)
    root.dump_syms()


# 创建符号处理器实例并导出函数
root = SymTable("")
sym_processor = root
# sym_processor = SymProcessor()
set_cur_func = sym_processor.set_cur_func
add_symbol = sym_processor.add_symbol
find_symbol = sym_processor.find_symbol
# gen_glob_syms = sym_processor.gen_glob_syms
# dump_syms = sym_processor.dump_syms
