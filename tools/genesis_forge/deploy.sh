#!/bin/bash

# Genesis Forge 部署脚本
# 用法: ./deploy.sh [环境] [操作]
# 环境: dev, staging, prod (默认: dev)
# 操作: build, up, down, restart, logs, status (默认: up)

set -e

# 默认值
ENVIRONMENT=${1:-dev}
ACTION=${2:-up}
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.${ENVIRONMENT}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境文件
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "环境文件 $ENV_FILE 不存在，使用 .env.example 创建"
        if [ -f ".env.example" ]; then
            cp .env.example "$ENV_FILE"
            log_info "已创建 $ENV_FILE，请根据需要修改配置"
        else
            log_error ".env.example 文件不存在"
            exit 1
        fi
    fi
}

# 检查 Docker 和 Docker Compose
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    log_success "服务启动完成"
    
    # 显示服务状态
    sleep 2
    show_status
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
    log_success "服务重启完成"
}

# 查看日志
show_logs() {
    log_info "查看服务日志..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
}

# 显示状态
show_status() {
    log_info "服务状态:"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    echo ""
    log_info "服务健康状态:"
    services=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --services)
    for service in $services; do
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps | grep -q "$service.*Up"; then
            echo -e "${GREEN}✓${NC} $service: 运行中"
        else
            echo -e "${RED}✗${NC} $service: 未运行"
        fi
    done
    
    echo ""
    log_info "服务访问信息:"
    echo "前端应用: http://localhost:3000"
    echo "后端API: http://localhost:5000"
    echo "Neo4j Browser: http://localhost:7474"
    echo "PostgreSQL: localhost:5432"
    echo "Redis: localhost:6379"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 等待 Neo4j 就绪
    log_info "等待 Neo4j 就绪..."
    until docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec neo4j cypher-shell -u "${NEO4J_USER:-neo4j}" -p "${NEO4J_PASSWORD:-password}" "RETURN 1" > /dev/null 2>&1; do
        sleep 5
    done
    
    # 初始化图数据
    log_info "初始化图数据..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec backend python init_graph_simple.py
    
    log_success "数据库初始化完成"
}

# 备份数据
backup_data() {
    log_info "备份数据..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="backups/$TIMESTAMP"
    
    mkdir -p "$BACKUP_DIR"
    
    # 备份 Neo4j 数据
    log_info "备份 Neo4j 数据..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec neo4j neo4j-admin dump --to=/backup/neo4j.dump
    docker cp "$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps -q neo4j):/backup/neo4j.dump" "$BACKUP_DIR/neo4j.dump"
    
    # 备份 PostgreSQL 数据
    log_info "备份 PostgreSQL 数据..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec postgres pg_dump -U "${POSTGRES_USER:-postgres}" "${POSTGRES_DB:-genesis_forge}" > "$BACKUP_DIR/postgres.sql"
    
    # 备份应用数据
    log_info "备份应用数据..."
    tar -czf "$BACKUP_DIR/app_data.tar.gz" domains ontology data logs
    
    log_success "数据备份完成: $BACKUP_DIR"
}

# 清理资源
cleanup() {
    log_info "清理未使用的 Docker 资源..."
    docker system prune -f
    log_success "资源清理完成"
}

# 主函数
main() {
    log_info "Genesis Forge 部署工具"
    log_info "环境: $ENVIRONMENT, 操作: $ACTION"
    
    # 检查依赖
    check_dependencies
    
    # 检查环境文件
    check_env_file
    
    # 加载环境变量
    set -a
    source "$ENV_FILE"
    set +a
    
    case "$ACTION" in
        "build")
            build_images
            ;;
        "up")
            build_images
            start_services
            init_database
            ;;
        "down")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "init-db")
            init_database
            ;;
        "backup")
            backup_data
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            log_error "未知操作: $ACTION"
            echo "可用操作: build, up, down, restart, logs, status, init-db, backup, cleanup"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"