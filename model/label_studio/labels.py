import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class QuestionType(Enum):
    """问题类型枚举"""
    FACTUAL = "factual"
    CONTEXTUAL = "contextual"
    CONCEPTUAL = "conceptual"
    REASONING = "reasoning"
    APPLICATION = "application"

@dataclass
class Question:
    """问题数据类"""
    text: str
    background_color: Optional[str] = None


@dataclass
class QuestionGroup:
    """问题组数据类"""
    type: QuestionType
    questions: List[Question]
    label_type: str = "Choice"
    label_config: Dict[str, Any] = field(default_factory=lambda: {"choice": "multiple"})


@dataclass
class LabelConfig:
    """标签配置数据类"""
    doc_name: str
    question_groups: List[QuestionGroup]


class LabelStudioXMLGenerator:
    """Label Studio XML配置生成器"""

    # 默认颜色映射
    COLOR_MAP = {
        QuestionType.FACTUAL: None,  # 使用默认颜色
        QuestionType.CONTEXTUAL: ["#4CAF50", "#FFC107", "#F44336"],  # 绿色、黄色、红色
        QuestionType.CONCEPTUAL: ["#4CAF50", "#FFC107"],  # 绿色、黄色
        QuestionType.REASONING: ["#4CAF50", "#FFC107"],  # 绿色、黄色
        QuestionType.APPLICATION:["#4CAF50", "#FFC107"]
    }

    # 类型显示名称映射
    TYPE_DISPLAY_NAMES = {
        QuestionType.FACTUAL: "事实型",
        QuestionType.CONTEXTUAL: "上下文型",
        QuestionType.CONCEPTUAL: "概念型",
        QuestionType.REASONING: "推理型",
        QuestionType.APPLICATION: "应用型",
    }

    def __init__(self, grid_columns: int = 2, gap: str = "10px"):
        """
        初始化XML生成器

        Args:
            grid_columns: 网格列数
            gap: 网格间距
        """
        self.grid_columns = grid_columns
        self.gap = gap

    def _create_header(self, text: str, size: int = 4) -> ET.Element:
        """创建Header元素"""
        header = ET.Element("Header")
        header.set("value", text)
        header.set("size", str(size))
        return header

    def _create_choice(self, question: Question) -> ET.Element:
        """创建Choice元素"""
        choice = ET.Element("Choice")
        choice.set("value", question.text)
        if question.background_color:
            choice.set("background", question.background_color)
        return choice

    def _create_choices(self, group: QuestionGroup) -> ET.Element:
        """创建Choices元素"""
        choices = ET.Element("Choices")
        choices.set("name", group.type.value)
        choices.set("toName", "text")
        choices.set("choice", group.label_config.get("choice", "multiple"))

        # 为每个问题创建Choice元素
        for i, question in enumerate(group.questions):
            # 如果没有指定颜色，使用颜色映射中的颜色
            if not question.background_color and group.type in self.COLOR_MAP:
                colors = self.COLOR_MAP[group.type]
                if colors and i < len(colors):
                    question.background_color = colors[i]

            choice_elem = self._create_choice(question)
            choices.append(choice_elem)

        return choices

    def _create_question_group_view(self, group: QuestionGroup) -> ET.Element:
        """创建问题组的View元素"""
        view = ET.Element("View")

        # 添加Header
        header_text = self.TYPE_DISPLAY_NAMES.get(group.type, group.type.value)
        header = self._create_header(header_text, size=5)
        view.append(header)

        # 添加Choices
        choices = self._create_choices(group)
        view.append(choices)

        return view

    def _create_grid_view(self, groups: List[QuestionGroup]) -> ET.Element:
        """创建网格布局的View元素"""
        grid_view = ET.Element("View")
        grid_view.set("style",
                      f"display: grid; grid-template-columns: repeat({self.grid_columns}, 1fr); gap: {self.gap};")

        for group in groups:
            group_view = self._create_question_group_view(group)
            grid_view.append(group_view)

        return grid_view

    def generate_xml(self, config: LabelConfig) -> str:
        """
        生成完整的XML配置

        Args:
            config: 标签配置对象

        Returns:
            格式化的XML字符串
        """
        # 创建根元素
        root = ET.Element("View")

        # 第一部分：切片文本显示区域
        text_view = ET.Element("View")
        text_view.set("style", "background: #f5f5f5; padding: 15px; border-radius: 5px;")


        # 添加Text元素
        text_elem = ET.Element("Text")
        text_elem.set("name", "text")
        text_elem.set("value", "$text")
        text_elem.set("style", "font-family: monospace;")
        text_view.append(text_elem)

        root.append(text_view)

        # 第二部分：召回问题标注区域
        recall_view = ET.Element("View")
        recall_view.set("style", "background: #e3f2fd; padding: 15px; border-radius: 5px; margin-top: 15px;")


        # 添加网格布局
        grid_view = self._create_grid_view(config.question_groups)
        recall_view.append(grid_view)

        root.append(recall_view)

        # 转换为格式化的XML字符串
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        return pretty_xml

    def generate_from_json(self, json_data: Dict[str, Any]) -> str:
        """
        从JSON数据生成XML配置

        Args:
            json_data: JSON格式的数据

        Returns:
            格式化的XML字符串
        """
        # 解析JSON数据
        doc_name = json_data.get("doc_name", "未命名文档")
        datas = json_data.get("datas", [])

        # 转换问题组
        question_groups = []
        for data in datas:
            question_type = QuestionType(data.get("type"))
            questions_data = data.get("questions", [])

            # 创建问题列表
            questions = [Question(text=q) for q in questions_data]

            # 创建问题组
            group = QuestionGroup(
                type=question_type,
                questions=questions,
                label_type=data.get("label_type", "Choice"),
                label_config=data.get("label_config", {"choice": "multiple"})
            )
            question_groups.append(group)

        # 创建配置对象
        config = LabelConfig(
            doc_name=doc_name,
            question_groups=question_groups
        )

        return self.generate_xml(config)


def main():
    """主函数示例"""
    # 创建生成器
    from utils.pub_funs import load_json_file, save_xml_file
    generator = LabelStudioXMLGenerator(grid_columns=2, gap="10px")
    # 示例：从文件加载
    json_data = load_json_file(r"D:\pyworkplace\git_place\ai-ken\tests\ospf\ospfv2_detailed_questions.json")
    xml_content = generator.generate_from_json(json_data)
    # 保存到文件
    save_xml_file(xml_content, "output.xml")


if __name__ == "__main__":
    main()
