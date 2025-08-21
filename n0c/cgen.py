import sys
from io import StringIO
from typing import List

from utils import fatal
from defs import Symbol, NodeType, ASTNode, ValType

str_literal_labels = {}

def get_str_lit_label(value: str) -> int:
    """ 固定字符串的标号，从1即L1开始 """
    label = str_literal_labels.get(value, 0)
    if label <= 0:
        label = len(str_literal_labels) + 1
        str_literal_labels[value] = label
    return label


class CodeGenerator:
    type_indexes = {
        "VOID": 0, "BOOL": 1, "INT8": 2, "INT16": 3,
        "INT32": 4, "INT64": 5, "FLOAT32": 6, "FLOAT64": 7,
        "UINT8": 10, "UINT16": 11, "UINT32": 12, "UINT64": 13,
        "STR": 5,
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
        NodeType.A_LE: "sle", NodeType.A_LT: "slt",
        NodeType.A_GE: "sge", NodeType.A_GT: "sgt",
    }

    def __init__(self):
        self.output = StringIO() # 字符串缓冲区
        self.next_temp = 1 # 变量标号，从%.t1开始
        self.label_id = 1  # 字符串标号，从L1开始

    def check_type(self, val_type: ValType, unsigned = False) -> int:
        idx = self.type_indexes.get(val_type.name, -1)
        if idx < 0:
            fatal("not a built-in type")
        elif idx == 0:
            fatal("no QBE void type")
        elif not unsigned and idx >= 8:
            idx -= 8
        return idx

    def qbe_type(self, val_type: ValType) -> str:
        idx = self.check_type(val_type, False)
        return self.qbe_type_names[idx]

    def qbe_store_type(self, val_type: ValType) -> str:
        idx = self.check_type(val_type, False)
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
        if not out:
            out = sys.stdout
        out.write(self.output.getvalue())

    def cg_file_preamble(self) -> None:
        pass

    def cg_file_postamble(self) -> None:
        for value, label in str_literal_labels.items():
            self.cg_str_lit(value, label)

    def cg_func_preamble(self, name: str, params: str = "") -> None:
        print(f"export function ${name}({params})", end="", file=self.output)
        print(" {\n@START", file=self.output)

    def cg_func_postamble(self) -> None:
        print("@END\n  ret\n}", file=self.output)

    def cg_print(self, label: int, temp: int, val_type: ValType) -> None:
        qtype = self.qbe_type(val_type)
        print(f"  call $printf(l $L{label}, {qtype} %.t{temp})", file=self.output)

    def cg_label(self, l: int) -> None:
        print(f"@L{l}", file=self.output)

    def cg_str_lit(self, value, label) -> None:
        # 转义特殊字符
        # value = quote_string(value)
        print(f"data $L{label} = {{ b {value}, b 0 }}", file=self.output)

    def cg_load_lit(self, value, val_type: ValType) -> int:
        t = self.gen_temp()
        qtype = self.qbe_type(val_type)
        if val_type.is_float():
            print(f"  %.t{t} ={qtype} copy {qtype}_{value}", file=self.output)
        else:
            print(f"  %.t{t} ={qtype} copy {value}", file=self.output)
        return t

    def cg_load_var(self, sym: Symbol) -> int:
        t_new = self.gen_temp()
        qtype = self.qbe_type(sym.val_type)
        if sym.has_addr:
            load_qtype = self.qbe_load_type(sym.val_type)
            print(f"  %.t{t_new} ={qtype} load{load_qtype} %{sym.name}", file=self.output)
        else:
            print(f"  %.t{t_new} ={qtype} copy %{sym.name}", file=self.output)
        return t_new

    def cg_stor_var(self, t: int, val_type: ValType, sym: Symbol) -> None:
        qtype = self.qbe_store_type(val_type)
        if sym.has_addr:
            print(f"  store{qtype} %.t{t}, %{sym.name}", file=self.output)
        else:
            print(f"  %{sym.name} ={qtype} copy %.t{t}", file=self.output)

    def cg_add_local(self, val_type: ValType, sym: Symbol) -> None:
        size = 4
        if val_type in (ValType.INT64, ValType.UINT64, ValType.FLOAT64):
            size = 8
        print(f"  %{sym.name} =l alloc{size} 1", file=self.output)

    def cg_align(self, val_type: ValType, offset: int = 0) -> int:
        # Structs: use the type of the first member
        if val_type == ValType.OBJ:
            pass
        if val_type in (ValType.VOID, ValType.OBJ, ValType.CUSTOM):
            fatal(f"No QBE size for type kind {val_type.name}")
        if val_type in (ValType.BOOL, ValType.INT8, ValType.UINT8):
            return offset
        if val_type == ValType.REF:
            alignment = 8
        else:
            alignment = max(1, val_type.bytes())
        return (offset + (alignment - 1)) & ~(alignment - 1)

    def cg_jump(self, l: int) -> None:
        print(f"  jmp @L{l}", file=self.output)

    def cg_abort(self):
        print(f"  jmp @END", file=self.output)
        self.cg_label(self.gen_label())

    def cg_return(self, t, val_type: ValType):
        if val_type != ValType.VOID:
            qtype = self.qbe_type(val_type)
            print(f"  %.ret ={qtype} copy %.t{t}", file=self.output)
        self.cg_abort()

    def cg_if_false(self, t1: int, label: int) -> None:
        new_label = self.gen_label()
        print(f"  jnz %.t{t1}, @L{new_label}, @L{label}", file=self.output)
        self.cg_label(new_label)

    def cg_negate(self, t: int, val_type: ValType) -> int:
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t} ={qtype} sub 0, %.t{t}", file=self.output)
        return t

    def cg_not(self, t: int, val_type: ValType) -> int:
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t} ={qtype} ceq{qtype} %.t{t}, 0", file=self.output)
        return t

    def cg_invert(self, t: int, val_type: ValType) -> int:
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t} ={qtype} xor %.t{t}, -1", file=self.output)
        return t

    def cg_arithmetic(self, op: NodeType, t1: int, t2: int, val_type: ValType) -> int:
        op = self.arithmetic_ops.get(op)
        if not op:
            fatal(f"Unknown arithmetic operator {op}")
        if op == "div" and val_type.is_unsigned:
            op = "divu"
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t1} ={qtype} {op} %.t{t1}, %.t{t2}", file=self.output)
        return t1

    def cg_logical(self, op: NodeType, t1: int, t2: int, val_type: ValType) -> int:
        op = self.logical_ops.get(op)
        if not op:
            fatal(f"Unknown logical operator {op}")
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t1} ={qtype} {op} %.t{t1}, %.t{t2}", file=self.output)
        return t1

    def cg_comparison(self, op: NodeType, t1: int, t2: int, val_type: ValType) -> int:
        op = self.comparison_ops.get(op)
        if not op:
            fatal(f"Unknown comparison operator {op}")
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} =w c{op}{qtype} %.t{t1}, %.t{t2}", file=self.output)
        return t_new

    def cg_cast(self, t: int, val_type: ValType, new_type: ValType) -> int:
        t_new = self.gen_temp()
        ext_qtype = self.qbe_ext_type(val_type)
        new_qtype = self.qbe_type(new_type)
        if new_type.is_float() and (val_type.is_integer() or val_type.is_unsigned()):
            print(f"  %.t{t_new} ={new_qtype} {ext_qtype}tof %.t{t}", file=self.output)
            return t_new

        bs1, bs2 = val_type.bytes(), new_type.bytes()
        # Widening
        if bs2 > bs1:
            if val_type in (ValType.INT32, ValType.UINT32, ValType.FLOAT32):
                print(f"  %.t{t_new} ={new_qtype} ext{ext_qtype} %.t{t}", file=self.output)
                return t_new
            else:
                fatal(f"Not sure how to widen from {val_type} to {new_type}")
        # Narrowing
        if bs2 < bs1:
            if val_type in (ValType.INT32, ValType.UINT32):
                return t
            else:
                fatal(f"Not sure how to narrow from {val_type} to {new_type}")
        return t

    def cg_call(self, sym: Symbol, params: str = "") -> int:
        if sym.val_type == ValType.VOID:
            t, ret = 0, ""
        else:
            t = self.gen_temp()
            qtype = self.qbe_type(sym.val_type)
            ret = f"%.t{t} ={qtype} "
        print(f"  {ret}call ${sym.name}({params})", file=self.output)
        return t

    def cg_glob_sym(self, sym: Symbol) -> None:
        if not sym:
            return
        qtype = self.qbe_store_type(sym.val_type)
        if sym.val_type.is_float():
            prefix, value = qtype + "_", sym.init_val
        else:
            prefix, value = "", sym.init_val
        print(f"export data ${sym.name} = {{ {qtype} {prefix}{value}, }}", file=self.output)


codegen = CodeGenerator()
cg_glob_sym = codegen.cg_glob_sym
