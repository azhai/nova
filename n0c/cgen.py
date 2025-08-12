import sys
from io import StringIO
from typing import List

from defs import Symbol, NodeType, ASTNode, ValType, fatal

str_literal_labels = {}

def get_str_lit_label(value: str) -> int:
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
        if not out:
            out = sys.stdout
        out.write(self.output.getvalue())

    def cg_file_preamble(self) -> None:
        pass

    def cg_file_postamble(self) -> None:
        for value, label in str_literal_labels.items():
            self.cg_str_lit(value, label)

    def cg_func_preamble(self, node: ASTNode) -> None:
        print(f"export function ${node.sym.name}(", end="", file=self.output)
        for i, param in enumerate(node.args):
            if i > 0:
                print(", ", end="", file=self.output)
            if param.val_type == ValType.VOID:
                break
            qtype = self.qbe_type(param.val_type)
            print(f"{qtype} %{param.name}", end="", file=self.output)
        print(") {\n@START", file=self.output)

    def cg_func_postamble(self) -> None:
        print("@END\n  ret\n}", file=self.output)

    def cg_label(self, l: int) -> None:
        print(f"@L{l}", file=self.output)

    def cg_str_lit(self, value, label) -> None:
        # 转义特殊字符
        # value = quote_string(value)
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

    def cg_load_lit(self, value, val_type: ValType) -> int:
        t = self.gen_temp()
        qtype = self.qbe_type(val_type)
        if val_type.is_float():
            print(f"  %.t{t} ={qtype} copy {qtype}_{value}", file=self.output)
        else:
            print(f"  %.t{t} ={qtype} copy {value}", file=self.output)
        return t

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
        if op == "shr" and val_type.is_unsigned:
            op = "shru"
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t1} ={qtype} {op} %.t{t1}, %.t{t2}", file=self.output)
        return t1

    def cg_comparison(self, op: NodeType, t1: int, t2: int, val_type: ValType) -> int:
        op = self.comparison_ops.get(op)
        if not op:
            fatal(f"Unknown comparison operator {op}")
        if val_type.is_unsigned:
            op = op.replace("s", "", 1)
        t_new = self.gen_temp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} =w c{op}{qtype} %.t{t1}, %.t{t2}", file=self.output)
        return t_new

    def cg_if_false(self, t1: int, label: int) -> None:
        print(f"  jz %.t{t1}, @L{label}", file=self.output)

    def cg_add_local(self, val_type: ValType, sym: Symbol) -> None:
        size = 4
        if val_type in (ValType.INT64, ValType.UINT64, ValType.FLOAT64):
            size = 8
        print(f"  %{sym.name} =l alloc{size} 1", file=self.output)

    def cg_load_var(self, sym: Symbol) -> int:
        # if sym.val_type.kind == TypeKind.K_VOID:
        #     return 0
        t_new = self.gen_temp()
        qtype = self.qbe_load_type(sym.val_type)
        print(f"  %.t{t_new} ={qtype} load ${sym.name}", file=self.output)
        return t_new

    def cg_stor_var(self, t: int, val_type: ValType, sym: Symbol) -> None:
        qtype = self.qbe_store_type(val_type)
        print(f"  store {qtype} %.t{t}, ${sym.name}", file=self.output)

    def cg_cast(self, t: int, val_type: ValType, new_type: ValType) -> int:
        t_new = self.gen_temp()
        if val_type.is_float():
            if new_type.is_float():
                qtype = self.qbe_type(new_type)
                print(f"  %.t{t_new} ={qtype} copy %.t{t}", file=self.output)
            else:
                qtype = self.qbe_type(val_type)
                new_qtype = self.qbe_type(new_type)
                print(f"  %.t{t_new} ={new_qtype} trunc {qtype} %.t{t}", file=self.output)
        else:
            if new_type.is_float():
                qtype = self.qbe_type(val_type)
                new_qtype = self.qbe_type(new_type)
                print(f"  %.t{t_new} ={new_qtype} extend {qtype} %.t{t}", file=self.output)
            else:
                qtype = self.qbe_ext_type(val_type)
                new_qtype = self.qbe_type(new_type)
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
cg_glob_sym = codegen.cg_glob_sym
