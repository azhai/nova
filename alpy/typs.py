from typing import Optional, Dict

from defs import DataType, TypeKind, Litval, TokenType, fatal, ASTNodeType, SymType, ASTNode, cast_node


class TypeProcessor:
    _type_instances: Dict[tuple[TypeKind, bool], DataType] = {}
    _builtin_types_initialized = False

    @classmethod
    def init_builtin_types(cls) -> None:
        if cls._builtin_types_initialized:
            return

        # 创建所有内置类型实例
        builtin_kinds = [
            TypeKind.TY_VOID,
            TypeKind.TY_BOOL,
            TypeKind.TY_INT8,
            TypeKind.TY_INT16,
            TypeKind.TY_INT32,
            TypeKind.TY_INT64,
            TypeKind.TY_UINT8,
            TypeKind.TY_UINT16,
            TypeKind.TY_UINT32,
            TypeKind.TY_UINT64,
            TypeKind.TY_FLT32,
            TypeKind.TY_FLT64
        ]

        for kind in builtin_kinds:
            is_unsigned = kind in [
                TypeKind.TY_UINT8,
                TypeKind.TY_UINT16,
                TypeKind.TY_UINT32,
                TypeKind.TY_UINT64
            ]
            cls._type_instances[(kind, is_unsigned)] = DataType(kind, 0, 0, is_unsigned)

        cls._builtin_types_initialized = True

    @classmethod
    def get_type(cls, kind: TypeKind, is_unsigned: bool = False) -> DataType:
        if not cls._builtin_types_initialized:
            cls.init_builtin_types()
        key = (kind, is_unsigned)
        if key not in cls._type_instances:
            fatal(f"Unknown type: {kind} (unsigned: {is_unsigned})")
        return cls._type_instances[key]

    @staticmethod
    def new_type(kind: TypeKind, is_unsigned: bool = False) -> DataType:
        return DataType(kind=kind, is_unsigned=is_unsigned)

    @staticmethod
    def is_integer(type_: DataType) -> bool:
        return TypeKind.TY_INT8 <= type_.kind <= TypeKind.TY_UINT64

    @staticmethod
    def is_float(type_: DataType) -> bool:
        return type_.kind in (TypeKind.TY_FLT32, TypeKind.TY_FLT64)

    @classmethod
    def is_numeric(cls, type_: DataType) -> bool:
        return cls.is_integer(type_) or cls.is_float(type_)

    @staticmethod
    def get_typename(type_: DataType) -> str:
        if type_.kind == TypeKind.TY_VOID:
            return "void"
        if type_.kind == TypeKind.TY_BOOL:
            return "bool"
        if type_.kind == TypeKind.TY_INT8:
            return "int8"
        if type_.kind == TypeKind.TY_INT16:
            return "int16"
        if type_.kind == TypeKind.TY_INT32:
            return "int32"
        if type_.kind == TypeKind.TY_INT64:
            return "int64"
        if type_.kind == TypeKind.TY_UINT8:
            return "uint8"
        if type_.kind == TypeKind.TY_UINT16:
            return "uint16"
        if type_.kind == TypeKind.TY_UINT32:
            return "uint32"
        if type_.kind == TypeKind.TY_UINT64:
            return "uint64"
        if type_.kind == TypeKind.TY_FLT32:
            return "float32"
        if type_.kind == TypeKind.TY_FLT64:
            return "float64"
        return "unknown"

    @classmethod
    def add_type(cls, node: 'ASTNode') -> None:
        if not node:
            return

        # 递归处理子节点
        cls.add_type(node.left)
        cls.add_type(node.right)

        # 根据节点类型设置类型
        if node.op == ASTNodeType.A_NUMLIT:
            # 整数字面量，初始类型为int64
            node.type = cls.get_type(TypeKind.TY_INT64)
            # 拓宽到合适的类型
            cls.widen_expression(node)
        elif node.op == ASTNodeType.A_STRLIT:
            # 字符串字面量类型
            node.type = cls.get_type(TypeKind.TY_PTR)
        elif node.op == ASTNodeType.A_IDENT:
            # 标识符类型从符号获取
            if node.sym:
                node.type = node.sym.type
        elif node.op in (ASTNodeType.A_ADD, ASTNodeType.A_SUBTRACT, ASTNodeType.A_MULTIPLY, ASTNodeType.A_DIVIDE):
            # 二元运算类型
            if node.left and node.right and node.left.type:
                node.type = node.left.type
        elif node.op in (ASTNodeType.A_EQ, ASTNodeType.A_NE, ASTNodeType.A_LT, ASTNodeType.A_GT, ASTNodeType.A_LE,
                         ASTNodeType.A_GE):
            # 比较运算结果为bool类型
            node.type = cls.get_type(TypeKind.TY_BOOL)
        elif node.op == ASTNodeType.A_ASSIGN:
            # 赋值运算类型
            if node.right:
                node.type = node.right.type
        elif node.op == ASTNodeType.A_FUNCCALL:
            # 函数调用类型
            if node.sym and node.sym.sym_type == SymType.SYM_FUNC:
                node.type = node.sym.type
        elif node.op == ASTNodeType.A_CAST:
            # 类型转换类型
            if node.right and node.type:
                node.right = cls.widen_expression(node.right)

    @staticmethod
    def parse_litval(token_type: TokenType, value: str) -> Litval:
        litval = Litval()
        if token_type == TokenType.T_NUMLIT:
            # 解析整数和浮点数
            if value.startswith('0x') or value.startswith('0X'):
                litval.intval = int(value, 16)
            elif value.startswith('0') and len(value) > 1:
                litval.intval = int(value, 8)
            else:
                litval.intval = int(value)
            litval.dblval = float(litval.dblval)
        elif token_type == TokenType.T_STRLIT:
            # 解析字符串
            litval.strval = value
        else:
            fatal(f"Invalid literal token type: {token_type}")
        return litval

    @classmethod
    def widen_type(cls, t1: DataType, t2: DataType) -> Optional[DataType]:
        # 如果类型相同，直接返回
        if t1 == t2:
            return t1

        # 处理void类型
        if t1.kind == TypeKind.TY_VOID or t2.kind == TypeKind.TY_VOID:
            return None

        # 处理布尔类型
        if t1.kind == TypeKind.TY_BOOL:
            return t2
        if t2.kind == TypeKind.TY_BOOL:
            return t1

        # 处理浮点类型
        t1_flt = cls.is_float(t1)
        t2_flt = cls.is_float(t2)

        if t1_flt and t2_flt:
            # 两个都是浮点类型，返回精度更高的
            return t1 if t1.kind == TypeKind.TY_FLT64 else t2
        if t1_flt or t2_flt:
            # 一个是浮点，一个是整数，返回浮点类型
            return t1 if t1_flt else t2

        # 处理整数类型
        # 获取整数类型的宽度值
        def int_width(kind: TypeKind) -> int:
            widths = {
                TypeKind.TY_INT8: 8,
                TypeKind.TY_INT16: 16,
                TypeKind.TY_INT32: 32,
                TypeKind.TY_INT64: 64,
                TypeKind.TY_UINT8: 8,
                TypeKind.TY_UINT16: 16,
                TypeKind.TY_UINT32: 32,
                TypeKind.TY_UINT64: 64
            }
            return widths.get(kind, 0)

        # 如果一个是有符号，一个是无符号，返回更宽的类型
        if t1.is_unsigned != t2.is_unsigned:
            w1 = int_width(t1.kind)
            w2 = int_width(t2.kind)
            if w1 > w2:
                return t1
            elif w2 > w1:
                return t2
            # 宽度相同但符号不同，无法拓宽
            return None

        # 都是有符号或都是无符号，返回更宽的类型
        w1 = int_width(t1.kind)
        w2 = int_width(t2.kind)
        return t1 if w1 > w2 else t2

    @classmethod
    def widen_expression(cls, node: ASTNode) -> ASTNode | None:
        if not node:
            return None

        # 对于字面量，根据其值拓宽类型
        if node.op == ASTNodeType.A_NUMLIT:
            val = node.numlit.intval
            if -128 <= val <= 127:
                target_type = cls.get_type(TypeKind.TY_INT8)
            elif -32768 <= val <= 32767:
                target_type = cls.get_type(TypeKind.TY_INT16)
            elif -2147483648 <= val <= 2147483647:
                target_type = cls.get_type(TypeKind.TY_INT32)
            else:
                target_type = cls.get_type(TypeKind.TY_INT64)

            if not (node.type == target_type or
                    node.type.is_unsigned == target_type.is_unsigned and
                    node.type.size >= target_type.size):
                return cast_node(node, target_type)

        # 对于其他节点类型，可能需要不同的拓宽逻辑
        return node


# 初始化内置类型
TypeProcessor.init_builtin_types()

# 导出常用函数和类型
init_builtin_types = TypeProcessor.init_builtin_types
get_type = TypeProcessor.get_type
new_type = TypeProcessor.new_type
is_integer = TypeProcessor.is_integer
is_float = TypeProcessor.is_float
is_numeric = TypeProcessor.is_numeric
get_typename = TypeProcessor.get_typename
widen_type = TypeProcessor.widen_type
add_type = TypeProcessor.add_type
parse_litval = TypeProcessor.parse_litval
