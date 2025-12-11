from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class SemanticCorrespondenceChecker:
    """基于语义相似度的对应关系判断"""

    def __init__(self, model_name: str = r'D:\pyworkplace\git_place\ai-ken\models\paraphrase-multilingual-MiniLM-L12-v2'):
        self.model = SentenceTransformer(model_name)

    def check_semantic_correspondence(self,
                                      chunk_list1: List[Dict],
                                      chunk_list2: List[Dict],
                                      similarity_threshold: float = 0.8) -> Dict:
        """
        基于语义相似度判断对应关系

        Args:
            chunk_list1: 第一个chunk列表
            chunk_list2: 第二个chunk列表
            similarity_threshold: 相似度阈值

        Returns:
            对应关系映射
        """
        # 提取文本
        texts1 = [self._extract_text(chunk) for chunk in chunk_list1]
        texts2 = [self._extract_text(chunk) for chunk in chunk_list2]

        # 获取嵌入向量
        embeddings1 = self.model.encode(texts1, convert_to_tensor=True)
        embeddings2 = self.model.encode(texts2, convert_to_tensor=True)

        # 计算相似度矩阵
        similarity_matrix = cosine_similarity(embeddings1.cpu().numpy(),
                                              embeddings2.cpu().numpy())

        correspondence = {
            "semantic_matches": [],
            "similarity_matrix": similarity_matrix.tolist(),
            "threshold_matches": []
        }

        # 寻找最佳匹配
        for i in range(len(chunk_list1)):
            chunk1_id = self._get_chunk_id(chunk_list1[i], i, prefix='chunk1')

            # 找到最相似的chunk2
            similarities = similarity_matrix[i]
            max_similarity = np.max(similarities)
            best_match_idx = np.argmax(similarities)

            if max_similarity >= similarity_threshold:
                chunk2_id = self._get_chunk_id(chunk_list2[best_match_idx],
                                               best_match_idx, prefix='chunk2')

                match_info = {
                    'chunk1_id': chunk1_id,
                    'chunk2_id': chunk2_id,
                    'similarity': float(max_similarity),
                    'chunk1_text': texts1[i][:100],  # 截断显示
                    'chunk2_text': texts2[best_match_idx][:100]
                }

                correspondence["semantic_matches"].append(match_info)

            # 记录所有超过阈值的匹配
            threshold_matches = []
            for j, similarity in enumerate(similarities):
                if similarity >= similarity_threshold:
                    chunk2_id = self._get_chunk_id(chunk_list2[j], j, prefix='chunk2')
                    threshold_matches.append({
                        'chunk2_id': chunk2_id,
                        'similarity': float(similarity)
                    })

            if threshold_matches:
                correspondence["threshold_matches"].append({
                    'chunk1_id': chunk1_id,
                    'matches': threshold_matches
                })

        # 统计信息
        total_chunks1 = len(chunk_list1)
        matched_count = len(correspondence["semantic_matches"])

        correspondence["stats"] = {
            "total_chunks1": total_chunks1,
            "total_chunks2": len(chunk_list2),
            "matched_count": matched_count,
            "match_rate": matched_count / total_chunks1 * 100 if total_chunks1 > 0 else 0,
            "avg_similarity": np.mean([m['similarity'] for m in correspondence["semantic_matches"]])
            if correspondence["semantic_matches"] else 0
        }

        return correspondence

    def _extract_text(self, chunk) -> str:
        """从chunk中提取文本"""
        if isinstance(chunk, str):
            return chunk
        elif isinstance(chunk, dict):
            return chunk.get('text', '')
        else:
            return str(chunk)

    def _get_chunk_id(self, chunk, index: int, prefix: str = 'chunk') -> str:
        """获取chunk ID"""
        if isinstance(chunk, dict) and 'chunk_id' in chunk:
            return chunk['chunk_id']
        else:
            return f'{prefix}_{index}'


if __name__ == '__main__':
    import os

    os.environ['HUGGINGFACE_CO_URL_HOME'] = "https://hf-mirror.com/"
    os.environ['_HF_DEFAULT_ENDPOINT'] = "https://hf-mirror.com/"
    _HF_DEFAULT_ENDPOINT = "https://hf-mirror.com"
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    os.environ['HF_HUB_OFFLINE'] = '0'  # 确保在线模式

    model = SentenceTransformer('BAAI/bge-reranker-base')
    model.save('./models/BAAI/bge-reranker-base')
