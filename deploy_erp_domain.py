"""
部署 ERP 域到 ontology 目录

在启动 ERP 系统前，需要将 supply_chain_erp 域的文件复制到 ontology 目录
"""

import os
import shutil
from pathlib import Path

def deploy_erp_domain():
    """部署 supply_chain_erp 域到 ontology 目录"""
    project_root = Path(__file__).parent
    domains_dir = project_root / "domains"
    ontology_dir = project_root / "ontology"
    
    # 源目录和目标目录
    source_domain = "supply_chain_erp"
    source_dir = domains_dir / source_domain
    target_dir = ontology_dir
    
    # 确保目录存在
    target_dir.mkdir(exist_ok=True)
    
    # 必需的文件列表
    required_files = [
        "object_types.xml",
        "action_types.xml", 
        "seed_data.xml"
    ]
    
    print(f"=== 部署 {source_domain} 域到 ontology ===")
    
    # 检查源文件
    missing_files = []
    for filename in required_files:
        source_file = source_dir / filename
        if not source_file.exists():
            missing_files.append(filename)
    
    if missing_files:
        print(f"错误: 缺少必需文件: {missing_files}")
        return False
    
    # 备份现有文件（如果存在）
    backup_files = []
    for filename in required_files:
        target_file = target_dir / filename
        if target_file.exists():
            backup_file = target_dir / f"{filename}.backup"
            shutil.copy2(target_file, backup_file)
            backup_files.append(backup_file)
    
    if backup_files:
        print(f"已备份 {len(backup_files)} 个现有文件")
    
    # 复制文件
    copied_files = []
    for filename in required_files:
        source_file = source_dir / filename
        target_file = target_dir / filename
        
        shutil.copy2(source_file, target_file)
        copied_files.append(filename)
        print(f"  已复制: {filename}")
    
    # 可选文件
    optional_files = ["config.json"]
    for filename in optional_files:
        source_file = source_dir / filename
        if source_file.exists():
            target_file = target_dir / filename
            shutil.copy2(source_file, target_file)
            print(f"  已复制(可选): {filename}")
    
    print(f"=== 部署完成: 复制了 {len(copied_files)} 个文件 ===")
    return True

if __name__ == "__main__":
    success = deploy_erp_domain()
    if success:
        print("ERP 域部署成功，可以启动 ERP 系统了")
        print("运行: python applications/erp/main.py")
    else:
        print("ERP 域部署失败")