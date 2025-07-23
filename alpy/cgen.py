from typing import List
from defs import DataType, TypeKind, Sym, Litval, OutFile, fatal, ASTNodeType


class CodeGenerator:
    def __init__(self):
        self.next_temp = 1
        self.label_id = 1
        self.qbe_type_names = [
            "", "w", "w", "w", "w", "l", "s", "d"
        ]
        self.qbe_store_type_names = [
            "", "b", "b", "h", "w", "l", "s", "d"
        ]
        self.qbe_load_type_names = [
            "", "sb", "sb", "sh", "sw", "l", "s", "d",
            "", "ub", "ub", "uh", "uw", "l", "s", "d"
        ]
        self.qbe_ext_type_names = [
            "", "sw", "sw", "sw", "sw", "sl", "s", "d",
            "", "uw", "uw", "uw", "uw", "ul", "s", "d"
        ]

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

    def cg_file_preamble(self) -> None:
        pass

    def cg_file_postamble(self) -> None:
        pass

    def cg_func_preamble(self, fn_sym: Sym) -> None:
        print(f"export function ${fn_sym.name}(", end="", file=OutFile)
        for i, param in enumerate(fn_sym.params):
            if i > 0:
                print(", ", end="", file=OutFile)
            # if param.type.kind == TypeKind.TY_VOID:
            #     break
            qtype = self.qbe_type(param.type)
            print(f"{qtype} %{param.name}", end="", file=OutFile)
        print(") {", file=OutFile)
        print("@START", file=OutFile)

    def cg_func_postamble(self) -> None:
        print("@END", file=OutFile)
        print("  ret", file=OutFile)
        print("}", file=OutFile)

    def cgalloctemp(self) -> int:
        self.next_temp += 1
        return self.next_temp

    def cglabel(self, l: int) -> None:
        print(f"@L{l}", file=OutFile)

    def cgstrlit(self, label: int, val: str) -> None:
        escaped = val.replace('\a', '\\a').replace('\b', '\\b')
        escaped = escaped.replace('\f', '\\f').replace('\n', '\\n')
        escaped = escaped.replace('\r', '\\r').replace('\t', '\\t').replace('\v', '\\v')
        print(f"data $L{label} = {{ b \"{escaped}\", b 0 }}", file=OutFile)

    def cgjump(self, l: int) -> None:
        print(f"  jmp @L{l}", file=OutFile)

    def cgglobsym(self, s: Sym) -> None:
        if not s:
            return
        qtype = self.qbe_store_type(s.type)
        if s.type.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            print(f"export data ${s.name} = {{ {qtype} {qtype}_{s.init_val.dblval}, }}", file=OutFile)
        else:
            print(f"export data ${s.name} = {{ {qtype} {s.init_val.intval}, }}", file=OutFile)

    def cgprint(self, label: int, temp: int, val_type: DataType) -> None:
        qtype = self.qbe_type(val_type)
        print(f"  call $printf(l $L{label}, {qtype} %.t{temp})", file=OutFile)

    def cgloadlit(self, value: Litval, val_type: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        if val_type.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            print(f"  %.t{t} ={qtype} copy {qtype}_{value.dblval}", file=OutFile)
        else:
            print(f"  %.t{t} ={qtype} copy {value.intval}", file=OutFile)
        return t

    def cgadd(self, t1: int, t2: int, val_type: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t} ={qtype} add %.t{t1}, %.t{t2}", file=OutFile)
        return t

    def cgsub(self, t1: int, t2: int, val_type: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t} ={qtype} sub %.t{t1}, %.t{t2}", file=OutFile)
        return t

    def cgmul(self, t1: int, t2: int, val_type: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t} ={qtype} mul %.t{t1}, %.t{t2}", file=OutFile)
        return t

    def cgdiv(self, t1: int, t2: int, val_type: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        if val_type.is_unsigned:
            print(f"  %.t{t} ={qtype} divu %.t{t1}, %.t{t2}", file=OutFile)
        else:
            print(f"  %.t{t} ={qtype} div %.t{t1}, %.t{t2}", file=OutFile)
        return t

    def cgnegate(self, t: int, val_type: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} neg %.t{t}", file=OutFile)
        return t_new

    def cgcompare(self, op: ASTNodeType, t1: int, t2: int, val_type: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        op_map = {
            ASTNodeType.A_EQ: "eq",
            ASTNodeType.A_NE: "ne",
            ASTNodeType.A_LT: "lt",
            ASTNodeType.A_GT: "gt",
            ASTNodeType.A_LE: "le",
            ASTNodeType.A_GE: "ge"
        }
        if op not in op_map:
            fatal(f"Unknown comparison operator {op}")
        print(f"  %.t{t} =w {op_map[op]} {qtype} %.t{t1}, %.t{t2}", file=OutFile)
        return t

    def cgjump_if_false(self, t1: int, label: int) -> None:
        print(f"  jz %.t{t1}, @L{label}", file=OutFile)

    def cgnot(self, t: int, val_type: DataType) -> int:
        t_new = self.cgalloctemp()
        print(f"  %.t{t_new} =w not %.t{t}", file=OutFile)
        return t_new

    def cginvert(self, t: int, val_type: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} inv %.t{t}", file=OutFile)
        return t_new

    def cgand(self, t1: int, t2: int, val_type: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} and %.t{t1}, %.t{t2}", file=OutFile)
        return t_new

    def cgor(self, t1: int, t2: int, val_type: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} or %.t{t1}, %.t{t2}", file=OutFile)
        return t_new

    def cgxor(self, t1: int, t2: int, val_type: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} xor %.t{t1}, %.t{t2}", file=OutFile)
        return t_new

    def cgshl(self, t1: int, t2: int, val_type: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        print(f"  %.t{t_new} ={qtype} shl %.t{t1}, %.t{t2}", file=OutFile)
        return t_new

    def cgshr(self, t1: int, t2: int, val_type: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbe_type(val_type)
        if val_type.is_unsigned:
            print(f"  %.t{t_new} ={qtype} shru %.t{t1}, %.t{t2}", file=OutFile)
        else:
            print(f"  %.t{t_new} ={qtype} shr %.t{t1}, %.t{t2}", file=OutFile)
        return t_new

    def cgloadvar(self, sym: Sym) -> int:
        # if sym.type.kind == TypeKind.TY_VOID:
        #     return 0
        t = self.cgalloctemp()
        qtype = self.qbe_load_type(sym.type)
        print(f"  %.t{t} ={qtype} load ${sym.name}", file=OutFile)
        return t

    def cgstorvar(self, t: int, exprtype: DataType, sym: Sym) -> None:
        qtype = self.qbe_store_type(sym.type)
        print(f"  store {qtype} %.t{t}, ${sym.name}", file=OutFile)

    def cgcast(self, t: int, val_type: DataType, newtype: DataType) -> int:
        t_new = self.cgalloctemp()
        if val_type.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            if newtype.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
                qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={qtype} copy %.t{t}", file=OutFile)
            else:
                qtype = self.qbe_type(val_type)
                new_qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={new_qtype} trunc {qtype} %.t{t}", file=OutFile)
        else:
            if newtype.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
                qtype = self.qbe_type(val_type)
                new_qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={new_qtype} extend {qtype} %.t{t}", file=OutFile)
            else:
                qtype = self.qbe_ext_type(val_type)
                new_qtype = self.qbe_type(newtype)
                print(f"  %.t{t_new} ={new_qtype} {qtype} %.t{t}", file=OutFile)
        return t_new

    def cgaddlocal(self, val_type: DataType, sym: Sym) -> None:
        qtype = self.qbe_store_type(val_type)
        print(f"  var {qtype} {sym.name}", file=OutFile)

    def cgcall(self, sym: Sym, numargs: int, arglist: List[int], typelist: List[DataType]) -> int:
        t = self.cgalloctemp()
        args = []
        for i in range(numargs):
            qtype = self.qbe_type(typelist[i])
            args.append(f"{qtype} %.t{arglist[i]}")
        args_str = ", ".join(args)
        print(f"  %.t{t} =l call ${sym.name}({args_str})", file=OutFile)
        return t

    def genlabel(self) -> int:
        self.label_id += 1
        return self.label_id


codegen = CodeGenerator()
cgalloctemp = codegen.cgalloctemp
cglabel = codegen.cglabel
cgstrlit = codegen.cgstrlit
cgjump = codegen.cgjump
qbetype = codegen.qbe_type
qbe_storetype = codegen.qbe_store_type
qbe_loadtype = codegen.qbe_load_type
qbe_exttype = codegen.qbe_ext_type
cg_file_preamble = codegen.cg_file_preamble
cg_file_postamble = codegen.cg_file_postamble
cg_func_preamble = codegen.cg_func_preamble
cg_func_postamble = codegen.cg_func_postamble
cgglobsym = codegen.cgglobsym
cgprint = codegen.cgprint
cgloadlit = codegen.cgloadlit
cgadd = codegen.cgadd
cgsub = codegen.cgsub
cgmul = codegen.cgmul
cgdiv = codegen.cgdiv
cgnegate = codegen.cgnegate
cgcompare = codegen.cgcompare
cgjump_if_false = codegen.cgjump_if_false
cgnot = codegen.cgnot
cginvert = codegen.cginvert
cgand = codegen.cgand
cgor = codegen.cgor
cgxor = codegen.cgxor
cgshl = codegen.cgshl
cgshr = codegen.cgshr
cgloadvar = codegen.cgloadvar
cgstorvar = codegen.cgstorvar
cgcast = codegen.cgcast
cgaddlocal = codegen.cgaddlocal
cgcall = codegen.cgcall
genlabel = codegen.genlabel
