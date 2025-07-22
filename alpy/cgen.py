from typing import List

from defs import DataType, TypeKind, Sym, Litval, OutFile, fatal, ASTNodeType


class CodeGenerator:
    def __init__(self):
        self.nexttemp = 1
        self.labelid = 1
        self.qbe_typename = [
            "", "w", "w", "w", "w", "l", "s", "d"
        ]
        self.qbe_storetypename = [
            "", "b", "b", "h", "w", "l", "s", "d"
        ]
        self.qbe_loadtypename = [
            "", "sb", "sb", "sh", "sw", "l", "s", "d",
            "", "ub", "ub", "uh", "uw", "l", "s", "d"
        ]
        self.qbe_exttypename = [
            "", "sw", "sw", "sw", "sw", "sl", "s", "d",
            "", "uw", "uw", "uw", "uw", "ul", "s", "d"
        ]

    def cgalloctemp(self) -> int:
        self.nexttemp += 1
        return self.nexttemp

    def cglabel(self, l: int) -> None:
        print(f"@L{l}", file=OutFile)

    def cgstrlit(self, label: int, val: str) -> None:
        escaped = val.replace('\a', '\\a').replace('\b', '\\b')
        escaped = escaped.replace('\f', '\\f').replace('\n', '\\n')
        escaped = escaped.replace('\r', '\\r').replace('\t', '\\t').replace('\v', '\\v')
        print(f"data $L{label} = {{ b \"{escaped}\", b 0 }}", file=OutFile)

    def cgjump(self, l: int) -> None:
        print(f"  jmp @L{l}", file=OutFile)

    def qbetype(self, type_: DataType) -> str:
        if type_.kind.value > TypeKind.TY_FLT64.value:
            fatal("not a built-in type")
        if type_.kind == TypeKind.TY_VOID:
            fatal("no QBE void type")
        return self.qbe_typename[type_.kind.value]

    def qbe_storetype(self, type_: DataType) -> str:
        if type_.kind.value > TypeKind.TY_FLT64.value:
            fatal("not a built-in type")
        if type_.kind == TypeKind.TY_VOID:
            fatal("no QBE void type")
        return self.qbe_storetypename[type_.kind.value]

    def qbe_loadtype(self, type_: DataType) -> str:
        if type_.kind.value > TypeKind.TY_FLT64.value:
            fatal("not a built-in type")
        if type_.kind == TypeKind.TY_VOID:
            fatal("no QBE void type")
        idx = type_.kind.value
        if type_.is_unsigned:
            idx += TypeKind.TY_FLT64.value + 1
        return self.qbe_loadtypename[idx]

    def qbe_exttype(self, type_: DataType) -> str:
        if type_.kind.value > TypeKind.TY_FLT64.value:
            fatal("not a built-in type")
        if type_.kind == TypeKind.TY_VOID:
            fatal("no QBE void type")
        idx = type_.kind.value
        if type_.is_unsigned:
            idx += TypeKind.TY_FLT64.value + 1
        return self.qbe_exttypename[idx]

    def cg_file_preamble(self) -> None:
        pass

    def cg_file_postamble(self) -> None:
        pass

    def cg_func_preamble(self, func: Sym) -> None:
        print(f"export function ${func.name}(", end="", file=OutFile)
        param = func.memb
        while param:
            qtype = self.qbetype(param.type)
            print(f"{qtype} %{param.name}", end="", file=OutFile)
            param = param.next
            if param:
                print(", ", end="", file=OutFile)
        print(") {", file=OutFile)
        print("@START", file=OutFile)

    def cg_func_postamble(self) -> None:
        print("@END", file=OutFile)
        print("  ret", file=OutFile)
        print("}", file=OutFile)

    def cgglobsym(self, s: Sym) -> None:
        if not s:
            return
        qtype = self.qbe_storetype(s.type)
        if s.type.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            print(f"export data ${s.name} = {{ {qtype} {qtype}_{s.init_val.dblval}, }}", file=OutFile)
        else:
            print(f"export data ${s.name} = {{ {qtype} {s.init_val.intval}, }}", file=OutFile)

    def cgprint(self, label: int, temp: int, type_: DataType) -> None:
        qtype = self.qbetype(type_)
        print(f"  call $printf(l $L{label}, {qtype} %%.t{temp})", file=OutFile)

    def cgloadlit(self, value: Litval, type_: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbetype(type_)
        if type_.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            print(f"  %%.t{t} ={qtype} copy {qtype}_{value.dblval}", file=OutFile)
        else:
            print(f"  %%.t{t} ={qtype} copy {value.intval}", file=OutFile)
        return t

    def cgadd(self, t1: int, t2: int, type_: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbetype(type_)
        print(f"  %%.t{t} ={qtype} add %%.t{t1}, %%.t{t2}", file=OutFile)
        return t

    def cgsub(self, t1: int, t2: int, type_: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbetype(type_)
        print(f"  %%.t{t} ={qtype} sub %%.t{t1}, %%.t{t2}", file=OutFile)
        return t

    def cgmul(self, t1: int, t2: int, type_: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbetype(type_)
        print(f"  %%.t{t} ={qtype} mul %%.t{t1}, %%.t{t2}", file=OutFile)
        return t

    def cgdiv(self, t1: int, t2: int, type_: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbetype(type_)
        if type_.is_unsigned:
            print(f"  %%.t{t} ={qtype} divu %%.t{t1}, %%.t{t2}", file=OutFile)
        else:
            print(f"  %%.t{t} ={qtype} div %%.t{t1}, %%.t{t2}", file=OutFile)
        return t

    def cgnegate(self, t: int, type_: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbetype(type_)
        print(f"  %%.t{t_new} ={qtype} neg %%.t{t}", file=OutFile)
        return t_new

    def cgcompare(self, op: ASTNodeType, t1: int, t2: int, type_: DataType) -> int:
        t = self.cgalloctemp()
        qtype = self.qbetype(type_)
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
        print(f"  %%.t{t} =w {op_map[op]} {qtype} %%.t{t1}, %%.t{t2}", file=OutFile)
        return t

    def cgjump_if_false(self, t1: int, label: int) -> None:
        print(f"  jz %%.t{t1}, @L{label}", file=OutFile)

    def cgnot(self, t: int, type_: DataType) -> int:
        t_new = self.cgalloctemp()
        print(f"  %%.t{t_new} =w not %%.t{t}", file=OutFile)
        return t_new

    def cginvert(self, t: int, type_: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbetype(type_)
        print(f"  %%.t{t_new} ={qtype} inv %%.t{t}", file=OutFile)
        return t_new

    def cgand(self, t1: int, t2: int, type_: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbetype(type_)
        print(f"  %%.t{t_new} ={qtype} and %%.t{t1}, %%.t{t2}", file=OutFile)
        return t_new

    def cgor(self, t1: int, t2: int, type_: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbetype(type_)
        print(f"  %%.t{t_new} ={qtype} or %%.t{t1}, %%.t{t2}", file=OutFile)
        return t_new

    def cgxor(self, t1: int, t2: int, type_: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbetype(type_)
        print(f"  %%.t{t_new} ={qtype} xor %%.t{t1}, %%.t{t2}", file=OutFile)
        return t_new

    def cgshl(self, t1: int, t2: int, type_: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbetype(type_)
        print(f"  %%.t{t_new} ={qtype} shl %%.t{t1}, %%.t{t2}", file=OutFile)
        return t_new

    def cgshr(self, t1: int, t2: int, type_: DataType) -> int:
        t_new = self.cgalloctemp()
        qtype = self.qbetype(type_)
        if type_.is_unsigned:
            print(f"  %%.t{t_new} ={qtype} shru %%.t{t1}, %%.t{t2}", file=OutFile)
        else:
            print(f"  %%.t{t_new} ={qtype} shr %%.t{t1}, %%.t{t2}", file=OutFile)
        return t_new

    def cgloadvar(self, sym: Sym) -> int:
        t = self.cgalloctemp()
        qtype = self.qbe_loadtype(sym.type)
        print(f"  %%.t{t} ={qtype} load ${sym.name}", file=OutFile)
        return t

    def cgstorvar(self, t: int, exprtype: DataType, sym: Sym) -> None:
        qtype = self.qbe_storetype(sym.type)
        print(f"  store {qtype} %%.t{t}, ${sym.name}", file=OutFile)

    def cgcast(self, t: int, type_: DataType, newtype: DataType) -> int:
        t_new = self.cgalloctemp()
        if type_.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
            if newtype.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
                qtype = self.qbetype(newtype)
                print(f"  %%.t{t_new} ={qtype} copy %%.t{t}", file=OutFile)
            else:
                qtype = self.qbetype(type_)
                new_qtype = self.qbetype(newtype)
                print(f"  %%.t{t_new} ={new_qtype} trunc {qtype} %%.t{t}", file=OutFile)
        else:
            if newtype.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64):
                qtype = self.qbetype(type_)
                new_qtype = self.qbetype(newtype)
                print(f"  %%.t{t_new} ={new_qtype} extend {qtype} %%.t{t}", file=OutFile)
            else:
                qtype = self.qbe_exttype(type_)
                new_qtype = self.qbetype(newtype)
                print(f"  %%.t{t_new} ={new_qtype} {qtype} %%.t{t}", file=OutFile)
        return t_new

    def cgaddlocal(self, type_: DataType, sym: Sym) -> None:
        qtype = self.qbe_storetype(type_)
        print(f"  var {qtype} {sym.name}", file=OutFile)

    def cgcall(self, sym: Sym, numargs: int, arglist: List[int], typelist: List[DataType]) -> int:
        t = self.cgalloctemp()
        args = []
        for i in range(numargs):
            qtype = self.qbetype(typelist[i])
            args.append(f"{qtype} %%.t{arglist[i]}")
        args_str = ", ".join(args)
        print(f"  %%.t{t} =l call ${sym.name}({args_str})", file=OutFile)
        return t

    def genlabel(self) -> int:
        self.labelid += 1
        return self.labelid


codegen = CodeGenerator()
cgalloctemp = codegen.cgalloctemp
cglabel = codegen.cglabel
cgstrlit = codegen.cgstrlit
cgjump = codegen.cgjump
qbetype = codegen.qbetype
qbe_storetype = codegen.qbe_storetype
qbe_loadtype = codegen.qbe_loadtype
qbe_exttype = codegen.qbe_exttype
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
