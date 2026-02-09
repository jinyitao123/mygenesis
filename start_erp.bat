@echo off
echo 启动 Genesis ERP 系统...
echo.

echo 1. 部署 supply_chain_erp 域到 ontology...
python deploy_erp_domain.py

echo.
echo 2. 启动 ERP 服务器...
echo 访问: http://localhost:8001
echo 按 Ctrl+C 停止服务器
echo.

python applications/erp/main.py