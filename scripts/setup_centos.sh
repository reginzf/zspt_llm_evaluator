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
    grep -v "^${key}=" "$STATE_FILE" > "${STATE_FILE}.tmp" && \
        mv "${STATE_FILE}.tmp" "$STATE_FILE"
    printf '%s="%s"\n' "$key" "$val" >> "$STATE_FILE"
    # 同步到当前 shell
    eval "${key}=\"${val}\""
}

# 标记步骤完成
mark_done() {
    local step="$1"
    COMPLETED_STEPS="$COMPLETED_STEPS $step"
    grep -v '^COMPLETED_STEPS=' "$STATE_FILE" > "${STATE_FILE}.tmp" && \
        mv "${STATE_FILE}.tmp" "$STATE_FILE"
    printf 'COMPLETED_STEPS="%s"\n' "$COMPLETED_STEPS" >> "$STATE_FILE"
}

# 判断步骤是否已完成
is_done() {
    echo "$COMPLETED_STEPS" | grep -qw "$1"
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
