from typing import Optional, List, Dict
from defs import Sym, SymType, Outfh, TypeKind, fatal


class SymProcessor:
    def __init__(self):
        self.sym_stack: List[Dict[str, Sym]] = [{}]  # 作用域栈，每个作用域是符号字典
        self.GlobHead: Optional[Sym] = None  # 全局符号列表头
        self.CurFunc: Optional[Sym] = None  # 当前函数

    def set_cur_func(self, func: Sym) -> None:
        """设置当前函数"""
        self.CurFunc = func

    @staticmethod
    def add_sym_to(sym: Sym, sym_list: Optional[Sym]) -> Sym:
        """将符号添加到符号列表头部"""
        if not sym:
            return sym_list
        sym.next = sym_list
        return sym

    def add_symbol(self, sym: Sym, to_head: bool = False) -> None:
        """将符号添加到当前作用域"""
        if not sym or not sym.name:
            fatal("Invalid symbol")

        current_scope = self.sym_stack[-1]
        if sym.name in current_scope:
            fatal(f"Symbol '{sym.name}' already declared in current scope")

        current_scope[sym.name] = sym

        # 如果是全局符号，添加到全局符号列表
        if to_head or len(self.sym_stack) == 1 and sym.sym_type != SymType.SYM_LOCAL:
            self.GlobHead = self.add_sym_to(sym, self.GlobHead)

    def find_symbol(self, name: str) -> Optional[Sym]:
        """ 在所有作用域中查找符号，从当前作用域向上查找 """
        for scope in reversed(self.sym_stack):
            if name in scope:
                return scope[name]
        return None

    def new_scope(self) -> None:
        """ 创建新的作用域 """
        self.sym_stack.append({})

    def end_scope(self) -> None:
        """ 结束当前作用域 """
        if len(self.sym_stack) <= 1:
            fatal("Cannot end global scope")
        self.sym_stack.pop()

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

    def gen_glob_syms(self) -> None:
        """ 生成全局符号的代码 """
        from cgen import cgglobsym
        sym = self.GlobHead
        while sym:
            if sym.sym_type == SymType.SYM_VAR and sym.init_val is not None:
                cgglobsym(sym)
            sym = sym.next

    def dump_syms(self) -> None:
        """ 打印符号表内容（调试用） """
        print("Symbol table:", file=Outfh)
        for i, scope in enumerate(self.sym_stack):
            print(f"Scope {i}:", file=Outfh)
            for name, sym in scope.items():
                from typs import get_typename
                typestr = get_typename(sym.type)
                print(f"  {name}: type={typestr}, kind={sym.sym_type}", file=Outfh)


# 创建符号处理器实例并导出函数
sym_processor = SymProcessor()
set_cur_func = sym_processor.set_cur_func
add_symbol = sym_processor.add_symbol
find_symbol = sym_processor.find_symbol
gen_glob_syms = sym_processor.gen_glob_syms
dump_syms = sym_processor.dump_syms
