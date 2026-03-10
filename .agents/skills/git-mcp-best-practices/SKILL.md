---
name: git-mcp-best-practices
description: 基于 Git MCP 的 Git 操作最佳实践指南。使用场景：(1) 查看仓库状态、提交历史、分支信息，(2) 执行代码提交、分支切换、创建新分支，(3) 对比变更、审查代码差异，(4) 解决合并冲突、回滚提交，(5) 生成规范的提交信息，(6) 执行 Git Flow / GitHub Flow 工作流。集成 Git MCP 工具，遵循 Conventional Commits 规范，提供结构化的 Git 操作流程。
---

# Git MCP 最佳实践

基于 Git MCP Server 的 Git 操作指南，整合 Conventional Commits 规范和常用 Git 工作流。

## 🚀 快速开始

### 常用操作速查

| 操作 | MCP 命令 | 说明 |
|------|---------|------|
| 查看状态 | `git_status` | 工作区变更、暂存区状态 |
| 查看差异 | `git_diff_unstaged` / `git_diff_staged` | 未暂存/已暂存变更 |
| 提交代码 | `git_add` → `git_commit` | 暂存后提交 |
| 查看历史 | `git_log` | 提交历史记录 |
| 切换分支 | `git_checkout` | 切换到指定分支 |
| 创建分支 | `git_create_branch` | 基于当前分支创建 |
| 查看分支 | `git_branch` | 列出所有分支 |

---

## 📋 核心工作流程

### 1. 日常提交流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. 查看当前状态                                               │
│     git_status({ repo_path: "." })                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  2. 查看变更详情（如有未暂存文件）                              │
│     git_diff_unstaged({ repo_path: "." })                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  3. 暂存变更                                                   │
│     git_add({ repo_path: ".", files: ["file1", "file2"] })    │
│     # 或暂存所有: files: ["."]                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  4. 确认暂存内容                                               │
│     git_diff_staged({ repo_path: "." })                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  5. 提交（使用规范格式）                                        │
│     git_commit({ repo_path: ".", message: "feat: xxx" })      │
└─────────────────────────────────────────────────────────────┘
```

### 2. 提交信息规范 (Conventional Commits)

#### 格式模板

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加用户登录功能` |
| `fix` | 修复 Bug | `fix: 修复登录验证失败问题` |
| `docs` | 文档变更 | `docs: 更新 API 文档` |
| `style` | 代码格式 | `style: 格式化代码缩进` |
| `refactor` | 重构 | `refactor: 重构用户服务层` |
| `perf` | 性能优化 | `perf: 优化数据库查询` |
| `test` | 测试相关 | `test: 添加单元测试` |
| `chore` | 构建/工具 | `chore: 更新依赖包` |
| `ci` | CI/CD | `ci: 配置 GitHub Actions` |
| `revert` | 回滚 | `revert: 回滚提交 abc123` |

#### Scope 范围（可选）

根据项目模块定义，例如：
- `frontend` - 前端代码
- `backend` - 后端代码
- `api` - API 接口
- `db` - 数据库
- `auth` - 认证模块

#### 完整示例

```
feat(auth): 添加 JWT 认证支持

- 实现 Token 生成和验证
- 添加登录/登出接口
- 配置拦截器验证 Token

Closes #123
```

---

## 🌿 分支管理

### Git Flow 工作流

```
main/master ──┬── v1.0.0 ──┬── v1.1.0 ──┬── v2.0.0
              │            │            │
develop ──────┴────────────┴────────────┘
              │
              ├── feature/login ────┤
              │                     │
              ├── feature/payment ──┤
              │                     │
              ├── release/v1.1.0 ───┴──┤
              │                        │
              └── hotfix/urgent ───────┴──┤
```

### 分支操作

#### 创建功能分支

```typescript
// 1. 确保在 develop 分支
await git_checkout({ repo_path: ".", branch_name: "develop" })

// 2. 创建并切换到新分支
await git_create_branch({ 
  repo_path: ".", 
  branch_name: "feature/user-auth",
  base_branch: "develop" 
})

// 3. 自动切换到新分支（部分 Git 版本需要手动切换）
await git_checkout({ repo_path: ".", branch_name: "feature/user-auth" })
```

#### 查看分支列表

```typescript
// 本地分支
await git_branch({ repo_path: ".", branch_type: "local" })

// 远程分支
await git_branch({ repo_path: ".", branch_type: "remote" })

// 所有分支
await git_branch({ repo_path: ".", branch_type: "all" })
```

#### 删除分支

**注意**: Git MCP 暂未提供直接删除分支的命令，需使用 Shell:

```powershell
# 删除本地分支（已合并）
git branch -d feature/xxx

# 强制删除本地分支
git branch -D feature/xxx

# 删除远程分支
git push origin --delete feature/xxx
```

---

## 🔍 代码审查与对比

### 查看变更

#### 未暂存变更（Working Directory）

```typescript
await git_diff_unstaged({ repo_path: ".", context_lines: 3 })
```

#### 已暂存变更（Staged）

```typescript
await git_diff_staged({ repo_path: ".", context_lines: 5 })
```

#### 指定文件对比

```typescript
// 查看特定文件的未暂存变更
await git_diff_unstaged({ 
  repo_path: ".", 
  context_lines: 3 
})
// 结果中会显示具体文件路径
```

### 提交历史查看

#### 基本日志

```typescript
await git_log({ repo_path: ".", max_count: 10 })
```

#### 时间范围过滤

```typescript
// 最近一周的提交
await git_log({ 
  repo_path: ".", 
  start_timestamp: "1 week ago",
  max_count: 50 
})

// 指定日期范围
await git_log({ 
  repo_path: ".", 
  start_timestamp: "2024-01-01",
  end_timestamp: "2024-01-31",
  max_count: 100 
})
```

#### 查看特定提交详情

```typescript
await git_show({ repo_path: ".", revision: "abc123" })

// 查看最新提交
await git_show({ repo_path: ".", revision: "HEAD" })
```

#### 分支对比

```typescript
// 查看 feature 分支比 develop 多哪些提交
await git_branch({ 
  repo_path: ".", 
  branch_type: "local",
  not_contains: "develop",
  contains: "feature/xxx"
})
```

---

## ↩️ 回滚与撤销

### 撤销操作速查表

| 场景 | Git 命令 | MCP 支持 |
|------|---------|---------|
| 撤销工作区修改 | `git checkout -- file` | ❌ 需 Shell |
| 取消暂存 | `git reset HEAD file` | ✅ `git_reset` |
| 修改上次提交 | `git commit --amend` | ❌ 需 Shell |
| 回滚到指定版本 | `git reset --hard` | ❌ 需 Shell |
| 查看历史 | `git log` | ✅ `git_log` |

### 取消暂存

```typescript
// 取消所有暂存
await git_reset({ repo_path: "." })

// 取消特定文件暂存（需 Shell）
// git reset HEAD filename
```

### 安全回滚（推荐方式）

**方式 1: 使用 revert（推荐，保留历史）**

```powershell
# 回滚指定提交，创建新的提交
git revert abc123

# 回滚多个提交
git revert abc123 def456

# 回滚但不自动提交（手动检查）
git revert -n abc123
```

**方式 2: 使用 reset（危险，会丢失历史）**

```powershell
# 软回滚（保留变更到暂存区）
git reset --soft HEAD~1

# 混合回滚（保留变更到工作区）
git reset --mixed HEAD~1

# 硬回滚（完全丢弃变更）⚠️ 危险！
git reset --hard HEAD~1
```

---

## 🔀 合并与冲突解决

### 合并流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. 切换到目标分支（如 develop）                               │
│     git_checkout({ repo_path: ".", branch_name: "develop" })  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  2. 拉取最新代码（如需要）                                     │
│     # 需 Shell: git pull origin develop                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  3. 合并功能分支                                               │
│     # 需 Shell: git merge feature/xxx                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  4. 如有冲突，解决后提交                                       │
│     git_add({ repo_path: ".", files: ["."] })                │
│     git_commit({ repo_path: ".", message: "merge: xxx" })     │
└─────────────────────────────────────────────────────────────┘
```

### 冲突解决标记

```typescript
// 查看当前状态，了解冲突文件
await git_status({ repo_path: "." })

// 解决冲突后查看差异
await git_diff_staged({ repo_path: "." })
```

**冲突文件格式**:
```
<<<<<<< HEAD
当前分支的内容
=======
合并分支的内容
>>>>>>> feature/xxx
```

**解决步骤**:
1. 打开冲突文件，搜索 `<<<<<<<`
2. 手动编辑，保留需要的代码
3. 删除冲突标记 (`<<<<<<<`, `=======`, `>>>>>>>`)
4. 暂存并提交

---

## 📝 完整操作示例

### 场景 1: 新功能开发

```typescript
// Step 1: 查看当前状态
await git_status({ repo_path: "." })

// Step 2: 切换到 develop 分支
await git_checkout({ repo_path: ".", branch_name: "develop" })

// Step 3: 创建功能分支
await git_create_branch({ 
  repo_path: ".", 
  branch_name: "feature/user-login",
  base_branch: "develop" 
})
await git_checkout({ repo_path: ".", branch_name: "feature/user-login" })

// Step 4: 开发完成后，查看变更
await git_status({ repo_path: "." })
await git_diff_unstaged({ repo_path: "." })

// Step 5: 暂存变更
await git_add({ repo_path: ".", files: ["."] })

// Step 6: 确认暂存内容
await git_diff_staged({ repo_path: "." })

// Step 7: 提交（使用规范格式）
await git_commit({ 
  repo_path: ".", 
  message: `feat(auth): 添加用户登录功能

- 实现用户名密码验证
- 添加 JWT Token 生成
- 配置登录接口路由

Closes #123` 
})

// Step 8: 查看提交历史
await git_log({ repo_path: ".", max_count: 5 })
```

### 场景 2: 紧急 Bug 修复

```typescript
// Step 1: 切换到 main 分支
await git_checkout({ repo_path: ".", branch_name: "main" })

// Step 2: 创建热修复分支
await git_create_branch({ 
  repo_path: ".", 
  branch_name: "hotfix/critical-bug",
  base_branch: "main" 
})
await git_checkout({ repo_path: ".", branch_name: "hotfix/critical-bug" })

// Step 3: 修复 Bug
// ... 修改代码 ...

// Step 4: 提交修复
await git_add({ repo_path: ".", files: ["bugfix-file.js"] })
await git_commit({ 
  repo_path: ".", 
  message: "fix(api): 修复关键 API 响应错误\n\n- 修复空指针异常\n- 添加参数校验" 
})

// Step 5: 查看提交
await git_show({ repo_path: ".", revision: "HEAD" })

// Step 6: 合并到 main 和 develop（需 Shell）
// git checkout main && git merge hotfix/critical-bug
// git checkout develop && git merge hotfix/critical-bug
// git branch -d hotfix/critical-bug
```

### 场景 3: 代码审查前的自查

```typescript
// Step 1: 查看当前分支
await git_branch({ repo_path: ".", branch_type: "local" })

// Step 2: 查看所有变更
await git_status({ repo_path: "." })

// Step 3: 对比目标分支的差异（需 Shell）
// git diff develop...feature/xxx

// Step 4: 查看提交历史
await git_log({ 
  repo_path: ".", 
  start_timestamp: "1 week ago",
  max_count: 20 
})

// Step 5: 检查每个提交详情
await git_show({ repo_path: ".", revision: "HEAD" })
await git_show({ repo_path: ".", revision: "HEAD~1" })
```

---

## 🛠️ 高级用法

### 提交信息模板

#### 功能提交
```
feat(<scope>): <简短描述>

- <变更点1>
- <变更点2>
- <变更点3>

Closes #<issue编号>
```

#### 修复提交
```
fix(<scope>): <修复的问题>

- <修复详情1>
- <修复详情2>

Fixes #<bug编号>
```

#### 重构提交
```
refactor(<scope>): <重构内容>

- <重构原因>
- <具体变更>

BREAKING CHANGE: <如有破坏性变更，说明影响>
```

### 批量操作

```typescript
// 暂存多个特定文件
await git_add({ 
  repo_path: ".", 
  files: ["src/api/user.ts", "src/components/Login.vue"] 
})

// 查看特定文件的提交历史（需 Shell）
// git log --follow -- src/api/user.ts
```

---

## ⚠️ 注意事项

### MCP 工具限制

| 功能 | 状态 | 替代方案 |
|------|------|---------|
| 推送代码 | ❌ | `git push` (Shell) |
| 拉取代码 | ❌ | `git pull` (Shell) |
| 删除分支 | ❌ | `git branch -d` (Shell) |
| 合并分支 | ❌ | `git merge` (Shell) |
| 变基 | ❌ | `git rebase` (Shell) |
| 查看远程 | ❌ | `git remote -v` (Shell) |
| 添加远程 | ❌ | `git remote add` (Shell) |
| 打标签 | ❌ | `git tag` (Shell) |

### 安全建议

1. **提交前检查**: 始终先 `git_diff_staged` 再提交
2. **分支确认**: 提交前用 `git_branch` 确认当前分支
3. **敏感信息**: 避免提交 `.env`, `config.json` 等包含密钥的文件
4. **大文件**: 不要提交日志、二进制大文件到 Git
5. **定期推送**: 重要变更及时推送到远程备份

### Windows 环境注意

```powershell
# 配置行尾符自动处理（推荐）
git config --global core.autocrlf true

# 配置默认编码为 UTF-8
git config --global core.quotepath off
git config --global i18n.logoutputencoding utf-8
git config --global i18n.commitencoding utf-8
```

---

## 📚 参考资源

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow 工作流](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Git 官方文档](https://git-scm.com/doc)
