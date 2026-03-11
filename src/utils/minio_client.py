"""
MinIO客户端工具类
用于处理文件上传、下载、删除等操作
"""
import os
import logging
from minio import Minio
from minio.error import S3Error
from typing import List, Optional
from env_config_init import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO文件存储客户端（基于bucket_name的单例模式）"""
    
    # 存储不同bucket_name的实例
    _instances = {}
    
    def __new__(cls, endpoint: str = None, access_key: str = None, 
                secret_key: str = None, bucket_name: str = None):
        """
        创建类实例的工厂方法，实现基于bucket_name的单例模式
        
        通过bucket_name作为唯一标识符，确保每个存储桶只有一个客户端实例存在。
        
        Args:
            endpoint: MinIO服务地址
            access_key: 访问密钥
            secret_key: 秘密密钥
            bucket_name: 存储桶名称，如果为None则使用settings中的默认值
            
        Returns:
            MinIOClient: 返回类的单例实例
        """
        # 如果没有指定bucket_name，使用settings中的默认值
        if bucket_name is None:
            bucket_name = settings.MINIO_BUCKET_NAME
        
        # 使用bucket_name作为唯一标识符
        key = bucket_name
        if key not in cls._instances:
            cls._instances[key] = super(MinIOClient, cls).__new__(cls)
        return cls._instances[key]
    
    def __init__(self, endpoint: str = None, access_key: str = None, 
                 secret_key: str = None, bucket_name: str = None):
        """
        初始化MinIO客户端
        
        Args:
            endpoint: MinIO服务地址 (如: "10.210.2.223:9000")
            access_key: 访问密钥
            secret_key: 秘密密钥
            bucket_name: 存储桶名称
        """
        # 避免重复初始化
        if hasattr(self, 'endpoint'):
            return
        
        # 从settings配置文件获取MinIO配置
        self.endpoint = endpoint or settings.MINIO_ENDPOINT
        self.access_key = access_key or settings.MINIO_ACCESS_KEY
        self.secret_key = secret_key or settings.MINIO_SECRET_KEY
        self.bucket_name = bucket_name or settings.MINIO_BUCKET_NAME
        self.secure = settings.MINIO_SECURE
        
        # 初始化客户端
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        # 确保存储桶存在
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在，不存在则创建"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"创建存储桶: {self.bucket_name}")
            else:
                logger.info(f"存储桶已存在: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"检查/创建存储桶失败: {e}")
            raise
    
    def upload_file(self, local_file_path: str, object_name: str = None) -> bool:
        """
        上传文件到MinIO
        
        Args:
            local_file_path: 本地文件路径
            object_name: 对象名称（在MinIO中的文件名），如果为None则使用原文件名
            
        Returns:
            bool: 上传成功返回True
        """
        try:
            if not os.path.exists(local_file_path):
                logger.error(f"本地文件不存在: {local_file_path}")
                return False
            
            if object_name is None:
                object_name = os.path.basename(local_file_path)
            
            # 上传文件
            self.client.fput_object(
                self.bucket_name,
                object_name,
                local_file_path
            )
            
            logger.info(f"文件上传成功: {local_file_path} -> {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"文件上传失败: {e}")
            return False
        except Exception as e:
            logger.error(f"上传过程中发生错误: {e}")
            return False
    
    def upload_multiple_files(self, file_paths: List[str], prefix: str = "") -> List[str]:
        """
        批量上传文件
        
        Args:
            file_paths: 本地文件路径列表
            prefix: 对象名称前缀
            
        Returns:
            List[str]: 成功上传的文件对象名称列表
        """
        uploaded_files = []
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                object_name = prefix + os.path.basename(file_path)
                if self.upload_file(file_path, object_name):
                    uploaded_files.append(object_name)
            else:
                logger.warning(f"文件不存在，跳过上传: {file_path}")
        
        logger.info(f"批量上传完成，成功上传 {len(uploaded_files)} 个文件")
        return uploaded_files
    
    def download_file(self, object_name: str, local_file_path: str) -> bool:
        """
        从MinIO下载文件
        
        Args:
            object_name: 对象名称
            local_file_path: 本地保存路径
            
        Returns:
            bool: 下载成功返回True
        """
        try:
            # 确保本地目录存在
            local_dir = os.path.dirname(local_file_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            
            # 下载文件
            self.client.fget_object(
                self.bucket_name,
                object_name,
                local_file_path
            )
            
            logger.info(f"文件下载成功: {object_name} -> {local_file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"文件下载失败: {e}")
            return False
        except Exception as e:
            logger.error(f"下载过程中发生错误: {e}")
            return False
    
    def get_file_content(self, object_name: str) -> bytes:
        """
        从MinIO获取文件内容（直接读取到内存）
        
        Args:
            object_name: 对象名称
            
        Returns:
            bytes: 文件内容，失败返回None
        """
        try:
            # 获取对象
            response = self.client.get_object(self.bucket_name, object_name)
            # 读取内容
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"文件内容获取成功: {object_name}, 大小: {len(data)} bytes")
            return data
            
        except S3Error as e:
            logger.error(f"获取文件内容失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取文件内容过程中发生错误: {e}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """
        删除MinIO中的文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 删除成功返回True
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"文件删除成功: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"文件删除失败: {e}")
            return False
        except Exception as e:
            logger.error(f"删除过程中发生错误: {e}")
            return False
    
    def delete_multiple_files(self, object_names: List[str]) -> int:
        """
        批量删除文件
        
        Args:
            object_names: 对象名称列表
            
        Returns:
            int: 成功删除的文件数量
        """
        deleted_count = 0
        
        try:
            # MinIO支持批量删除
            errors = self.client.remove_objects(self.bucket_name, object_names)
            
            # 检查是否有错误
            error_count = 0
            for error in errors:
                logger.error(f"删除文件失败: {error}")
                error_count += 1
            
            deleted_count = len(object_names) - error_count
            logger.info(f"批量删除完成，成功删除 {deleted_count} 个文件")
            
        except Exception as e:
            logger.error(f"批量删除过程中发生错误: {e}")
        
        return deleted_count
    
    def list_files(self, prefix: str = "", recursive: bool = True) -> List[dict]:
        """
        列出存储桶中的文件
        
        Args:
            prefix: 文件前缀过滤
            recursive: 是否递归列出
            
        Returns:
            List[dict]: 文件信息列表
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            
            file_list = []
            for obj in objects:
                file_info = {
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag
                }
                file_list.append(file_info)
            
            logger.info(f"列出文件完成，共 {len(file_list)} 个文件")
            return file_list
            
        except S3Error as e:
            logger.error(f"列出文件失败: {e}")
            return []
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        获取文件的临时访问URL
        
        Args:
            object_name: 对象名称
            expires: 过期时间（秒）
            
        Returns:
            Optional[str]: 临时URL，失败返回None
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires
            )
            return url
        except S3Error as e:
            logger.error(f"获取文件URL失败: {e}")
            return None
    
    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 文件存在返回True
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False




def upload_local_file_to_minio(local_file_path: str, object_name: str = None, bucket_name: str = None) -> bool:
    """
    上传本地文件到MinIO的便捷函数
    
    Args:
        local_file_path: 本地文件路径
        object_name: 对象名称
        bucket_name: 存储桶名称，如果为None则使用settings中的默认值
        
    Returns:
        bool: 上传成功返回True
    """
    client = MinIOClient(bucket_name=bucket_name)
    return client.upload_file(local_file_path, object_name)


def download_minio_file_to_local(object_name: str, local_file_path: str, bucket_name: str = None) -> bool:
    """
    从MinIO下载文件到本地的便捷函数
    
    Args:
        object_name: 对象名称
        local_file_path: 本地文件路径
        bucket_name: 存储桶名称，如果为None则使用settings中的默认值
        
    Returns:
        bool: 下载成功返回True
    """
    client = MinIOClient(bucket_name=bucket_name)
    return client.download_file(object_name, local_file_path)


# 特定用途的存储桶客户端获取函数
def get_knowledge_files_client() -> MinIOClient:
    """获取知识库文档存储桶客户端"""
    return MinIOClient(bucket_name="knowledge-files")


def get_qa_raw_files_client() -> MinIOClient:
    """获取问答对原始文件存储桶客户端"""
    return MinIOClient(bucket_name="qa-raw-files")


def get_knowledge_report_client() -> MinIOClient:
    """获取知识库报告存储桶客户端"""
    return MinIOClient(bucket_name="knowledge-reports")


def get_llm_evaluation_client() -> MinIOClient:
    """获取LLM评估报告存储桶客户端"""
    return MinIOClient(bucket_name="llm-evaluation-reports")


def get_all_clients_info() -> dict:
    """获取所有已创建的客户端信息"""
    return {bucket: f"{client.endpoint}/{bucket}" for bucket, client in MinIOClient._instances.items()}