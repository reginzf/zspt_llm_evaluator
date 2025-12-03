from typing import List, Dict
import re
from difflib import SequenceMatcher


class CorrespondenceChecker:
    """
    检查不同切片size的chunk列表对应关系
    original_text: 只支持text
    """

    def __init__(self, original_text: str = None):
        self.original_text = original_text

    def check_content_overlap_correspondence(self,
                                             chunk_list1: List[Dict],
                                             chunk_list2: List[Dict],
                                             overlap_threshold: float = 0.7) -> Dict:
        """
        基于内容重叠度判断对应关系

        Args:
            chunk_list1: 第一个chunk列表，每个chunk包含text和位置信息
            chunk_list2: 第二个chunk列表
            overlap_threshold: 重叠度阈值，默认0.7

        Returns:
            对应关系映射和统计信息
        """
        # 确保chunk有文本内容
        chunk_list1 = self._ensure_chunk_format(chunk_list1)
        chunk_list2 = self._ensure_chunk_format(chunk_list2)

        correspondence = {
            "chunk1_to_chunk2": {},  # chunk1 -> [chunk2_ids]
            "chunk2_to_chunk1": {},  # chunk2 -> [chunk1_ids]
            "one_to_one_mapping": [],  # 一对一映射
            "one_to_many_mapping": [],  # 一对多映射
            "many_to_one_mapping": [],  # 多对一映射
            "unmatched_chunks": []  # 未匹配的chunk
        }

        # 计算所有chunk对的重叠度
        overlap_matrix = self._calculate_overlap_matrix(chunk_list1, chunk_list2)

        # 寻找对应关系
        for i, chunk1 in enumerate(chunk_list1):
            chunk1_id = chunk1.get('chunk_id', f'chunk1_{i}')
            max_overlap = 0
            best_matches = []

            for j, chunk2 in enumerate(chunk_list2):
                chunk2_id = chunk2.get('chunk_id', f'chunk2_{j}')
                overlap = overlap_matrix[i][j]

                if overlap >= overlap_threshold:
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_matches = [(chunk2_id, overlap)]
                    elif overlap == max_overlap:
                        best_matches.append((chunk2_id, overlap))

            if best_matches:
                correspondence["chunk1_to_chunk2"][chunk1_id] = best_matches

                # 判断映射类型
                if len(best_matches) == 1:
                    chunk2_id = best_matches[0][0]

                    # 检查是否也是一对一
                    if chunk2_id not in correspondence["chunk2_to_chunk1"]:
                        correspondence["chunk2_to_chunk1"][chunk2_id] = [(chunk1_id, max_overlap)]
                        correspondence["one_to_one_mapping"].append((chunk1_id, chunk2_id, max_overlap))
                    else:
                        correspondence["chunk2_to_chunk1"][chunk2_id].append((chunk1_id, max_overlap))
                        correspondence["many_to_one_mapping"].append((chunk1_id, chunk2_id, max_overlap))
                else:
                    for chunk2_id, overlap in best_matches:
                        if chunk2_id not in correspondence["chunk2_to_chunk1"]:
                            correspondence["chunk2_to_chunk1"][chunk2_id] = [(chunk1_id, overlap)]
                        else:
                            correspondence["chunk2_to_chunk1"][chunk2_id].append((chunk1_id, overlap))
                    correspondence["one_to_many_mapping"].append((chunk1_id, [c[0] for c in best_matches], max_overlap))
            else:
                correspondence["unmatched_chunks"].append(chunk1_id)

        # 统计信息
        correspondence["stats"] = {
            "total_chunk1": len(chunk_list1),
            "total_chunk2": len(chunk_list2),
            "one_to_one_count": len(correspondence["one_to_one_mapping"]),
            "one_to_many_count": len(correspondence["one_to_many_mapping"]),
            "many_to_one_count": len(correspondence["many_to_one_mapping"]),
            "unmatched_count": len(correspondence["unmatched_chunks"])
        }

        return correspondence

    def _ensure_chunk_format(self, chunk_list: List[Dict]) -> List[Dict]:
        """确保chunk格式统一"""
        formatted = []
        for i, chunk in enumerate(chunk_list):
            if isinstance(chunk, str):
                formatted.append({
                    'text': chunk,
                    'chunk_id': f'chunk_{i}',
                    'index': i
                })
            elif isinstance(chunk, dict):
                if 'chunk_id' not in chunk:
                    chunk['chunk_id'] = f'chunk_{i}'
                if 'index' not in chunk:
                    chunk['index'] = i
                formatted.append(chunk)
        return formatted

    def _calculate_overlap_matrix(self, chunk_list1: List[Dict], chunk_list2: List[Dict]) -> List[List[float]]:
        """计算重叠度矩阵"""
        matrix = []
        for chunk1 in chunk_list1:
            row = []
            text1 = chunk1['text'].lower().strip()

            for chunk2 in chunk_list2:
                text2 = chunk2['text'].lower().strip()

                # 使用多种方法计算相似度
                similarity = self._calculate_text_similarity(text1, text2)
                row.append(similarity)

            matrix.append(row)

        return matrix

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 方法1: Jaccard相似度（基于词集）
        words1 = set(re.findall(r'\w+', text1))
        words2 = set(re.findall(r'\w+', text2))

        if not words1 or not words2:
            return 0.0

        jaccard = len(words1 & words2) / len(words1 | words2)

        # 方法2: 序列匹配（考虑顺序）
        seq_matcher = SequenceMatcher(None, text1, text2)
        sequence_ratio = seq_matcher.ratio()

        # 方法3: 子串包含
        if text1 in text2 or text2 in text1:
            containment = 1.0
        else:
            # 计算最长公共子串
            lcs_length = self._longest_common_substring_length(text1, text2)
            containment = 2 * lcs_length / (len(text1) + len(text2))

        # 综合三种方法
        similarity = (jaccard * 0.3 + sequence_ratio * 0.4 + containment * 0.3)

        return similarity

    def _longest_common_substring_length(self, s1: str, s2: str) -> int:
        """计算最长公共子串长度"""
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        max_length = 0

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    max_length = max(max_length, dp[i][j])
                else:
                    dp[i][j] = 0

        return max_length




