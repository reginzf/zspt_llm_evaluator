from typing import List, Dict, Union, Tuple, Optional
from difflib import SequenceMatcher
import re
import numpy as np
from env_config_init import settings


class AlignmentBasedChecker:
    """基于对齐算法的对应关系判断"""

    # 默认模型路径配置
    DEFAULT_ENGLISH_MODEL = r'D:\pyworkplace\git_place\ai-ken\models\paraphrase-multilingual-MiniLM-L12-v2'
    DEFAULT_CHINESE_MODEL = r'D:\pyworkplace\git_place\ai-ken\models\text2vec-base-chinese'

    def __init__(self,
                 english_model_path: str = None,
                 chinese_model_path: str = None,
                 overlap_threshold: float = None,
                 similarity_threshold: float = None,
                 semantic_weight: float = None):
        """
        初始化AlignmentBasedChecker

        Args:
            english_model_path: 英文语义模型路径
            chinese_model_path: 中文/多语言语义模型路径
            overlap_threshold: 重叠阈值，默认从 settings.toml 读取
            similarity_threshold: 相似度阈值，默认从 settings.toml 读取
            semantic_weight: 语义权重，默认从 settings.toml 读取
        """
        self.english_model_path = english_model_path or self.DEFAULT_ENGLISH_MODEL
        self.chinese_model_path = chinese_model_path or self.DEFAULT_CHINESE_MODEL
        self._english_model = None
        self._chinese_model = None
        # 参数优先级：传入值 > settings.toml 默认值
        self.overlap_threshold = overlap_threshold if overlap_threshold is not None else settings.OVERLAP_THRESHOLD
        self.similarity_threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
        self.semantic_weight = semantic_weight if semantic_weight is not None else settings.SEMANTIC_WEIGHT

    # ==================== 基础工具方法 ====================
    
    def _extract_text(self, chunk) -> str:
        """从chunk对象中提取文本"""
        if isinstance(chunk, str):
            return chunk
        elif isinstance(chunk, dict):
            return chunk.get('text', '')
        return ''
    
    def _generate_text_preview(self, text: str, max_length: int = 100) -> str:
        """生成文本预览"""
        if len(text) > max_length:
            return text[:max_length] + '...'
        return text
    
    def _get_chunk_id(self, chunk, index: int) -> str:
        """获取chunk的ID"""
        if isinstance(chunk, dict) and 'chunk_id' in chunk:
            return chunk['chunk_id']
        return f'chunk_{index}'
    
    def _is_english_text(self, text: str) -> bool:
        """
        判断文本是否主要为英文
        
        Args:
            text: 待判断的文本
            
        Returns:
            True if primarily English, False otherwise
        """
        if not text:
            return False

        # 统计英文字符和中文字符的数量
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

        # 如果英文字符数量大于中文字符数量，则认为是英文
        return english_chars > chinese_chars
    
    def _get_semantic_model(self, is_english: bool):
        """
        懒加载语义模型
        
        Args:
            is_english: 是否为英文模型
            
        Returns:
            SentenceTransformer模型实例
        """
        from sentence_transformers import SentenceTransformer

        if is_english:
            if self._english_model is None:
                self._english_model = SentenceTransformer(self.english_model_path)
            return self._english_model
        else:
            if self._chinese_model is None:
                self._chinese_model = SentenceTransformer(self.chinese_model_path)
            return self._chinese_model
    
    def _get_model_for_texts(self, texts: List[str]) -> Optional:
        """
        根据文本语言获取合适的模型
        
        Args:
            texts: 文本列表
            
        Returns:
            SentenceTransformer模型实例或None
        """
        if not texts:
            return None
        
        # 取第一个文本判断语言
        sample_text = texts[0] if texts else ""
        is_english = self._is_english_text(sample_text)
        return self._get_semantic_model(is_english)
    
    # ==================== 相似度计算方法 ====================
    
    def calculate_overlap_ratio(self, text1: str, text2: str) -> Tuple[float, str]:
        """
        计算两个文本的重叠比例和重叠类型
        
        Args:
            text1: 第一个文本（来自chunk_list1）
            text2: 第二个文本（来自chunk_list2，人工标注）
            
        Returns:
            (重叠比例, 重叠类型)
            重叠类型: 'exact' - 完全重叠, 'contains' - 包含, 'partial' - 部分重叠, 'none' - 无重叠
        """
        if not text1 or not text2:
            return 0.0, 'none'

        # 去除首尾空白进行比较
        text1_stripped = text1.strip()
        text2_stripped = text2.strip()

        # 完全匹配
        if text1_stripped == text2_stripped:
            return 1.0, 'exact'

        # 检查包含关系
        if text1_stripped in text2_stripped:
            # text1 被 text2 包含
            ratio = len(text1_stripped) / len(text2_stripped)
            return ratio, 'contains'

        if text2_stripped in text1_stripped:
            # text2 被 text1 包含
            ratio = len(text2_stripped) / len(text1_stripped)
            return ratio, 'contains'

        # 部分重叠 - 使用SequenceMatcher计算
        matcher = SequenceMatcher(None, text1_stripped, text2_stripped)

        # 获取所有匹配块
        matching_blocks = matcher.get_matching_blocks()

        # 计算总匹配字符数
        total_match_chars = sum(block.size for block in matching_blocks)

        # 计算重叠比例（相对于较短文本）
        min_len = min(len(text1_stripped), len(text2_stripped))
        overlap_ratio = total_match_chars / min_len if min_len > 0 else 0.0

        if overlap_ratio > 0:
            return overlap_ratio, 'partial'

        return 0.0, 'none'
    
    def _calculate_chunk_similarity(self, chunk1: Dict, chunk2: Dict) -> float:
        """计算chunk相似度"""
        # 综合多种特征
        similarities = []

        # 1. 文本相似度
        text1 = self._extract_text(chunk1)
        text2 = self._extract_text(chunk2)

        if text1 and text2:
            # Jaccard相似度
            words1 = set(re.findall(r'\w+', text1.lower()))
            words2 = set(re.findall(r'\w+', text2.lower()))

            if words1 and words2:
                jaccard = len(words1 & words2) / len(words1 | words2)
                similarities.append(jaccard)

            # 序列相似度
            seq_matcher = SequenceMatcher(None, text1, text2)
            similarities.append(seq_matcher.ratio())

        # 2. 位置相似度（如果有）
        if 'start' in chunk1 and 'end' in chunk1 and 'start' in chunk2 and 'end' in chunk2:
            len1 = chunk1['end'] - chunk1['start']
            len2 = chunk2['end'] - chunk2['start']

            if len1 > 0 and len2 > 0:
                length_ratio = min(len1, len2) / max(len1, len2)
                similarities.append(length_ratio)

        # 3. 语义相似度（可以调用外部模型）
        # 这里简化处理

        return np.mean(similarities) if similarities else 0.0
    
    # ==================== 输入验证和结果初始化 ====================
    
    def _validate_inputs_and_get_defaults(self, chunk_list1: List[Union[str, Dict]], 
                                         chunk_list2: List[Union[str, Dict]], 
                                         detailed: bool = False) -> Tuple[bool, Optional[Dict]]:
        """
        验证输入并返回默认结果
        
        Args:
            chunk_list1: 第一个chunk列表
            chunk_list2: 第二个chunk列表
            detailed: 是否返回详细格式
            
        Returns:
            (是否继续处理, 默认结果或None)
        """
        if not chunk_list1:
            if detailed:
                return False, {
                    'scores': [],
                    'details': [],
                    'stats': {
                        'total_chunks': 0,
                        'exact_matches': 0,
                        'semantic_matches': 0,
                        'unmatched': 0,
                        'exact_match_rate': 0.0,
                        'overall_match_rate': 0.0
                    }
                }
            else:
                return False, []
        
        if not chunk_list2:
            if detailed:
                return False, {
                    'scores': [0.0] * len(chunk_list1),
                    'details': [{'index': i, 'match_type': 'unmatched', 'score': 0.0} 
                               for i in range(len(chunk_list1))],
                    'stats': {
                        'total_chunks': len(chunk_list1),
                        'exact_matches': 0,
                        'semantic_matches': 0,
                        'unmatched': len(chunk_list1),
                        'exact_match_rate': 0.0,
                        'overall_match_rate': 0.0
                    }
                }
            else:
                return False, [0.0] * len(chunk_list1)
        
        return True, None
    
    def _initialize_results(self, chunk_list1: List[Union[str, Dict]], 
                           detailed: bool = False) -> Tuple[List[float], List[Dict], set, List[int]]:
        """
        初始化结果数据结构
        
        Args:
            chunk_list1: chunk列表
            detailed: 是否返回详细格式
            
        Returns:
            (结果分数列表, 详细信息列表, 已匹配索引集合, 未匹配索引列表)
        """
        result = [0.0] * len(chunk_list1)
        details = [] if detailed else None
        matched_indices = set()
        unmatched_indices = []
        
        return result, details, matched_indices, unmatched_indices
    
    # ==================== 核心匹配逻辑 ====================
    
    def _perform_overlap_matching(self, texts1: List[str], texts2: List[str], 
                                 matched_indices: set, detailed: bool = False) -> Tuple[List[float], List[Dict], List[int]]:
        """
        执行重叠匹配
        
        Args:
            texts1: 第一个文本列表
            texts2: 第二个文本列表
            matched_indices: 已匹配的索引集合
            detailed: 是否返回详细格式
            
        Returns:
            (结果分数列表, 详细信息列表, 未匹配索引列表)
        """
        result = [0.0] * len(texts1)
        details = [] if detailed else None
        unmatched_indices = []

        # 用于记录哪些 chunk_list2（标注）已经被匹配
        matched_chunk2_indices = set()

        for i, text1 in enumerate(texts1):
            best_overlap = 0.0
            best_match_idx = -1
            best_overlap_type = 'none'

            for j, text2 in enumerate(texts2):
                # 修改：跳过已经匹配过的标注切片
                if j in matched_indices or j in matched_chunk2_indices:
                    continue

                overlap_ratio, overlap_type = self.calculate_overlap_ratio(text1, text2)

                # 完全重叠或包含，直接标记为完全匹配
                if overlap_type in ('exact', 'contains') and overlap_ratio >= self.overlap_threshold:
                    if overlap_ratio > best_overlap:
                        best_overlap = overlap_ratio
                        best_match_idx = j
                        best_overlap_type = overlap_type

                # 部分重叠超过阈值，也标记为完全匹配
                elif overlap_type == 'partial' and overlap_ratio >= self.overlap_threshold:
                    if overlap_ratio > best_overlap:
                        best_overlap = overlap_ratio
                        best_match_idx = j
                        best_overlap_type = overlap_type

            if best_match_idx >= 0:
                result[i] = 1.0
                matched_indices.add(best_match_idx)
                matched_chunk2_indices.add(best_match_idx)  # 标记标注切片已匹配

                if detailed and details is not None:
                    details.append({
                        'index': i,
                        'match_type': 'exact',
                        'overlap_type': best_overlap_type,
                        'overlap_ratio': best_overlap,
                        'matched_chunk2_index': best_match_idx,
                        'score': 1.0,
                        'chunk1_text_preview': self._generate_text_preview(text1),
                        'chunk2_text_preview': self._generate_text_preview(texts2[best_match_idx])
                    })
            else:
                unmatched_indices.append(i)
        
        return result, details, unmatched_indices
    
    def _perform_semantic_matching(self, texts1: List[str], texts2: List[str], 
                                  unmatched_indices: List[int], matched_indices: set,
                                  detailed: bool = False) -> Tuple[List[float], List[Dict], int]:
        """
        执行语义匹配
        
        Args:
            texts1: 第一个文本列表
            texts2: 第二个文本列表
            unmatched_indices: 未匹配的索引列表
            matched_indices: 已匹配的索引集合
            detailed: 是否返回详细格式
            
        Returns:
            (更新后的结果分数列表, 详细信息列表, 语义匹配数量)
        """
        result = [0.0] * len(texts1)
        details = [] if detailed else None
        semantic_match_count = 0
        
        if not unmatched_indices or not texts2:
            return result, details, semantic_match_count
        
        # 获取未匹配的文本和可用的chunk2文本
        unmatched_texts1 = [texts1[i] for i in unmatched_indices]
        
        # 可用的chunk2文本（排除已完全匹配的）
        available_chunk2_indices = [j for j in range(len(texts2)) if j not in matched_indices]
        available_texts2 = [texts2[j] for j in available_chunk2_indices]
        
        if not available_texts2:
            return result, details, semantic_match_count
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            model = self._get_model_for_texts(unmatched_texts1)
            if model is None:
                return result, details, semantic_match_count
            
            # 计算嵌入向量
            embeddings1 = model.encode(unmatched_texts1, convert_to_tensor=True)
            embeddings2 = model.encode(available_texts2, convert_to_tensor=True)
            
            # 计算相似度矩阵
            similarity_matrix = cosine_similarity(
                embeddings1.cpu().numpy(),
                embeddings2.cpu().numpy()
            )
            
            # 为每个未匹配的chunk1找最佳语义匹配
            for idx, orig_i in enumerate(unmatched_indices):
                max_similarity = np.max(similarity_matrix[idx])
                best_match_local_idx = np.argmax(similarity_matrix[idx])
                best_match_original_idx = available_chunk2_indices[best_match_local_idx]
                
                if max_similarity >= self.similarity_threshold:
                    # 应用权重
                    score = float(max_similarity) * self.semantic_weight
                    # 确保不超过1（除非权重>1）
                    if self.semantic_weight <= 1.0:
                        score = min(score, 0.99)  # 保持小于1以区分完全匹配
                    
                    result[orig_i] = score
                    semantic_match_count += 1
                    
                    if detailed and details is not None:
                        details.append({
                            'index': orig_i,
                            'match_type': 'semantic',
                            'similarity': float(max_similarity),
                            'matched_chunk2_index': best_match_original_idx,
                            'score': score,
                            'model_used': 'english' if self._is_english_text(unmatched_texts1[0]) else 'chinese',
                            'chunk1_text_preview': self._generate_text_preview(texts1[orig_i]),
                            'chunk2_text_preview': self._generate_text_preview(texts2[best_match_original_idx])
                        })
                elif detailed and details is not None:
                    details.append({
                        'index': orig_i,
                        'match_type': 'unmatched',
                        'best_similarity': float(max_similarity),
                        'score': 0.0,
                        'chunk1_text_preview': self._generate_text_preview(texts1[orig_i])
                    })
                    
        except ImportError as e:
            print(f"Warning: Could not import required modules for semantic matching: {e}")
        except Exception as e:
            print(f"Warning: Semantic matching failed: {e}")
            if detailed and details is not None:
                for orig_i in unmatched_indices:
                    details.append({
                        'index': orig_i,
                        'match_type': 'unmatched',
                        'error': str(e),
                        'score': 0.0,
                        'chunk1_text_preview': self._generate_text_preview(texts1[orig_i])
                    })
        
        return result, details, semantic_match_count
    
    # ==================== 主接口方法 ====================
    
    def check_chunk_match(self,
                          chunk_list1: List[Union[str, Dict]],
                          chunk_list2: List[Union[str, Dict]]) -> List[float]:
        """
        检查chunk_list1中的每个切片与chunk_list2的匹配情况
        
        Args:
            chunk_list1: 知识平台召回的切片正文列表
            chunk_list2: 人工标注的结果列表
            
        Returns:
            匹配结果列表，与chunk_list1一一对应:
            - 1: 完全匹配（完全重叠、包含或部分重叠>=overlap_threshold）
            - 小数: 语义相似度分数（>= similarity_threshold）
            - 0: 未匹配
        """
        # 验证输入
        should_continue, default_result = self._validate_inputs_and_get_defaults(
            chunk_list1, chunk_list2, detailed=False
        )
        if not should_continue:
            return default_result
        
        # 提取文本
        texts1 = [self._extract_text(chunk) for chunk in chunk_list1]
        texts2 = [self._extract_text(chunk) for chunk in chunk_list2]
        
        # 初始化结果
        result, _, matched_indices, unmatched_indices = self._initialize_results(
            chunk_list1, detailed=False
        )
        
        # 执行重叠匹配
        overlap_result, _, unmatched_indices = self._perform_overlap_matching(
            texts1, texts2, matched_indices, detailed=False
        )
        
        # 更新结果
        for i, score in enumerate(overlap_result):
            if score > 0:
                result[i] = score
        
        # 执行语义匹配
        semantic_result, _, _ = self._perform_semantic_matching(
            texts1, texts2, unmatched_indices, matched_indices, detailed=False
        )
        
        # 更新语义匹配结果
        for i, score in enumerate(semantic_result):
            if score > 0:
                result[i] = score
        
        return result
    
    def check_chunk_match_detailed(self,
                                   chunk_list1: List[Union[str, Dict]],
                                   chunk_list2: List[Union[str, Dict]]) -> Dict:
        """
        检查chunk匹配情况并返回详细信息
        
        Args:
            chunk_list1: 知识平台召回的切片正文列表
            chunk_list2: 人工标注的结果列表
            
        Returns:
            详细的匹配结果字典，包含:
            - scores: 匹配分数列表
            - details: 每个chunk的详细匹配信息
            - stats: 统计信息
        """
        # 验证输入
        should_continue, default_result = self._validate_inputs_and_get_defaults(
            chunk_list1, chunk_list2, detailed=True
        )
        if not should_continue:
            return default_result
        
        # 提取文本
        texts1 = [self._extract_text(chunk) for chunk in chunk_list1]
        texts2 = [self._extract_text(chunk) for chunk in chunk_list2]
        
        # 初始化结果
        result, details, matched_indices, unmatched_indices = self._initialize_results(
            chunk_list1, detailed=True
        )
        
        # 执行重叠匹配
        overlap_result, overlap_details, unmatched_indices = self._perform_overlap_matching(
            texts1, texts2, matched_indices, detailed=True
        )
        
        # 更新结果和详细信息
        for i, score in enumerate(overlap_result):
            if score > 0:
                result[i] = score
        
        if overlap_details:
            details.extend(overlap_details)
        
        # 执行语义匹配
        semantic_result, semantic_details, semantic_match_count = self._perform_semantic_matching(
            texts1, texts2, unmatched_indices, matched_indices, detailed=True
        )
        
        # 更新语义匹配结果
        for i, score in enumerate(semantic_result):
            if score > 0:
                result[i] = score
        
        if semantic_details:
            details.extend(semantic_details)
        
        # 处理剩余的未匹配项（如果没有在语义匹配中处理）
        for i in unmatched_indices:
            if result[i] == 0.0:
                details.append({
                    'index': i,
                    'match_type': 'unmatched',
                    'score': 0.0,
                    'chunk1_text_preview': self._generate_text_preview(texts1[i])
                })
        
        # 按索引排序details
        details.sort(key=lambda x: x['index'])
        
        # 计算统计信息
        exact_matches = sum(1 for d in details if d['match_type'] == 'exact')
        unmatched = sum(1 for d in details if d['match_type'] == 'unmatched')
        
        stats = {
            'total_chunks': len(chunk_list1),
            'exact_matches': exact_matches,
            'semantic_matches': semantic_match_count,
            'unmatched': unmatched,
            'exact_match_rate': exact_matches / len(chunk_list1) * 100 if chunk_list1 else 0,
            'overall_match_rate': (exact_matches + semantic_match_count) / len(chunk_list1) * 100 if chunk_list1 else 0,
            'average_score': np.mean(result) if result else 0
        }
        
        return {
            'scores': result,
            'details': details,
            'stats': stats
        }
    
    # ==================== 动态规划对齐方法 ====================
    
    def find_optimal_alignment(self, chunk_list1: List[Dict], chunk_list2: List[Dict]) -> Dict:
        """
        使用动态规划找到最优对齐

        Args:
            chunk_list1: 第一个chunk列表
            chunk_list2: 第二个chunk列表

        Returns:
            最优对齐结果
        """
        n = len(chunk_list1)
        m = len(chunk_list2)

        # 初始化DP表
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        path = [[None] * (m + 1) for _ in range(n + 1)]

        # 填充DP表
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                chunk1 = chunk_list1[i - 1]
                chunk2 = chunk_list2[j - 1]

                # 计算相似度
                similarity = self._calculate_chunk_similarity(chunk1, chunk2)

                # 三种操作：匹配、跳过chunk1、跳过chunk2
                options = [
                    (dp[i - 1][j - 1] + similarity, 'match', (i - 1, j - 1)),
                    (dp[i - 1][j], 'skip1', (i - 1, j)),
                    (dp[i][j - 1], 'skip2', (i, j - 1))
                ]

                # 选择最优操作
                best_score, best_op, best_prev = max(options, key=lambda x: x[0])
                dp[i][j] = best_score
                path[i][j] = (best_op, best_prev)

        # 回溯找到对齐路径
        alignment = []
        i, j = n, m

        while i > 0 or j > 0:
            if path[i][j] is None:
                break

            op, (prev_i, prev_j) = path[i][j]

            if op == 'match':
                alignment.append({
                    'chunk1_index': i - 1,
                    'chunk2_index': j - 1,
                    'chunk1_id': self._get_chunk_id(chunk_list1[i - 1], i - 1),
                    'chunk2_id': self._get_chunk_id(chunk_list2[j - 1], j - 1),
                    'similarity': self._calculate_chunk_similarity(
                        chunk_list1[i - 1], chunk_list2[j - 1]
                    )
                })
                i, j = prev_i, prev_j
            elif op == 'skip1':
                alignment.append({
                    'chunk1_index': i - 1,
                    'chunk2_index': None,
                    'chunk1_id': self._get_chunk_id(chunk_list1[i - 1], i - 1),
                    'chunk2_id': None,
                    'similarity': 0
                })
                i, j = prev_i, prev_j
            elif op == 'skip2':
                alignment.append({
                    'chunk1_index': None,
                    'chunk2_index': j - 1,
                    'chunk1_id': None,
                    'chunk2_id': self._get_chunk_id(chunk_list2[j - 1], j - 1),
                    'similarity': 0
                })
                i, j = prev_i, prev_j

        alignment.reverse()

        return {
            'alignment': alignment,
            'total_score': dp[n][m],
            'normalized_score': dp[n][m] / max(n, m),
            'alignment_length': len(alignment),
            'matches_count': sum(
                1 for a in alignment if a['chunk1_index'] is not None and a['chunk2_index'] is not None)
        }


# 使用示例
if __name__ == '__main__':
    # 示例数据
    chunk_list1 = [
        "这是知识平台召回的第一个切片内容，包含一些重要信息。",
        "The quick brown fox jumps over the lazy dog.",
        "部分重叠的文本内容，这里有一些相同的部分。",
        "这是一段完全不同的内容，可能无法匹配。",
        "语义相似但文字不同的表述方式。"
    ]

    chunk_list2 = [
        "这是知识平台召回的第一个切片内容，包含一些重要信息。",  # 完全匹配
        "The quick brown fox jumps over the lazy dog. Additional text here.",  # 包含关系
        "部分重叠的文本内容，这里有一些相同的部分，但也有不同。",  # 部分重叠
        "用不同的词语来表达相似的含义和意思。"  # 语义相似
    ]

    checker = AlignmentBasedChecker()

    # 简单版本 - 只返回分数列表
    scores = checker.check_chunk_match(
        chunk_list1,
        chunk_list2
    )
    print("匹配分数:", scores)

    # 详细版本 - 返回完整信息
    result = checker.check_chunk_match_detailed(
        chunk_list1,
        chunk_list2
    )
    print("\n详细结果:")
    print(f"分数列表: {result['scores']}")
    print(f"统计信息: {result['stats']}")
    print("\n每个切片的详细信息:")
    for detail in result['details']:
        print(f"  索引 {detail['index']}: {detail['match_type']} - 分数: {detail['score']}")
