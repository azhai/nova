from io import StringIO
from typing import List

from defs import ASTNode, Symbol, NodeType, ValType, fatal
from strlits import strlit_processor


class CodeGenerator:
    type_indexes = {
        "VOID": 0, "BOOL": 1, "INT8": 2, "INT16": 3,
        "INT32": 4, "INT64": 5, "FLOAT32": 6, "FLOAT64": 7,
        "UINT8": 10, "UINT16": 11, "UINT32": 12, "UINT64": 13,
    }
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
        NodeType.A_ADD: "add", NodeType.A_SUB: "sub",
        NodeType.A_MUL: "mul", NodeType.A_DIV: "div",
    }
    logical_ops = {
        NodeType.A_AND: "and", NodeType.A_OR: "or", NodeType.A_XOR: "xor",
        NodeType.A_LSHIFT: "shl", NodeType.A_RSHIFT: "shr",
    }
    comparison_ops = {
        NodeType.A_EQ: "eq", NodeType.A_NE: "ne",
        NodeType.A_LE: "le", NodeType.A_LT: "lt",
        NodeType.A_GE: "ge", NodeType.A_GT: "gt",
    }

    def __init__(self):
        self.output = StringIO()
        self.next_temp = 1
        self.label_id = 1

    def check_type(self, val_type: ValType, unsigned = False) -> int:
        idx = self.type_indexes.get(val_type.name, -1)
        if idx < 0:
            fatal("not a built-in type")
        elif idx == 0:
            fatal("no QBE void type")
        elif not unsigned and idx >= 8:
            fatal("not support unsigned type")
        return idx

    def qbe_type(self, val_type: ValType) -> str:
        idx = self.check_type(val_type)
        return self.qbe_type_names[idx]

    def qbe_store_type(self, val_type: ValType) -> str:
        idx = self.check_type(val_type)
        return self.qbe_store_type_names[idx]

    def qbe_load_type(self, val_type: ValType) -> str:
        idx = self.check_type(val_type, True)
        return self.qbe_load_type_names[idx]

    def qbe_ext_type(self, val_type: ValType) -> str:
        idx = self.check_type(val_type, True)
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

    def cg_func_preamble(self, fn_sym: Symbol) -> None:
        print(f"export function ${fn_sym.name}(", end="", file=self.output)
        for i, param in enumerate(fn_sym.params):
            if i > 0:
                print(", ", end="", file=self.output)
            if param.val_type == ValType.VOID:
                break
            qtype = self.qbe_type(param.val_type)
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

        #label, value = strlit.label, quote_string(strlit.val)
        label, value = strlit.label, strlit.val
        print(f"data $L{label} = {{ b {value}, b 0 }}", file=self.output)

    def cg_ret(self, node=None):
        if node:
            print(f"  ret {node}", file=self.output)
        else:
            print(f"  ret", file=self.output)

    def cg_jump(self, l: int) -> None:
        print(f"  jmp @L{l}", file=self.output)

    def cg_glob_sym(self, sym: Symbol) -> None:
        if not sym:
            return
        qtype = self.qbe_store_type(sym.val_type)
        if sym.val_type.is_float():
            prefix, value = qtype + "_", sym.init_val
        else:
            prefix, value = "", sym.init_val
        print(f"export data ${sym.name} = {{ {qtype} {prefix}{value}, }}", file=self.output)

    def cg_print(self, label: int, temp: int, val_type: ValType) -> None:
        qtype = self.qbe_type(val_type)
        print(f"  call $printf(l $L{label}, {qtype} %.t{temp})", file=self.output)

    def cg_load_lit(self, node: ASTNode) -> int:
        t = self.gen_temp()
        qtype = self.qbe_type(node.val_type)
        if node.val_type.is_float():
            print(f"  %.t{t} ={qtype} copy {qtype}_{node.number}", file=self.output)
        else:
            print(f"  %.t{t} ={qtype} copy {node.number}", file=self.output)
        return t

    def cg_negate(self, t: int, val_type: ValType) -> int:
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} neg %.t{t}", file=self.output)
        return t_new

    def cg_not(self, t: int, val_type: ValType) -> int:
        t_new = self.gen_temp()
        print(f"  %.t{t_new} =w not %.t{t}", file=self.output)
        return t_new

    def cg_invert(self, t: int, val_type: ValType) -> int:
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} inv %.t{t}", file=self.output)
        return t_new

    def cg_arithmetic(self, op: NodeType, t1: int, t2: int, val_type: ValType) -> int:
        op = self.arithmetic_ops.get(op)
        if not op:
            fatal(f"Unknown arithmetic operator {op}")
        if op == "div" and val_type.is_unsigned:
            op = "divu"
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} =w {op} {qtype} %.t{t1}, %.t{t2}", file=self.output)
        return t_new

    def cg_logical(self, op: NodeType, t1: int, t2: int, val_type: ValType) -> int:
        op = self.logical_ops.get(op)
        if not op:
            fatal(f"Unknown logical operator {op}")
        if op == "shr" and val_type.is_unsigned:
            op = "shru"
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} =w {op} {qtype} %.t{t1}, %.t{t2}", file=self.output)
        return t_new

    def cg_comparison(self, op: NodeType, t1: int, t2: int, val_type: ValType) -> int:
        op = self.comparison_ops.get(op)
        if not op:
            fatal(f"Unknown comparison operator {op}")
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} =w {op} {qtype} %.t{t1}, %.t{t2}", file=self.output)
        return t_new

    def cg_if_false(self, t1: int, label: int) -> None:
        print(f"  jz %.t{t1}, @L{label}", file=self.output)

    def cg_add_local(self, val_type: ValType, sym: Symbol) -> None:
        qtype = self.qbe_store_type(val_type)
        print(f"  var {qtype} {sym.name}", file=self.output)

    def cg_load_var(self, sym: Symbol) -> int:
        # if sym.val_type.kind == TypeKind.K_VOID:
        #     return 0
        t = self.gen_temp()
        qtype = self.qbe_load_type(sym.val_type)
        print(f"  %.t{t} ={qtype} load ${sym.name}", file=self.output)
        return t

    def cg_stor_var(self, t: int, exprtype: ValType, sym: Symbol) -> None:
        qtype = self.qbe_store_type(sym.val_type)
        print(f"  store {qtype} %.t{t}, ${sym.name}", file=self.output)

    def cg_cast(self, t: int, val_type: ValType, newtype: ValType) -> int:
        t_new = self.gen_temp()
        if val_type.is_float():
            if newtype.is_float():
                qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={qtype} copy %.t{t}", file=self.output)
            else:
                qtype = self.qbe_type(val_type)
                new_qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={new_qtype} trunc {qtype} %.t{t}", file=self.output)
        else:
            if newtype.is_float():
                qtype = self.qbe_type(val_type)
                new_qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={new_qtype} extend {qtype} %.t{t}", file=self.output)
            else:
                qtype = self.qbe_ext_type(val_type)
                new_qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={new_qtype} {qtype} %.t{t}", file=self.output)
        return t_new

    def cg_call(self, sym: Symbol, numargs: int, arglist: List[int], typelist: List[ValType]) -> int:
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
