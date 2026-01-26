# 项目初始化脚本说明

本项目提供了四个初始化脚本，分别适用于不同的操作系统环境：

## 脚本介绍

### init_project.ps1 / init_project_ascii.ps1
- **适用系统**：Windows PowerShell
- **功能**：自动化完成项目环境配置和初始化
- **依赖文件**：使用 [requirements.txt](file:///D:/pyworkplace/git_place/ai-ken/requirements.txt)（包含`psycopg2-binary`）
- **使用方式**：在PowerShell中执行

### init_project.sh / init_project_ascii.sh  
- **适用系统**：Linux/macOS bash
- **功能**：自动化完成项目环境配置和初始化
- **依赖文件**：
  - CentOS系统：使用 [requirements_centos.txt](file:///D:/pyworkplace/git_place/ai-ken/requirements_centos.txt)（包含`psycopg2`）
  - 其他Linux/macOS系统：使用 [requirements.txt](file:///D:/pyworkplace/git_place/ai-ken/requirements.txt)（包含`psycopg2-binary`）
- **特殊功能**：自动检测并安装符合要求的Python版本（3.10+）
- **使用方式**：在终端中执行

## 使用方法

### Windows (PowerShell)
```powershell
# 进入项目目录
cd /path/to/project

# 执行初始化脚本
.\init_project.ps1
```

### Linux/macOS (bash)
```bash
# 进入项目目录
cd /path/to/project

# 给脚本执行权限
chmod +x init_project.sh

# 执行初始化脚本
./init_project.sh
```

## 功能说明

1. **环境检查**：验证Python版本（3.10+）及必要文件
2. **自动Python安装**：如果检测到Python版本低于要求，自动在Linux系统上安装Python 3.10
3. **交互式配置**：引导用户输入数据库、路径、API等配置信息
4. **虚拟环境设置**：创建并激活Python虚拟环境
5. **依赖安装**：根据操作系统和环境安装所需包
6. **配置文件生成**：创建configs/settings.toml配置文件
7. **数据库初始化**：运行数据库创建脚本

## 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| SQL_HOST | 数据库主机地址 | localhost |
| SQL_PORT | 数据库端口 | 5432 |
| SQL_DB | 数据库名称 | label_studio |
| SQL_USER | 数据库用户名 | labelstudio |
| KNOWLEDGE_LOCAL_PATH | 知识文件存储路径 | ./data/knowledge |
| MODEL_PATH | 模型文件存储路径 | ./models |
| OVERLAP_THRESHOLD | 重叠阈值 | 0.8 |
| SIMILARITY_THRESHOLD | 相似度阈值 | 0.7 |
| SEMANTIC_WEIGHT | 语义权重 | 0.9 |
| TOP_K | 返回结果数量 | [1,3,5,10] |
| DEEPSEEK_API_KEY | DeepSeek API密钥 | - |
| DEEPSEEK_API_BASE | API基础地址 | https://api.deepseek.com |
| MODEL_NAME | 使用的模型名称 | deepseek-chat |

## 注意事项

1. 确保在项目根目录下执行脚本
2. 需要网络连接以下载依赖包
3. 数据库服务需提前安装并启动
4. API密钥需要从相应平台获取
5. 模型文件需要从指定位置下载
6. 脚本会根据操作系统智能选择适当的依赖文件
7. 在Linux系统上，如果Python版本低于3.10，脚本将自动安装Python 3.10