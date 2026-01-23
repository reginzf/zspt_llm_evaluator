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

        # 构建系统提示，包含所有问题列表
        questions_str_parts = []
        for question_type, question_list in self.questions_index.items():
            questions_str = "\n".join([f"{i}. {q}" for i, q in enumerate(question_list)])
            questions_str_parts.append(f"问题类型: {question_type}\n问题列表:\n{questions_str}\n")
        
        all_questions_str = "\n".join(questions_str_parts)

        system_prompt = f"""你是一个专业的知识标注助手，负责将知识切片与预定义的问题进行匹配。
        
知识领域：{self.domain_config.get('knowledge_domain', '')}
领域描述：{self.domain_config.get('domain_description', '')}
背景要求：{', '.join(self.domain_config.get('required_background', []))}
技能要求：{', '.join(self.domain_config.get('required_skills', []))}

所有可用问题列表：
{all_questions_str}

匹配规则：
1. 仔细分析知识切片的内容和意图
2. 将切片与各类问题进行语义匹配，不仅限于关键词匹配
3. 考虑同义词、近义词和概念匹配
4. 匹配时考虑问题类型（factual-事实型, contextual-上下文型, conceptual-概念型, reasoning-推理型, application-应用型）
5. 一次性返回所有匹配的问题索引，格式为：{{"factual": [0, 2], "contextual": [1], "conceptual": [], "reasoning": [0, 1, 2], "application": [1]}}
6. 只返回JSON格式结果，不要返回任何解释"""

        user_prompt = f"""请分析以下知识切片，并返回与之匹配的问题索引：
知识切片：
{slice_text}

请严格按照以下JSON格式返回，对每种类型返回匹配的问题索引列表（从0开始）：
{{"factual": [index1, index2], "contextual": [index3], "conceptual": [], "reasoning": [index1, index2], "application": [index4]}}
如果没有匹配任何问题，返回空字典 {{}}：
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500,  # 增加token限制以容纳所有类型的输出
                frequency_penalty=0.0,
                presence_penalty=0.0,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content.strip()

            # 解析响应
            try:
                result = json.loads(response_text)
                
                # 验证结果格式并清理索引
                cleaned_result = {}
                for question_type, indices in result.items():
                    if isinstance(indices, list) and question_type in self.questions_index:
                        question_list = self.questions_index[question_type]
                        # 验证索引是否有效
                        valid_indices = [idx for idx in indices
                                         if isinstance(idx, int) and 0 <= idx < len(question_list)]
                        if valid_indices:  # 只有在有有效索引时才添加
                            cleaned_result[question_type] = sorted(list(set(valid_indices)))
                
                return cleaned_result if cleaned_result else "无匹配"
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试从响应中提取JSON部分
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        result = json.loads(json_str)
                        
                        # 验证结果格式并清理索引
                        cleaned_result = {}
                        for question_type, indices in result.items():
                            if isinstance(indices, list) and question_type in self.questions_index:
                                question_list = self.questions_index[question_type]
                                # 验证索引是否有效
                                valid_indices = [idx for idx in indices
                                                 if isinstance(idx, int) and 0 <= idx < len(question_list)]
                                if valid_indices:  # 只有在有有效索引时才添加
                                    cleaned_result[question_type] = sorted(list(set(valid_indices)))
                        
                        return cleaned_result if cleaned_result else "无匹配"
                    except json.JSONDecodeError:
                        pass
                
                # 如果仍然失败，返回"无匹配"
                return "无匹配"

        except Exception as e:
            print(f"LLM调用失败: {e}")
            # 如果LLM调用失败，使用简单的关键词匹配作为备用方案
            return self.fallback_keyword_matching_all_types(slice_text)

    def fallback_keyword_matching_all_types(self, slice_text: str) -> Dict[str, List[int]]:
        """
        备用关键词匹配算法，处理所有问题类型
        
        Args:
            slice_text: 知识切片文本
            
        Returns:
            匹配结果字典
        """
        result = {}
        slice_lower = slice_text.lower()

        for question_type, question_list in self.questions_index.items():
            matched_indices = []
            
            for idx, question in enumerate(question_list):
                question_lower = question.lower()

                # 简单的关键词匹配逻辑
                question_words = re.findall(r'\w+', question_lower)
                slice_words = re.findall(r'\w+', slice_lower)

                # 计算词汇重叠度
                overlap = set(question_words) & set(slice_words)
                if len(overlap) > 0:
                    matched_indices.append(idx)
            
            if matched_indices:
                result[question_type] = matched_indices

        return result if result else "无匹配"

