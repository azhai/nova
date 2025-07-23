from typing import Dict, Optional

from defs import Strlit, OutFile


class StrLitProcessor:
    def __init__(self):
        self.strlit_dict: Dict[str, int] = {}
        self.next_strlit_label = 1
        self.strlit_list: Optional[Strlit] = None

    def add_strlit(self, value: str) -> int:
        """添加字符串字面量，避免重复并返回其标签"""
        if value in self.strlit_dict:
            return self.strlit_dict[value]

        # 分配新标签
        label = self.next_strlit_label
        self.next_strlit_label += 1
        self.strlit_dict[value] = label

        # 添加到字符串字面量列表
        new_strlit = Strlit(val=value, label=label, sibling=self.strlit_list)
        self.strlit_list = new_strlit

        return label

    def gen_strlits(self) -> None:
        """生成所有字符串字面量的汇编代码"""
        strlit = self.strlit_list
        while strlit:
            # 转义特殊字符
            escaped = strlit.val.replace('\a', '\\a').replace('\b', '\\b')
            escaped = escaped.replace('\f', '\\f').replace('\n', '\\n')
            escaped = escaped.replace('\r', '\\r').replace('\t', '\\t').replace('\v', '\\v')
            escaped = escaped.replace('\\', '\\\\').replace('"', '\\"')
            # 生成数据定义
            print(f"data $L{strlit.label} = {{ b \"{escaped}\", b 0 }}", file=OutFile)
            strlit = strlit.sibling

    def get_strlit_label(self, value: str) -> int:
        """获取字符串字面量的标签，如果不存在则添加"""
        if value not in self.strlit_dict:
            return self.add_strlit(value)
        return self.strlit_dict[value]


# 创建字符串字面量处理器实例并导出函数
strlit_processor = StrLitProcessor()
add_strlit = strlit_processor.add_strlit
gen_strlits = strlit_processor.gen_strlits
get_strlit_label = strlit_processor.get_strlit_label
