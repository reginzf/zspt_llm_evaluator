import json
import logging

from typing import Dict, List, Any, Optional
from pathlib import Path
from env_config_init import CONFIG_PATH

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器 - 负责读取、验证和管理Agent配置"""

    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为configs/agent_config.json
        """
        if config_path is None:
            # 默认配置文件路径
            self.config_path = CONFIG_PATH / "agent_config.json"
        else:
            self.config_path = Path(config_path)

        self.config_data = {}
        self.agents_config = []
        self.evaluation_settings = {}

        # 加载配置
        self.load_config()

    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if not self.config_path.exists():
                logger.warning(f"配置文件不存在: {self.config_path}")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)

            # 验证配置结构
            if self._validate_config_structure():
                self.agents_config = self.config_data.get('agents', [])
                self.evaluation_settings = self.config_data.get('evaluation_settings', {})
                logger.info(f"成功加载配置文件: {self.config_path}")
                logger.info(f"  - 检测到 {len(self.agents_config)} 个Agent配置")
                logger.info(f"  - 评估设置已加载")
                return True
            else:
                logger.error("配置文件结构无效")
                return False

        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON格式错误: {e}")
            return False
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return False

    def _validate_config_structure(self) -> bool:
        """
        验证配置文件结构
        
        Returns:
            bool: 结构是否有效
        """
        required_keys = ['agents']

        for key in required_keys:
            if key not in self.config_data:
                logger.error(f"缺少必需的配置项: {key}")
                return False

        # 验证agents数组
        if not isinstance(self.config_data['agents'], list):
            logger.error("agents 必须是数组格式")
            return False

        # 验证每个agent配置
        for i, agent_config in enumerate(self.config_data['agents']):
            if not self._validate_agent_config(agent_config, i):
                return False

        return True

    def _validate_agent_config(self, agent_config: Dict, index: int) -> bool:
        """
        验证单个agent配置
        
        Args:
            agent_config: Agent配置字典
            index: 索引位置
            
        Returns:
            bool: 配置是否有效
        """
        required_fields = ['name', 'type', 'api_key']

        for field in required_fields:
            if field not in agent_config:
                logger.error(f"Agent[{index}] 缺少必需字段: {field}")
                return False

        # 验证API密钥格式（简单验证）
        if not agent_config['api_key'] or agent_config['api_key'].startswith('your-'):
            logger.warning(f"Agent[{index}] '{agent_config['name']}' API密钥可能未正确配置")

        return True

    def get_agents_config(self) -> List[Dict]:
        """
        获取所有Agent配置
        
        Returns:
            List[Dict]: Agent配置列表
        """
        return self.agents_config.copy()

    def get_agent_config(self, agent_name: str) -> Optional[Dict]:
        """
        根据名称获取特定Agent配置
        
        Args:
            agent_name: Agent名称
            
        Returns:
            Optional[Dict]: Agent配置或None
        """
        for config in self.agents_config:
            if config.get('name') == agent_name:
                return config.copy()
        return None

    def get_evaluation_settings(self) -> Dict:
        """
        获取评估设置
        
        Returns:
            Dict: 评估设置
        """
        return self.evaluation_settings.copy()
    
    def get_match_types(self) -> Dict:
        """
        获取匹配类型配置
        
        Returns:
            Dict: match_types 配置字典
        """
        return self.config_data.get('match_types', {}).copy()

    def add_agent(self, agent_config: Dict) -> bool:
        """
        添加新的Agent配置
        
        Args:
            agent_config: Agent配置字典
            
        Returns:
            bool: 添加是否成功
        """
        if not self._validate_agent_config(agent_config, len(self.agents_config)):
            return False

        self.agents_config.append(agent_config)
        self.config_data['agents'] = self.agents_config
        return True

    def update_agent(self, agent_name: str, updates: Dict) -> bool:
        """
        更新指定Agent配置
        
        Args:
            agent_name: Agent名称
            updates: 更新内容字典
            
        Returns:
            bool: 更新是否成功
        """
        for i, config in enumerate(self.agents_config):
            if config.get('name') == agent_name:
                self.agents_config[i].update(updates)
                self.config_data['agents'] = self.agents_config
                return True
        return False

    def remove_agent(self, agent_name: str) -> bool:
        """
        移除指定Agent配置
        
        Args:
            agent_name: Agent名称
            
        Returns:
            bool: 移除是否成功
        """
        for i, config in enumerate(self.agents_config):
            if config.get('name') == agent_name:
                self.agents_config.pop(i)
                self.config_data['agents'] = self.agents_config
                return True
        return False

    def save_config(self, backup: bool = True) -> bool:
        """
        保存配置到文件
        
        Args:
            backup: 是否创建备份
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if backup and self.config_path.exists():
                backup_path = self.config_path.with_suffix('.backup.json')
                import shutil
                shutil.copy2(self.config_path, backup_path)
                logger.info(f"已创建配置备份: {backup_path}")

            # 保存新配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)

            logger.info(f"配置已保存到: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def validate_all_configs(self) -> Dict[str, List[str]]:
        """
        验证所有配置的有效性
        
        Returns:
            Dict: 验证结果，包含errors和warnings
        """
        results = {
            'errors': [],
            'warnings': []
        }

        # 验证每个agent
        for i, agent_config in enumerate(self.agents_config):
            name = agent_config.get('name', f'Agent-{i}')

            # 检查API密钥
            api_key = agent_config.get('api_key', '')
            if not api_key or api_key.startswith('your-') or api_key.startswith('sk-your'):
                results['warnings'].append(f"{name}: API密钥未正确配置")

            # 检查必需字段
            required_fields = ['name', 'type', 'api_url']
            for field in required_fields:
                if field not in agent_config:
                    results['errors'].append(f"{name}: 缺少必需字段 '{field}'")

        return results
