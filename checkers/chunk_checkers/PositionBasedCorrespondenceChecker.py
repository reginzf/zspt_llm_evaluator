from typing import List, Dict
class PositionBasedCorrespondenceChecker:
    """基于位置信息的对应关系判断"""

    def check_position_correspondence(self,
                                      chunk_list1: List[Dict],
                                      chunk_list2: List[Dict],
                                      original_text: str = None) -> Dict:
        """
        基于位置信息判断对应关系

        Args:
            chunk_list1: 包含start/end位置的chunk列表
            chunk_list2: 包含start/end位置的chunk列表
            original_text: 原始文本（可选）

        Returns:
            对应关系映射
        """
        # 确保chunk有位置信息
        chunk_list1 = self._add_position_info(chunk_list1, original_text)
        chunk_list2 = self._add_position_info(chunk_list2, original_text)

        correspondence = {
            "exact_matches": [],  # 完全匹配
            "partial_matches": [],  # 部分重叠
            "contained_matches": [],  # 包含关系
            "no_matches": []  # 无匹配
        }

        for i, chunk1 in enumerate(chunk_list1):
            chunk1_id = chunk1.get('chunk_id', f'chunk1_{i}')
            chunk1_start = chunk1['start']
            chunk1_end = chunk1['end']

            best_match = None
            best_overlap = 0
            match_type = None

            for j, chunk2 in enumerate(chunk_list2):
                chunk2_id = chunk2.get('chunk_id', f'chunk2_{j}')
                chunk2_start = chunk2['start']
                chunk2_end = chunk2['end']

                # 计算重叠
                overlap_start = max(chunk1_start, chunk2_start)
                overlap_end = min(chunk1_end, chunk2_end)

                if overlap_start < overlap_end:  # 有重叠
                    overlap_length = overlap_end - overlap_start
                    chunk1_length = chunk1_end - chunk1_start
                    chunk2_length = chunk2_end - chunk2_start

                    # 计算重叠比例
                    overlap_ratio1 = overlap_length / chunk1_length
                    overlap_ratio2 = overlap_length / chunk2_length

                    # 判断匹配类型
                    if overlap_ratio1 == 1.0 and overlap_ratio2 == 1.0:
                        # 完全匹配
                        current_match_type = 'exact'
                        current_overlap = 1.0
                    elif overlap_ratio1 == 1.0 or overlap_ratio2 == 1.0:
                        # 包含关系
                        current_match_type = 'contained'
                        current_overlap = max(overlap_ratio1, overlap_ratio2)
                    else:
                        # 部分重叠
                        current_match_type = 'partial'
                        current_overlap = (overlap_ratio1 + overlap_ratio2) / 2

                    if current_overlap > best_overlap:
                        best_overlap = current_overlap
                        best_match = {
                            'chunk1_id': chunk1_id,
                            'chunk2_id': chunk2_id,
                            'overlap_ratio': current_overlap,
                            'overlap_length': overlap_length,
                            'chunk1_ratio': overlap_ratio1,
                            'chunk2_ratio': overlap_ratio2
                        }
                        match_type = current_match_type

            if best_match:
                if match_type == 'exact':
                    correspondence["exact_matches"].append(best_match)
                elif match_type == 'contained':
                    correspondence["contained_matches"].append(best_match)
                else:
                    correspondence["partial_matches"].append(best_match)
            else:
                correspondence["no_matches"].append({
                    'chunk_id': chunk1_id,
                    'start': chunk1_start,
                    'end': chunk1_end
                })

        # 计算统计信息
        total_chunks = len(chunk_list1)
        correspondence["stats"] = {
            "total_chunks": total_chunks,
            "exact_matches": len(correspondence["exact_matches"]),
            "contained_matches": len(correspondence["contained_matches"]),
            "partial_matches": len(correspondence["partial_matches"]),
            "no_matches": len(correspondence["no_matches"]),
            "match_rate": (total_chunks - len(correspondence["no_matches"])) / total_chunks * 100
        }

        return correspondence

    def _add_position_info(self, chunk_list: List[Dict], original_text: str = None) -> List[Dict]:
        """为chunk添加位置信息"""
        if not original_text:
            return chunk_list

        result = []
        current_pos = 0

        for i, chunk in enumerate(chunk_list):
            if isinstance(chunk, str):
                text = chunk
            else:
                text = chunk.get('text', '')

            # 在原始文本中查找
            if text and original_text:
                # 简单查找（可优化为模糊匹配）
                start = original_text.find(text, current_pos)
                if start == -1:
                    start = current_pos

                end = start + len(text)
                current_pos = end
            else:
                start = chunk.get('start', 0)
                end = chunk.get('end', len(text))

            if isinstance(chunk, dict):
                chunk_copy = chunk.copy()
            else:
                chunk_copy = {}

            chunk_copy.update({
                'text': text,
                'start': start,
                'end': end,
                'chunk_id': chunk_copy.get('chunk_id', f'chunk_{i}'),
                'length': len(text)
            })

            result.append(chunk_copy)

        return result
