#!/bin/bash
# AI-KEN CentOS 一键初始化脚本
# 目标平台: CentOS / RHEL 9 / Rocky Linux 9
# 使用方法: bash scripts/setup_centos.sh
# 注意: 上传前必须用 dos2unix 转换行尾为 LF

set -uo pipefail

# ── 颜色 ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { printf "${GREEN}[INFO]${NC}  %s\n" "$1"; }
log_warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$1"; }
log_error() { printf "${RED}[ERROR]${NC} %s\n" "$1"; }
log_step()  { printf "${BLUE}[STEP]${NC}  %s\n" "$1"; }
log_ok()    { printf "${GREEN}[OK]${NC}    %s\n" "$1"; }
log_fail()  { printf "${RED}[FAIL]${NC}  %s\n" "$1"; }

# ── 路径 ──────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$PROJECT_ROOT/.setup_state"

log_info "PROJECT_ROOT: $PROJECT_ROOT"

# ── 状态文件工具 ──────────────────────────────────────────────────
# 初始化状态文件（若不存在）
init_state() {
    if [ ! -f "$STATE_FILE" ]; then
        touch "$STATE_FILE"
        echo 'COMPLETED_STEPS=""' >> "$STATE_FILE"
    fi
    # shellcheck source=/dev/null
    source "$STATE_FILE"
    COMPLETED_STEPS="${COMPLETED_STEPS:-}"
}

# 持久化单个变量到状态文件（先删旧行再追加）
save_var() {
    local key="$1"
    local val="$2"
    grep -v "^${key}=" "$STATE_FILE" > "${STATE_FILE}.tmp" || true
    mv "${STATE_FILE}.tmp" "$STATE_FILE"
    printf '%s="%s"\n' "$key" "$val" >> "$STATE_FILE"
    # 同步到当前 shell（使用 printf -v 避免 eval 注入风险）
    printf -v "$key" '%s' "$val"
}

# 标记步骤完成
mark_done() {
    local step="$1"
    COMPLETED_STEPS="$COMPLETED_STEPS $step"
    grep -v '^COMPLETED_STEPS=' "$STATE_FILE" > "${STATE_FILE}.tmp" || true
    mv "${STATE_FILE}.tmp" "$STATE_FILE"
    printf 'COMPLETED_STEPS="%s"\n' "$COMPLETED_STEPS" >> "$STATE_FILE"
}

# 判断步骤是否已完成
is_done() {
    echo "${COMPLETED_STEPS:-}" | grep -qw "$1"
}

# ── 变量收集（启动阶段，所有步骤共用）────────────────────────────
collect_inputs() {
    # 若已有变量（断点续跑）则跳过询问
    PYTHON_BIN="${PYTHON_BIN:-}"
    FRONTEND_PORT="${FRONTEND_PORT:-}"
    BACKEND_PORT="${BACKEND_PORT:-}"

    if [ -z "$PYTHON_BIN" ] && [ -z "$FRONTEND_PORT" ] && [ -z "$BACKEND_PORT" ]; then
        log_step "配置信息收集"
        printf "\n"

        printf "请输入 Python 3.12 可执行路径（留空则自动下载编译安装）: "
        read -r input_python
        save_var PYTHON_BIN "$input_python"

        printf "前端端口（默认 5002）: "
        read -r input_fe
        save_var FRONTEND_PORT "${input_fe:-5002}"

        printf "后端端口（默认 5001）: "
        read -r input_be
        save_var BACKEND_PORT "${input_be:-5001}"

        printf "\n"
        log_info "配置已保存到 $STATE_FILE"
    else
        log_info "使用已保存配置: Python=${PYTHON_BIN:-<自动安装>}, 前端端口=$FRONTEND_PORT, 后端端口=$BACKEND_PORT"
    fi
}

# ── Wheel 文件提示（每次启动都执行）──────────────────────────────
prompt_wheels() {
    # 动态从 requirements 文件中提取 file:// 条目的文件名
    local req_file="$PROJECT_ROOT/scripts/requirements_centos.txt"
    local wheel_files
    wheel_files=$(grep 'file:///' "$req_file" | sed 's|.*file:///||;s|#.*||' | awk -F'/' '{print $NF}' | tr -d ' ')

    printf "\n"
    log_info "requirements_centos.txt 中有以下本地 wheel 文件依赖，请确认已放置到以下位置之一："
    printf "  - %s/scripts/wheels/  （推荐）\n" "$PROJECT_ROOT"
    printf "  - %s/models/\n" "$PROJECT_ROOT"
    printf "  - /tmp/\n\n"
    printf "需要的文件:\n"
    while IFS= read -r whl; do
        [ -z "$whl" ] && continue
        printf "  - %s\n" "$whl"
    done <<< "$wheel_files"
    printf "\n按 Enter 继续，或 Ctrl+C 退出后上传文件..."
    read -r
    printf "\n"
}

step_python() {
    is_done "step_python" && log_info "step_python 已完成，跳过" && return 0
    log_step "步骤 1/8: Python 环境确认"

    if [ -n "$PYTHON_BIN" ]; then
        # 用户指定路径：验证版本
        if ! "$PYTHON_BIN" --version 2>&1 | grep -q '3\.12'; then
            log_error "指定的 Python 路径版本不是 3.12: $PYTHON_BIN"
            log_error "请删除 .setup_state 并重新运行，或手动修改其中的 PYTHON_BIN"
            return 1
        fi
        log_ok "Python 验证通过: $($PYTHON_BIN --version 2>&1)"
    else
        # 自动下载编译
        log_info "开始安装编译依赖..."
        yum install -y gcc make openssl-devel bzip2-devel libffi-devel \
            zlib-devel wget xz-devel sqlite-devel || {
            log_error "yum 安装编译依赖失败"
            return 1
        }

        local tgz="/tmp/Python-3.12.5.tgz"
        if [ ! -f "$tgz" ]; then
            log_info "下载 Python 3.12.5 源码..."
            wget -q --show-progress \
                https://www.python.org/ftp/python/3.12.5/Python-3.12.5.tgz \
                -O "$tgz" || {
                log_error "下载失败！请手动将 Python-3.12.5.tgz 放置到 /tmp/ 后重新运行"
                return 1
            }
        else
            log_info "发现已有 $tgz，跳过下载"
        fi

        log_info "解压源码..."
        tar -xzf "$tgz" -C /tmp/ || { log_error "解压失败，tgz 文件可能损坏"; return 1; }

        log_info "编译配置（约需 10-20 分钟）..."
        (
            cd /tmp/Python-3.12.5 || { log_error "无法进入源码目录"; exit 1; }
            ./configure --enable-optimizations --prefix=/usr/local || { log_error "configure 失败"; exit 1; }
            log_info "编译中（使用 $(nproc) 核心）..."
            make -j"$(nproc)" || { log_error "make 失败"; exit 1; }
            log_info "安装..."
            make altinstall || { log_error "make altinstall 失败"; exit 1; }
        ) || return 1

        save_var PYTHON_BIN "/usr/local/bin/python3.12"
        log_ok "Python 安装完成: $($PYTHON_BIN --version 2>&1)"
    fi

    mark_done "step_python"
}

step_venv() {
    is_done "step_venv" && log_info "step_venv 已完成，跳过" && return 0
    log_step "步骤 2/8: 创建 Python venv"

    local venv_dir="$PROJECT_ROOT/venv"

    if [ -d "$venv_dir" ]; then
        log_info "venv 已存在，跳过创建"
    else
        "$PYTHON_BIN" -m venv "$venv_dir" || {
            log_error "venv 创建失败"
            return 1
        }
        log_ok "venv 创建成功: $venv_dir"
    fi

    # 导出 pip/python 路径供后续步骤使用
    PIP="$venv_dir/bin/pip"
    PYTHON="$venv_dir/bin/python"
    log_info "pip: $PIP"

    mark_done "step_venv"
}

# 在多个目录中按优先级查找 wheel 文件，找到则输出绝对路径，找不到返回 1
find_wheel() {
    local filename="$1"
    shift
    local search_dirs=("$@")
    for dir in "${search_dirs[@]}"; do
        local candidate="$dir/$filename"
        if [ -f "$candidate" ]; then
            echo "$(cd "$dir" && pwd)/$(basename "$filename")"
            return 0
        fi
    done
    return 1
}

step_wheels() {
    is_done "step_wheels" && log_info "step_wheels 已完成，跳过" && return 0
    log_step "步骤 3/8: 修复 requirements 中的 file:// 路径"

    local req_src="$PROJECT_ROOT/scripts/requirements_centos.txt"
    local req_dst="$PROJECT_ROOT/requirements_fixed.txt"
    cp "$req_src" "$req_dst"

    local wheels_dir="$PROJECT_ROOT/scripts/wheels"
    local models_dir="$PROJECT_ROOT/models"
    local missing=()

    # 提取所有 file:// 行
    local file_lines
    file_lines=$(grep 'file:///' "$req_src" || true)

    while IFS= read -r line; do
        [ -z "$line" ] && continue

        # 提取文件名：取 file:/// 之后，# 之前的最后一段
        local raw_path
        raw_path=$(echo "$line" | sed 's|.*file:///||;s|#.*||')
        local whl_basename
        whl_basename=$(basename "$raw_path")

        # zh_core_web_sm 优先从 models/ 找，其余优先从 scripts/wheels/ 找
        local actual_path
        if echo "$whl_basename" | grep -q 'zh_core_web_sm'; then
            actual_path=$(find_wheel "$whl_basename" "$models_dir" "$wheels_dir" "/tmp") || true
        else
            actual_path=$(find_wheel "$whl_basename" "$wheels_dir" "$models_dir" "/tmp") || true
        fi

        if [ -n "$actual_path" ]; then
            log_ok "找到: $whl_basename → $actual_path"
            # 替换 file:///原路径（保留 #sha256= 部分）
            # actual_path is absolute (starts with /), so file:// + /path = file:///path (three slashes)
            local escaped_basename
            escaped_basename=$(printf '%s\n' "$whl_basename" | sed 's/[.[\*^$]/\\&/g')
            sed -i "s|file:///[^#]*${escaped_basename}|file://${actual_path}|g" "$req_dst"
        else
            log_warn "未找到: $whl_basename"
            missing+=("$whl_basename")
        fi
    done <<< "$file_lines"

    if [ ${#missing[@]} -gt 0 ]; then
        log_warn "以下 wheel 文件未找到："
        for m in "${missing[@]}"; do
            printf "  - %s\n" "$m"
        done
        printf "是否跳过这些包继续？[y/N] "
        read -r answer
        if [[ "$answer" =~ ^[Yy]$ ]]; then
            for m in "${missing[@]}"; do
                # 从 requirements_fixed.txt 中删除对应行
                grep -vF "$m" "$req_dst" > "${req_dst}.tmp" && mv "${req_dst}.tmp" "$req_dst"
                log_info "已从安装列表移除: $m"
            done
        else
            log_error "请将缺失的 wheel 文件放到 scripts/wheels/ 后重新运行"
            return 1
        fi
    fi

    log_ok "requirements_fixed.txt 已生成: $req_dst"
    mark_done "step_wheels"
}

step_deps() {
    is_done "step_deps" && log_info "step_deps 已完成，跳过" && return 0
    log_step "步骤 4/8: 安装 Python 依赖"

    local req_dst="$PROJECT_ROOT/requirements_fixed.txt"
    if [ ! -f "$req_dst" ]; then
        log_error "requirements_fixed.txt 不存在，请重置 step_wheels 后重新运行"
        log_error "方法: 从 .setup_state 的 COMPLETED_STEPS 中删除 step_wheels"
        return 1
    fi

    log_info "开始 pip install（大包较慢，请耐心等待）..."
    "$PIP" install --no-cache-dir -r "$req_dst" || {
        log_warn "pip install 返回非零，部分包可能安装失败"
        printf "是否忽略错误继续？[y/N] "
        read -r answer
        if [[ ! "$answer" =~ ^[Yy]$ ]]; then
            log_error "请检查上方错误信息后重新运行"
            return 1
        fi
    }

    log_ok "依赖安装完成"
    mark_done "step_deps"
}

step_models() {
    is_done "step_models" && log_info "step_models 已完成，跳过" && return 0
    log_step "步骤 5/8: 检测模型目录"

    local models_dir="$PROJECT_ROOT/models"
    local required_models=(
        "bge-base-zh-v1.5"
        "bge-reranker-base"
        "paraphrase-multilingual-MiniLM-L12-v2"
        "text2vec-base-chinese"
        "text2vec-word2vec-tencent-chinese"
    )
    local missing_models=()

    for model in "${required_models[@]}"; do
        if [ -d "$models_dir/$model" ]; then
            log_ok "模型存在: $model"
        else
            log_warn "模型缺失: $model"
            missing_models+=("$model")
        fi
    done

    if [ ${#missing_models[@]} -gt 0 ]; then
        printf "\n"
        log_warn "以下模型缺失，请后续上传到 %s/models/ 目录：\n" "$PROJECT_ROOT"
        for m in "${missing_models[@]}"; do
            printf "  - %s\n" "$m"
        done
        printf "\n（缺失模型不影响服务启动，但部分功能不可用）\n\n"
    else
        log_ok "所有模型均已就绪"
    fi

    mark_done "step_models"
}

step_services() {
    is_done "step_services" && log_info "step_services 已完成，跳过" && return 0
    log_step "步骤 6/8: 注册 ai-ken-backend 服务"

    local service_file="/etc/systemd/system/ai-ken-backend.service"

    cat > "$service_file" << EOF
[Unit]
Description=AI-KEN Backend Service (Flask API)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_ROOT}
Environment=PATH=${PROJECT_ROOT}/venv/bin
Environment=FLASK_ENV=production
Environment=CORS_ALLOW_ALL=false
ExecStart=${PROJECT_ROOT}/venv/bin/python app.py --host 127.0.0.1 --port ${BACKEND_PORT}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    log_info "服务文件已写入: $service_file"

    systemctl daemon-reload || { log_error "daemon-reload 失败"; return 1; }
    systemctl enable ai-ken-backend || { log_error "enable 失败"; return 1; }
    systemctl start ai-ken-backend || {
        log_error "服务启动失败，查看日志："
        journalctl -u ai-ken-backend --no-pager -n 20
        return 1
    }

    log_ok "ai-ken-backend 服务已启动"
    mark_done "step_services"
}

step_nginx() {
    is_done "step_nginx" && log_info "step_nginx 已完成，跳过" && return 0
    log_step "步骤 7/8: 配置并启动 Nginx"

    # 安装 nginx（若未安装）
    if ! command -v nginx &>/dev/null; then
        log_info "安装 nginx..."
        yum install -y nginx || { log_error "nginx 安装失败"; return 1; }
    fi

    local nginx_conf="/etc/nginx/conf.d/ai-ken.conf"
    local frontend_root="/var/www/ai-ken"

    # 确保前端静态文件目录存在
    mkdir -p "$frontend_root"

    cat > "$nginx_conf" << EOF
# AI-KEN 前后端分离 Nginx 配置（由 setup_centos.sh 生成）
# 前端端口: ${FRONTEND_PORT}  后端端口: ${BACKEND_PORT}

server {
    listen ${FRONTEND_PORT};
    server_name localhost;

    root ${frontend_root};
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    location /css/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /js/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /static/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location ~* ^/assets/.*\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location /local_knowledge/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /local_knowledge_detail/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /environment/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /label_studio/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /label_studio_env/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /qdrant/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /report/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /report_list/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /llm/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /knowledge_base/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location = /health {
        access_log off;
        add_header Content-Type text/plain;
        return 200 "healthy\n";
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

    log_info "nginx 配置已写入: $nginx_conf"

    # 检查配置语法
    nginx -t || { log_error "nginx 配置语法错误"; return 1; }

    systemctl enable nginx || { log_error "nginx enable 失败"; return 1; }

    # 首次安装用 start，已运行则 reload
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx || { log_error "nginx reload 失败"; return 1; }
        log_ok "nginx 配置已重载"
    else
        systemctl start nginx || { log_error "nginx 启动失败"; return 1; }
        log_ok "nginx 已启动"
    fi

    mark_done "step_nginx"
}

step_verify() {
    is_done "step_verify" && log_info "step_verify 已完成，跳过" && return 0
    log_step "步骤 8/8: 验证服务状态"

    sleep 3
    local pass=0 fail=0 all_ok=true

    log_info "--- Systemd 服务状态 ---"
    for svc in ai-ken-backend nginx; do
        local state
        state=$(systemctl is-active "$svc" 2>/dev/null || echo "inactive")
        if [ "$state" = "active" ]; then
            log_ok "$svc: active"
            pass=$((pass + 1))
        else
            log_fail "$svc: $state"
            fail=$((fail + 1))
            all_ok=false
            # 打印后端日志辅助排查
            if [ "$svc" = "ai-ken-backend" ]; then
                journalctl -u ai-ken-backend --no-pager -n 20
            fi
        fi
    done

    printf "\n"
    log_info "--- HTTP 验证 ---"

    local routes=(
        "Nginx健康检查|http://127.0.0.1:${FRONTEND_PORT}/health"
        "API-QA数据组|http://127.0.0.1:${FRONTEND_PORT}/api/qa/groups"
    )

    for route in "${routes[@]}"; do
        local name="${route%%|*}"
        local url="${route##*|}"
        local code
        code=$(no_proxy=127.0.0.1 curl -s --max-time 8 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || echo "000")
        if [[ "$code" =~ ^[23] ]]; then
            log_ok "$name → $code"
            pass=$((pass + 1))
        else
            log_fail "$name → $code ($url)"
            fail=$((fail + 1))
            all_ok=false
        fi
    done

    printf "\n"
    log_info "通过: $pass  失败: $fail"

    if $all_ok; then
        printf "\n${GREEN}✓ 初始化完成！所有服务正常${NC}\n"
        printf "${GREEN}  前端访问地址: http://$(hostname -I | awk '{print $1}'):${FRONTEND_PORT}${NC}\n\n"
    else
        printf "\n${YELLOW}⚠ 初始化完成，但有部分验证失败，请检查上方日志${NC}\n\n"
    fi

    mark_done "step_verify"
}

# ── 入口 ──────────────────────────────────────────────────────────
main() {
    # root 检查
    if [ "$(id -u)" -ne 0 ]; then
        log_error "请以 root 用户运行本脚本"
        exit 1
    fi

    printf "\n${BLUE}============================================${NC}\n"
    printf "${BLUE}   AI-KEN CentOS 初始化 - %s${NC}\n" "$(date '+%Y-%m-%d %H:%M:%S')"
    printf "${BLUE}   项目路径: %s${NC}\n" "$PROJECT_ROOT"
    printf "${BLUE}============================================${NC}\n\n"

    init_state
    collect_inputs
    prompt_wheels

    # PIP/PYTHON 提前赋值：step_venv 内部也赋值，但断点续跑时 step_venv 被跳过，
    # 此处提前赋值是断点续跑场景的兜底，确保后续步骤始终有效
    PIP="$PROJECT_ROOT/venv/bin/pip"
    PYTHON="$PROJECT_ROOT/venv/bin/python"

    step_python
    step_venv
    step_wheels
    step_deps
    step_models
    step_services
    step_nginx
    step_verify
}

main "$@"
