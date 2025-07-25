from io import StringIO
from typing import List

from defs import DataType, TypeKind, Sym, Litval, ASTNodeType, fatal, quote_string
from strlits import strlit_processor


class CodeGenerator:
    qbe_type_names = [
        "", "w", "w", "w", "w", "l", "s", "d"
    ]
    qbe_store_type_names = [
        "", "b", "b", "h", "w", "l", "s", "d"
    ]
    qbe_load_type_names = [
        "", "sb", "sb", "sh", "sw", "l", "s", "d",
        "", "ub", "ub", "uh", "uw", "l", "s", "d"
    ]
    qbe_ext_type_names = [
        "", "sw", "sw", "sw", "sw", "sl", "s", "d",
        "", "uw", "uw", "uw", "uw", "ul", "s", "d"
    ]
    arithmetic_ops = {
        ASTNodeType.A_ADD: "add", ASTNodeType.A_SUBTRACT: "sub",
        ASTNodeType.A_MULTIPLY: "mul", ASTNodeType.A_DIVIDE: "div",
    }
    logical_ops = {
        ASTNodeType.A_AND: "and", ASTNodeType.A_OR: "or", ASTNodeType.A_XOR: "xor",
        ASTNodeType.A_LSHIFT: "shl", ASTNodeType.A_RSHIFT: "shr",
    }
    comparison_ops = {
        ASTNodeType.A_EQ: "eq", ASTNodeType.A_NE: "ne",
        ASTNodeType.A_LE: "le", ASTNodeType.A_LT: "lt",
        ASTNodeType.A_GE: "ge", ASTNodeType.A_GT: "gt",
    }

    def __init__(self):
        self.output = StringIO()
        self.next_temp = 1
        self.label_id = 1

    @staticmethod
    def check_type(val_type: DataType):
        if val_type.kind.value > TypeKind.TY_FLT64.value:
            fatal("not a built-in type")
        if val_type.kind == TypeKind.TY_VOID:
            fatal("no QBE void type")

    def qbe_type(self, val_type: DataType) -> str:
        self.check_type(val_type)
        return self.qbe_type_names[val_type.kind.value]

    def qbe_store_type(self, val_type: DataType) -> str:
        self.check_type(val_type)
        return self.qbe_store_type_names[val_type.kind.value]

    def qbe_load_type(self, val_type: DataType) -> str:
        self.check_type(val_type)
        idx = val_type.kind.value
        if val_type.is_unsigned:
            idx += TypeKind.TY_FLT64.value + 1
        return self.qbe_load_type_names[idx]

    def qbe_ext_type(self, val_type: DataType) -> str:
        self.check_type(val_type)
        idx = val_type.kind.value
        if val_type.is_unsigned:
            idx += TypeKind.TY_FLT64.value + 1
        return self.qbe_ext_type_names[idx]

    def gen_temp(self) -> int:
        self.next_temp += 1
        return self.next_temp

    def gen_label(self) -> int:
        self.label_id += 1
        return self.label_id

    def write_all(self, out) -> None:
        out.write(self.output.getvalue())

    def cg_file_preamble(self) -> None:
        pass

    def cg_file_postamble(self) -> None:
        for strlit in strlit_processor:
            self.cg_strlit(strlit)

    def cg_func_preamble(self, fn_sym: Sym) -> None:
        print(f"export function ${fn_sym.name}(", end="", file=self.output)
        for i, param in enumerate(fn_sym.params):
            if i > 0:
                print(", ", end="", file=self.output)
            if param.type.kind == TypeKind.TY_VOID:
                break
            qtype = self.qbe_type(param.type)
            print(f"{qtype} %{param.name}", end="", file=self.output)
        print(") {", file=self.output)
        print("@START", file=self.output)

    def cg_func_postamble(self) -> None:
        print("@END", file=self.output)
        print("  ret", file=self.output)
        print("}", file=self.output)

    def cg_label(self, l: int) -> None:
        print(f"@L{l}", file=self.output)

    def cg_strlit(self, strlit) -> None:
        # 转义特殊字符
        # escaped = strlit.val.replace('\a', '\\a').replace('\b', '\\b')
        # escaped = escaped.replace('\f', '\\f').replace('\n', '\\n')
        # escaped = escaped.replace('\r', '\\r').replace('\t', '\\t').replace('\v', '\\v')
        # escaped = escaped.replace('\\', '\\\\').replace('"', '\\"')
        # print(f"data $L{label} = {{ b \"{escaped}\", b 0 }}", file=self.output)
        label, value = strlit.label, quote_string(strlit.val)
        print(f"data $L{label} = {{ b \"{value}\", b 0 }}", file=self.output)

    def cg_ret(self, node=None):
        if node:
            print(f"  ret {node}", file=self.output)
        else:
            print(f"  ret", file=self.output)

    def cg_jump(self, l: int) -> None:
        print(f"  jmp @L{l}", file=self.output)

    def cg_glob_sym(self, s: Sym) -> None:
        if not s:
            return
        qtype = self.qbe_store_type(s.type)
        if s.type.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            prefix, value = qtype + "_", s.init_val.dblval
        else:
            prefix, value = "", s.init_val.intval
        print(f"export data ${s.name} = {{ {qtype} {prefix}{value}, }}", file=self.output)

    def cg_print(self, label: int, temp: int, val_type: DataType) -> None:
        qtype = self.qbe_type(val_type)
        print(f"  call $printf(l $L{label}, {qtype} %.t{temp})", file=self.output)

    def cg_load_lit(self, value: Litval, val_type: DataType) -> int:
        t = self.gen_temp()
        qtype = self.qbe_type(val_type)
        if val_type.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            print(f"  %.t{t} ={qtype} copy {qtype}_{value.dblval}", file=self.output)
        else:
            print(f"  %.t{t} ={qtype} copy {value.intval}", file=self.output)
        return t

    def cg_negate(self, t: int, val_type: DataType) -> int:
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} neg %.t{t}", file=self.output)
        return t_new

    def cg_not(self, t: int, val_type: DataType) -> int:
        t_new = self.gen_temp()
        print(f"  %.t{t_new} =w not %.t{t}", file=self.output)
        return t_new

    def cg_invert(self, t: int, val_type: DataType) -> int:
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} inv %.t{t}", file=self.output)
        return t_new

    def cg_arithmetic(self, op: ASTNodeType, t1: int, t2: int, val_type: DataType) -> int:
        op = self.arithmetic_ops.get(op)
        if not op:
            fatal(f"Unknown arithmetic operator {op}")
        if op == "div" and val_type.is_unsigned:
            op = "divu"
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} =w {op} {qtype} %.t{t1}, %.t{t2}", file=self.output)
        return t_new

    def cg_logical(self, op: ASTNodeType, t1: int, t2: int, val_type: DataType) -> int:
        op = self.logical_ops.get(op)
        if not op:
            fatal(f"Unknown logical operator {op}")
        if op == "shr" and val_type.is_unsigned:
            op = "shru"
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} =w {op} {qtype} %.t{t1}, %.t{t2}", file=self.output)
        return t_new

    def cg_comparison(self, op: ASTNodeType, t1: int, t2: int, val_type: DataType) -> int:
        op = self.comparison_ops.get(op)
        if not op:
            fatal(f"Unknown comparison operator {op}")
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} =w {op} {qtype} %.t{t1}, %.t{t2}", file=self.output)
        return t_new

    def cg_if_false(self, t1: int, label: int) -> None:
        print(f"  jz %.t{t1}, @L{label}", file=self.output)

    def cg_add_local(self, val_type: DataType, sym: Sym) -> None:
        qtype = self.qbe_store_type(val_type)
        print(f"  var {qtype} {sym.name}", file=self.output)

    def cg_load_var(self, sym: Sym) -> int:
        # if sym.type.kind == TypeKind.TY_VOID:
        #     return 0
        t = self.gen_temp()
        qtype = self.qbe_load_type(sym.type)
        print(f"  %.t{t} ={qtype} load ${sym.name}", file=self.output)
        return t

    def cg_stor_var(self, t: int, exprtype: DataType, sym: Sym) -> None:
        qtype = self.qbe_store_type(sym.type)
        print(f"  store {qtype} %.t{t}, ${sym.name}", file=self.output)

    def cg_cast(self, t: int, val_type: DataType, newtype: DataType) -> int:
        t_new = self.gen_temp()
        if val_type.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            if newtype.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
                qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={qtype} copy %.t{t}", file=self.output)
            else:
                qtype = self.qbe_type(val_type)
                new_qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={new_qtype} trunc {qtype} %.t{t}", file=self.output)
        else:
            if newtype.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
                qtype = self.qbe_type(val_type)
                new_qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={new_qtype} extend {qtype} %.t{t}", file=self.output)
            else:
                qtype = self.qbe_ext_type(val_type)
                new_qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={new_qtype} {qtype} %.t{t}", file=self.output)
        return t_new

    def cg_call(self, sym: Sym, numargs: int, arglist: List[int], typelist: List[DataType]) -> int:
        t = self.gen_temp()
        args = []
        for i in range(numargs):
            qtype = self.qbe_type(typelist[i])
            args.append(f"{qtype} %.t{arglist[i]}")
        args_str = ", ".join(args)
        print(f"  %.t{t} =l call ${sym.name}({args_str})", file=self.output)
        return t


codegen = CodeGenerator()
gen_label = codegen.gen_label
gen_temp = codegen.gen_temp
cg_glob_sym = codegen.cg_glob_sym
cg_negate = codegen.cg_negate
cg_not = codegen.cg_not
cg_invert = codegen.cg_invert
# cg_arithmetic = codegen.cg_arithmetic
# cg_logical = codegen.cg_logical
# cg_comparison = codegen.cg_comparison
# cg_label = codegen.cg_label
# cg_str_lit = codegen.cg_strlit
# cg_ret = codegen.cg_ret
# cg_jump = codegen.cg_jump
# cg_if_false = codegen.cg_if_false
# cg_print = codegen.cg_print
# cg_load_lit = codegen.cg_load_lit
# cg_load_var = codegen.cg_load_var
# cg_stor_var = codegen.cg_stor_var
# cg_cast = codegen.cg_cast
# cg_add_local = codegen.cg_add_local
# cg_call = codegen.cg_call
