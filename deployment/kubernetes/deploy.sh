#!/bin/bash
# Kubernetes部署脚本
# 自动化部署CODEX交易系统到Kubernetes集群

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
用法: $0 [选项]

选项:
  -h, --help          显示帮助信息
  -n, --namespace     指定Kubernetes命名空间 (默认: codex-trading)
  -e, --env           指定环境类型 (production|development|testing, 默认: production)
  -c, --context       指定kubectl上下文 (可选)
  --dry-run           执行试运行，不实际应用变更
  --skip-secrets      跳过密钥创建 (仅用于开发环境)
  --skip-monitoring   跳过监控组件部署
  --wait              等待部署完成 (默认: true)
  --timeout           超时时间 (默认: 600秒)
  -v, --verbose       详细输出

示例:
  # 部署到生产环境
  $0 --env production

  # 部署到开发环境
  $0 --env development

  # 部署到指定命名空间
  $0 --namespace my-namespace --env production

  # 试运行模式
  $0 --dry-run

EOF
}

# 默认配置
NAMESPACE="codex-trading"
ENVIRONMENT="production"
DRY_RUN=false
SKIP_SECRETS=false
SKIP_MONITORING=false
WAIT=true
TIMEOUT=600
VERBOSE=false
KUBE_CONTEXT=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            log_info "使用命名空间: $NAMESPACE"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            if [[ ! "$ENVIRONMENT" =~ ^(production|development|testing)$ ]]; then
                log_error "无效的环境类型: $ENVIRONMENT. 必须是 production、development 或 testing"
                exit 1
            fi
            log_info "使用环境: $ENVIRONMENT"
            shift 2
            ;;
        -c|--context)
            KUBE_CONTEXT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            log_warn "试运行模式已启用，不会实际应用变更"
            shift
            ;;
        --skip-secrets)
            SKIP_SECRETS=true
            log_warn "将跳过密钥创建"
            shift
            ;;
        --skip-monitoring)
            SKIP_MONITORING=true
            log_warn "将跳过监控组件部署"
            shift
            ;;
        --no-wait)
            WAIT=false
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            set -x  # 启用详细输出
            shift
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 设置kubectl上下文
setup_kube_context() {
    if [[ -n "$KUBE_CONTEXT" ]]; then
        log_info "设置kubectl上下文: $KUBE_CONTEXT"
        kubectl config use-context "$KUBE_CONTEXT"
    fi
}

# 验证集群连接
verify_cluster() {
    log_info "验证Kubernetes集群连接..."
    if ! kubectl cluster-info &>/dev/null; then
        log_error "无法连接到Kubernetes集群"
        exit 1
    fi
    log_info "集群连接正常"
}

# 检查命名空间是否存在
check_namespace() {
    log_info "检查命名空间: $NAMESPACE"
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        log_info "创建命名空间: $NAMESPACE"
        kubectl create namespace "$NAMESPACE" --dry-run=$DRY_RUN -o yaml | kubectl apply -f -
    fi
}

# 应用配置映射
apply_configmaps() {
    log_info "应用配置映射..."
    if [[ "$DRY_RUN" == true ]]; then
        kubectl apply --dry-run=client -f configmap.yaml -n "$NAMESPACE"
    else
        kubectl apply -f configmap.yaml -n "$NAMESPACE"
    fi
}

# 应用密钥
apply_secrets() {
    if [[ "$SKIP_SECRETS" == true ]]; then
        log_warn "跳过密钥创建"
        return
    fi

    log_info "应用密钥..."
    if [[ "$DRY_RUN" == true ]]; then
        kubectl apply --dry-run=client -f secrets.yaml -n "$NAMESPACE"
    else
        # 检查密钥是否已存在
        if kubectl get secret codex-database-secret -n "$NAMESPACE" &>/dev/null; then
            log_warn "密钥已存在，跳过创建"
        else
            kubectl apply -f secrets.yaml -n "$NAMESPACE"
        fi
    fi
}

# 应用PVC
apply_pvcs() {
    log_info "应用持久化存储卷声明..."
    if [[ "$DRY_RUN" == true ]]; then
        kubectl apply --dry-run=client -f pvc.yaml -n "$NAMESPACE"
    else
        kubectl apply -f pvc.yaml -n "$NAMESPACE"
    fi
}

# 应用RBAC
apply_rbac() {
    log_info "应用RBAC权限控制..."
    if [[ "$DRY_RUN" == true ]]; then
        kubectl apply --dry-run=client -f rbac.yaml
    else
        kubectl apply -f rbac.yaml
    fi
}

# 应用部署
apply_deployments() {
    log_info "应用部署配置..."
    if [[ "$DRY_RUN" == true ]]; then
        kubectl apply --dry-run=client -f deployment.yaml -n "$NAMESPACE"
    else
        kubectl apply -f deployment.yaml -n "$NAMESPACE"
    fi
}

# 应用服务
apply_services() {
    log_info "应用服务配置..."
    if [[ "$DRY_RUN" == true ]]; then
        kubectl apply --dry-run=client -f service.yaml -n "$NAMESPACE"
    else
        kubectl apply -f service.yaml -n "$NAMESPACE"
    fi
}

# 应用HPA
apply_hpa() {
    log_info "应用水平自动缩放器..."
    if [[ "$DRY_RUN" == true ]]; then
        kubectl apply --dry-run=client -f hpa.yaml -n "$NAMESPACE"
    else
        kubectl apply -f hpa.yaml -n "$NAMESPACE"
    fi
}

# 应用Ingress
apply_ingress() {
    log_info "应用Ingress配置..."
    if [[ "$DRY_RUN" == true ]]; then
        kubectl apply --dry-run=client -f ingress.yaml -n "$NAMESPACE"
    else
        kubectl apply -f ingress.yaml -n "$NAMESPACE"
    fi
}

# 等待部署完成
wait_for_deployment() {
    if [[ "$WAIT" == false ]]; then
        return
    fi

    log_info "等待部署完成..."
    local timeout=$TIMEOUT
    local elapsed=0

    # 等待应用部署
    log_info "等待应用部署就绪..."
    while [[ $elapsed -lt $timeout ]]; do
        if kubectl rollout status deployment/codex-trading-app -n "$NAMESPACE" --timeout=1 &>/dev/null; then
            log_info "应用部署成功"
            break
        fi
        sleep 5
        elapsed=$((elapsed + 5))
        if [[ $((elapsed % 30)) -eq 0 ]]; then
            log_info "等待部署中... (已等待 ${elapsed}s/${timeout}s)"
        fi
    done

    if [[ $elapsed -ge $timeout ]]; then
        log_error "部署超时"
        kubectl get pods -n "$NAMESPACE"
        return 1
    fi

    # 等待数据库部署
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "等待数据库部署就绪..."
        kubectl rollout status deployment/postgres -n "$NAMESPACE" --timeout=300 &>/dev/null || true
        kubectl rollout status deployment/redis -n "$NAMESPACE" --timeout=300 &>/dev/null || true
    fi

    log_info "部署完成！"
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."

    # 检查Pod状态
    log_info "检查Pod状态:"
    kubectl get pods -n "$NAMESPACE"

    # 检查服务状态
    log_info "检查服务状态:"
    kubectl get services -n "$NAMESPACE"

    # 检查Ingress状态
    if kubectl get ingress codex-trading-ingress -n "$NAMESPACE" &>/dev/null; then
        log_info "检查Ingress状态:"
        kubectl get ingress codex-trading-ingress -n "$NAMESPACE"
    fi

    # 运行健康检查
    log_info "运行健康检查..."
    if kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=codex-trading | grep -q Running; then
        log_info "✓ Pods运行正常"
    else
        log_error "✗ Pods异常"
        return 1
    fi

    # 检查端点
    log_info "检查服务端点:"
    kubectl get endpoints -n "$NAMESPACE"
}

# 显示访问信息
show_access_info() {
    log_info "======================================"
    log_info "部署完成！访问信息："
    log_info "======================================"
    log_info "API文档: https://api.codex.trading.com/docs"
    log_info "健康检查: https://api.codex.trading.com/health"
    log_info "Grafana: https://grafana.codex.trading.com"
    log_info "Prometheus: https://prometheus.codex.trading.com"
    log_info "命名空间: $NAMESPACE"
    log_info "======================================"
}

# 清理临时文件
cleanup() {
    if [[ -n "${TEMP_DIR:-}" ]] && [[ -d "$TEMP_DIR" ]]; then
        log_info "清理临时文件: $TEMP_DIR"
        rm -rf "$TEMP_DIR"
    fi
}

# 注册退出陷阱
trap cleanup EXIT

# 主函数
main() {
    log_info "======================================"
    log_info "CODEX交易系统 Kubernetes 部署脚本"
    log_info "======================================"
    log_info "环境: $ENVIRONMENT"
    log_info "命名空间: $NAMESPACE"
    log_info "======================================"

    # 创建临时目录用于修改配置文件
    TEMP_DIR=$(mktemp -d)
    log_info "临时目录: $TEMP_DIR"

    # 执行部署步骤
    setup_kube_context
    verify_cluster
    check_namespace
    apply_configmaps
    apply_secrets
    apply_pvcs
    apply_rbac
    apply_deployments
    apply_services
    apply_hpa
    apply_ingress

    # 等待部署完成
    if [[ "$WAIT" == true ]]; then
        wait_for_deployment
    fi

    # 验证部署
    verify_deployment

    # 显示访问信息
    show_access_info

    log_info "部署脚本执行完成！"
}

# 执行主函数
main
