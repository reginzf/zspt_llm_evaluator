from typing import List, Dict
from difflib import SequenceMatcher
import re
import numpy as np


class AlignmentBasedChecker:
    """基于对齐算法的对应关系判断"""

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

    def _extract_text(self, chunk) -> str:
        if isinstance(chunk, str):
            return chunk
        elif isinstance(chunk, dict):
            return chunk.get('text', '')
        return ''

    def _get_chunk_id(self, chunk, index: int) -> str:
        if isinstance(chunk, dict) and 'chunk_id' in chunk:
            return chunk['chunk_id']
        return f'chunk_{index}'
