from typing import Union, List, Dict
import json
import re
from openai import OpenAI

from env_config_init import settings


class KnowledgeSliceAnnotator:
    """
    知识切片智能标注器
    使用LLM将知识切片匹配到预定义的问题库中
    """

    def __init__(self, domain_config: dict, questions_config: dict):
        """
        初始化标注器
        
        Args:
            domain_config: 领域配置
            questions_config: 问题库配置
        """
        # 初始化LLM客户端，使用settings.toml中的配置
        api_key = settings.DEEPSEEK_API_KEY or settings.OPENAI_API_KEY
        api_base = settings.DEEPSEEK_API_BASE or settings.OPENAI_API_BASE
        model_name = settings.MODEL_NAME or "deepseek-chat"

        if not api_key:
            raise ValueError("未配置API密钥，请在settings.toml中设置DEEPSEEK_API_KEY或OPENAI_API_KEY")

        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        self.model_name = model_name

        self.domain_config = domain_config
        self.questions_config = questions_config
        self.questions_index = self.load_questions(questions_config)

    def load_questions(self, questions_config: dict) -> dict:
        """
        加载问题配置，构建问题索引
        
        Args:
            questions_config: 问题配置字典
            
        Returns:
            构建好的问题索引字典
        """
        questions_index = {}

        if "datas" in questions_config:
            for data_item in questions_config["datas"]:
                question_type = data_item.get("type", "")
                questions = data_item.get("questions", [])

                if question_type and questions:
                    questions_index[question_type] = questions

        return questions_index

    def semantic_matching(self, slice_text: str, question_list: List[str], question_type: str) -> List[int]:
        """
        使用LLM进行语义匹配
        
        Args:
            slice_text: 知识切片文本
            question_list: 问题列表
            question_type: 问题类型
            
        Returns:
            匹配到的问题下标列表
        """
        if not slice_text.strip() or not question_list:
            return []

        # 构建系统提示
        system_prompt = f"""你是一个专业的知识标注助手，负责将知识切片与预定义的问题进行匹配。
        
知识领域：{self.domain_config.get('knowledge_domain', '')}
领域描述：{self.domain_config.get('domain_description', '')}
背景要求：{', '.join(self.domain_config.get('required_background', []))}
技能要求：{', '.join(self.domain_config.get('required_skills', []))}

匹配规则：
1. 仔细分析知识切片的内容和意图
2. 将切片与问题进行语义匹配，不仅限于关键词匹配
3. 考虑同义词、近义词和概念匹配
4. 匹配时考虑问题类型（factual-事实型, contextual-上下文型, conceptual-概念型, reasoning-推理型, application-应用型）
5. 只返回匹配的问题索引（从0开始），不要返回任何解释"""

        # 构建用户提示
        questions_str = "\n".join([f"{i}. {q}" for i, q in enumerate(question_list)])

        user_prompt = f"""请分析以下知识切片，并返回与之匹配的问题索引列表：

知识切片：
{slice_text}

问题列表：
{questions_str}

请严格按照JSON数组格式返回，只返回匹配的问题索引列表（从0开始），例如 [0, 2, 3]：
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=200,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content.strip()

            # 由于使用了json_object格式，直接尝试解析整个响应
            try:
                matched_indices = json.loads(response_text)
                # 如果解析成功，验证它是一个列表
                if isinstance(matched_indices, list):
                    # 验证索引是否有效
                    valid_indices = [idx for idx in matched_indices
                                     if isinstance(idx, int) and 0 <= idx < len(question_list)]
                    return sorted(list(set(valid_indices)))  # 去重并排序
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试从响应中提取JSON部分
                json_match = re.search(r'\[(.*?)\]', response_text)
                if json_match:
                    indices_str = json_match.group(0)
                    try:
                        matched_indices = json.loads(indices_str)
                        # 验证索引是否有效
                        valid_indices = [idx for idx in matched_indices
                                         if isinstance(idx, int) and 0 <= idx < len(question_list)]
                        return sorted(list(set(valid_indices)))  # 去重并排序
                    except json.JSONDecodeError:
                        pass

            # 如果以上方法都失败，尝试简单数字提取作为后备方案
            numbers = re.findall(r'\d+', response_text)
            indices = [int(num) for num in numbers if 0 <= int(num) < len(question_list)]
            return sorted(list(set(indices)))

        except Exception as e:
            print(f"LLM调用失败: {e}")
            # 如果LLM调用失败，使用简单的关键词匹配作为备用方案
            return self.fallback_keyword_matching(slice_text, question_list)

    def fallback_keyword_matching(self, slice_text: str, question_list: List[str]) -> List[int]:
        """
        备用关键词匹配算法
        
        Args:
            slice_text: 知识切片文本
            question_list: 问题列表
            
        Returns:
            匹配到的问题下标列表
        """
        matched_indices = []
        slice_lower = slice_text.lower()

        for idx, question in enumerate(question_list):
            question_lower = question.lower()

            # 简单的关键词匹配逻辑
            # 检查切片是否包含问题中的重要词汇
            question_words = re.findall(r'\w+', question_lower)
            slice_words = re.findall(r'\w+', slice_lower)

            # 计算词汇重叠度
            overlap = set(question_words) & set(slice_words)
            if len(overlap) > 0:
                matched_indices.append(idx)

        return sorted(matched_indices)

    def analyze_slice(self, slice_text: str) -> Union[Dict[str, List[int]], str]:
        """
        分析知识切片并返回匹配结果
        
        Args:
            slice_text: 知识切片文本
            
        Returns:
            匹配结果字典或"无匹配"
        """
        if not slice_text or not slice_text.strip():
            return "无匹配"

        result = {}

        for question_type, question_list in self.questions_index.items():
            matched_indices = self.semantic_matching(slice_text, question_list, question_type)

            if matched_indices:
                result[question_type] = matched_indices

        return result if result else "无匹配"


def demo():
    # 示例配置
    domain_config = {
        "knowledge_domain": "OSPFv2协议",
        "domain_description": "开放最短路径优先协议版本2，是IP网络中使用最广泛的内部网关协议之一",
        "required_background": [
            "网络基础知识（TCP/IP协议栈）",
            "路由协议基本概念",
            "OSPF基本术语和工作原理"
        ],
        "required_skills": [
            "网络协议分析能力",
            "技术文档理解能力",
            "问题分类和匹配能力"
        ]
    }

    questions_config = {
        "doc_name": "OSPFv2",
        "datas": [
            {
                "type": "factual",
                "label_type": "Choice",
                "label_config": {
                    "choice": "multiple"
                },
                "questions": [
                    "OSPF协议使用哪个IP协议号？",
                    "OSPF Hello报文默认发送间隔是多少秒？",
                    "OSPF Router ID通常如何确定？"
                ]
            },
            {
                "type": "contextual",
                "label_type": "Choice",
                "label_config": {
                    "choice": "multiple"
                },
                "questions": [
                    "在OSPF中，DR和BDR的作用是什么？",
                    "OSPF邻居状态从Init到Full需要经历哪些状态？",
                    "OSPF区域边界路由器（ABR）的主要功能是什么？"
                ]
            },
            {
                "type": "conceptual",
                "label_type": "Choice",
                "label_config": {
                    "choice": "multiple"
                },
                "questions": [
                    "解释OSPF链路状态数据库（LSDB）的概念",
                    "解释OSPF中SPF算法的基本工作原理",
                    "解释OSPF区域划分的目的和优势"
                ]
            },
            {
                "type": "reasoning",
                "label_type": "Choice",
                "label_config": {
                    "choice": "multiple"
                },
                "questions": [
                    "如果OSPF邻居无法建立Full状态，可能的原因有哪些？",
                    "为什么在广播网络中需要选举DR和BDR？"
                ]
            },
            {
                "type": "application",
                "label_type": "Choice",
                "label_config": {
                    "choice": "multiple"
                },
                "questions": [
                    "如何在Cisco路由器上配置基本的OSPF？",
                    "如何查看OSPF邻居状态？"
                ]
            }
        ]
    }

    # 初始化标注器
    annotator = KnowledgeSliceAnnotator(domain_config, questions_config)

    # 测试用例
    test_cases = [
        "使用 dis ospf peer 查看ospf邻居状态",
        "OSPF使用IP协议号89进行通信，这是IANA分配的专门协议号",
        "BGP协议使用TCP端口179建立连接",
        "在Cisco路由器上进入配置模式，使用router ospf命令启用OSPF进程，然后配置network语句指定参与OSPF的接口"
    ]

    print("LLM知识切片标注演示:")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"输入切片: {test_case}")
        result = annotator.analyze_slice(test_case)
        print(f"标注结果: {result}")
        print("-" * 50)


if __name__ == '__main__':
    demo()
