#!/bin/bash
# AI-KEN 生产环境一键部署脚本
# 功能：前端构建 → 上传到服务器 → 远端代码同步 → 验证
#
# 使用方法：
#   bash scripts/deploy_prod.sh
#
# 依赖：
#   - ssh/scp（或 sshpass）：用于连接服务器
#   - npm：用于前端构建
#   - sshpass：免密 SSH（brew install sshpass / apt install sshpass）

set -e  # 遇到错误立即退出

# ============================================================
# 配置
# ============================================================
REMOTE_HOST="10.210.2.223"
REMOTE_USER="root"
REMOTE_PASS="admin@123"
REMOTE_PROJECT="/root/zlzspt_chunk"
REMOTE_FRONTEND="/var/www/ai-ken"

FRONTEND_DIR="$(cd "$(dirname "$0")/../frontend" && pwd)"
DIST_DIR="$FRONTEND_DIR/dist"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "${BLUE}[STEP]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_fail()  { echo -e "${RED}[FAIL]${NC}  $1"; }

# SSH 命令封装（带超时，绕过代理访问本机）
ssh_run() {
    sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no \
        "$REMOTE_USER@$REMOTE_HOST" "$@"
}

# 上传封装：优先 rsync，降级到 tar+ssh
scp_upload() {
    local src="$1"
    local dst="$2"
    if command -v rsync &>/dev/null; then
        sshpass -p "$REMOTE_PASS" rsync -az --delete \
            -e "ssh -o StrictHostKeyChecking=no" \
            "$src" "$REMOTE_USER@$REMOTE_HOST:$dst"
    else
        tar -C "$src" -czf - . | \
            sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no \
            "$REMOTE_USER@$REMOTE_HOST" "tar -xzf - -C $dst"
    fi
}

# 检查依赖
check_deps() {
    log_step "检查本地依赖..."
    local missing=()
    for cmd in npm sshpass ssh scp; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "缺少依赖命令: ${missing[*]}"
        log_error "sshpass 安装: brew install sshpass (macOS) / apt install sshpass (Ubuntu)"
        exit 1
    fi
    log_info "依赖检查通过"
}

# ============================================================
# 步骤 1：构建前端
# ============================================================
build_frontend() {
    log_step "步骤 1/4：构建前端..."

    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "前端目录不存在: $FRONTEND_DIR"
        exit 1
    fi

    cd "$FRONTEND_DIR"

    # 清理上次构建
    if [ -d "dist" ]; then
        log_info "清理旧 dist 目录..."
        rm -rf dist
    fi

    # 安装依赖（如果 node_modules 不存在）
    if [ ! -d "node_modules" ]; then
        log_info "安装 npm 依赖..."
        npm install
    fi

    # 构建
    log_info "执行 npm run build-only..."
    npm run build-only

    if [ ! -f "dist/index.html" ]; then
        log_error "构建失败：dist/index.html 不存在"
        exit 1
    fi

    log_info "前端构建成功，输出目录: $DIST_DIR"
    cd - > /dev/null
}

# ============================================================
# 步骤 2：上传前端到服务器
# ============================================================
upload_frontend() {
    log_step "步骤 2/4：上传前端到服务器 $REMOTE_HOST:$REMOTE_FRONTEND ..."

    # 清理远端目录
    log_info "清理远端 $REMOTE_FRONTEND ..."
    ssh_run "rm -rf ${REMOTE_FRONTEND:?}/* && echo '远端清理完成'"

    # 上传 dist 内容
    log_info "上传 dist/ 到远端..."
    scp_upload "$DIST_DIR/" "$REMOTE_FRONTEND/"

    # 修复文件权限（确保 nginx 可读取）
    log_info "修复文件权限..."
    ssh_run "chown -R root:root $REMOTE_FRONTEND && chmod -R 755 $REMOTE_FRONTEND"

    # 验证上传
    local remote_index
    remote_index=$(ssh_run "test -f $REMOTE_FRONTEND/index.html && echo 'ok' || echo 'missing'")
    if [ "$remote_index" = "ok" ]; then
        log_info "前端文件上传成功"
    else
        log_error "上传验证失败：$REMOTE_FRONTEND/index.html 不存在"
        exit 1
    fi
}

# ============================================================
# 步骤 3：远端执行 sync_code.sh
# ============================================================
sync_remote() {
    log_step "步骤 3/4：远端执行 sync_code.sh ..."

    ssh_run "cd $REMOTE_PROJECT && bash scripts/sync_code.sh"

    log_info "远端同步完成"
}

# ============================================================
# 步骤 4：验证服务状态
# ============================================================
verify_services() {
    log_step "步骤 4/4：验证服务状态..."
    echo ""

    # 等待服务启动
    sleep 3

    local backend_ok=true
    local frontend_ok=true
    local all_ok=true

    # 检查服务 systemd 状态
    log_info "--- Systemd 服务状态 ---"
    local backend_active
    backend_active=$(ssh_run "systemctl is-active ai-ken-backend 2>/dev/null || echo 'inactive'")
    local nginx_active
    nginx_active=$(ssh_run "systemctl is-active nginx 2>/dev/null || echo 'inactive'")

    if [ "$backend_active" = "active" ]; then
        log_ok "ai-ken-backend: active"
    else
        log_fail "ai-ken-backend: $backend_active"
        backend_ok=false
        all_ok=false
    fi

    if [ "$nginx_active" = "active" ]; then
        log_ok "nginx: active"
    else
        log_fail "nginx: $nginx_active"
        frontend_ok=false
        all_ok=false
    fi

    echo ""
    log_info "--- HTTP 路由验证 ---"

    # 验证路由列表：[描述, URL]
    local routes=(
        "Nginx健康检查|http://10.210.2.223:5002/health"
        "前端首页|http://10.210.2.223:5002/"
        "API-QA数据组列表|http://10.210.2.223:5002/api/qa/groups"
        "API-LLM模型列表|http://10.210.2.223:5002/api/llm/models"
        "API-知识库列表|http://10.210.2.223:5002/api/local_knowledge/list/"
        "API-Label Studio环境|http://10.210.2.223:5002/api/label_studio_env/list/"
        "API-环境列表|http://10.210.2.223:5002/api/environment/list/"
        "API-报告列表|http://10.210.2.223:5002/api/report_list/list/"
    )

    local pass=0
    local fail=0

    for route in "${routes[@]}"; do
        local name="${route%%|*}"
        local url="${route##*|}"
        local code
        # 在远端执行 curl，绕过代理
        code=$(ssh_run "no_proxy=127.0.0.1,10.210.2.223 curl -s --max-time 8 -o /dev/null -w '%{http_code}' '$url'" 2>/dev/null || echo "000")
        if [[ "$code" =~ ^[23] ]]; then
            log_ok "$name -> $code"
            ((pass++))
        else
            log_fail "$name -> $code ($url)"
            ((fail++))
            all_ok=false
        fi
    done

    echo ""
    log_info "--- 验证结果 ---"
    log_info "通过: $pass  失败: $fail"

    if $all_ok; then
        echo -e "\n${GREEN}✓ 部署成功！所有服务和路由正常${NC}"
        echo -e "${GREEN}  前端访问地址: http://10.210.2.223:5002${NC}\n"
    else
        echo -e "\n${YELLOW}⚠ 部署完成，但有部分验证失败，请检查上方日志${NC}\n"
        return 1
    fi
}

# ============================================================
# 主流程
# ============================================================
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   AI-KEN 生产部署 - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}   目标: $REMOTE_USER@$REMOTE_HOST${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    check_deps
    build_frontend
    upload_frontend
    sync_remote
    verify_services

    exit $?
}

main "$@"
