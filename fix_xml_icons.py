#!/usr/bin/env python3
"""
修复XML文件中的表情符号图标
"""

import os
import re
from pathlib import Path

# 表情符号到文本图标的映射
EMOJI_MAP = {
    "📦": "package",      # 包裹
    "🚚": "truck",       # 卡车
    "📊": "chart",       # 图表
    "💹": "exchange",    # 交易
    "🛡️": "shield-check", # 盾牌检查
    "👁️": "eye",        # 眼睛
    "⚠️": "alert-triangle", # 警告三角
    "🏭": "factory",     # 工厂
    "🏥": "hospital",    # 医院
    "💊": "pill",        # 药丸
    "🖥️": "monitor",    # 显示器
    "🔒": "lock",        # 锁
    "🏙️": "building",   # 建筑
    "🚦": "traffic-light", # 交通灯
    "💡": "lightbulb",   # 灯泡
}

def fix_xml_file(file_path):
    """修复单个XML文件中的表情符号"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换表情符号
        fixed_content = content
        for emoji, text_icon in EMOJI_MAP.items():
            fixed_content = fixed_content.replace(emoji, text_icon)
        
        # 如果内容有变化，保存文件
        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"已修复: {file_path}")
            return True
        else:
            print(f"无需修复: {file_path}")
            return False
            
    except Exception as e:
        print(f"处理文件失败 {file_path}: {e}")
        return False

def main():
    # 修复所有领域的action_types.xml文件
    domains_dir = Path("domains")
    
    if not domains_dir.exists():
        print(f"错误: 找不到domains目录: {domains_dir}")
        return
    
    fixed_count = 0
    total_count = 0
    
    for domain_dir in domains_dir.iterdir():
        if domain_dir.is_dir():
            xml_file = domain_dir / "action_types.xml"
            if xml_file.exists():
                total_count += 1
                if fix_xml_file(xml_file):
                    fixed_count += 1
    
    print(f"\n修复完成:")
    print(f"  检查文件数: {total_count}")
    print(f"  修复文件数: {fixed_count}")

if __name__ == "__main__":
    main()