#!/usr/bin/env python3
"""
验证domains目录下的XML文件是否符合genesis_forge系统规则
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Set
import re

# 支持的属性类型
SUPPORTED_TYPES = {'int', 'float', 'bool', 'string', 'enum', 'date', 'datetime', 'boolean'}

def validate_object_types(file_path: str) -> List[str]:
    """验证object_types.xml文件"""
    errors = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # 检查domain属性
        domain = root.get('domain')
        if not domain:
            errors.append(f"缺少domain属性")
        
        # 收集所有对象类型名称
        object_types = set()
        for obj_type in root.findall('.//ObjectType'):
            type_name = obj_type.get('name')
            if not type_name:
                errors.append(f"ObjectType缺少name属性")
                continue
                
            object_types.add(type_name)
            
            # 验证属性定义
            for prop in obj_type.findall('.//Property'):
                prop_name = prop.get('name')
                prop_type = prop.get('type')
                
                if not prop_name:
                    errors.append(f"ObjectType {type_name}: Property缺少name属性")
                    
                if not prop_type:
                    errors.append(f"ObjectType {type_name}.{prop_name}: Property缺少type属性")
                elif prop_type not in SUPPORTED_TYPES:
                    errors.append(f"ObjectType {type_name}.{prop_name}: 不支持的类型 '{prop_type}'，支持的类型: {SUPPORTED_TYPES}")
                
                # 如果是enum类型，检查是否有enum_values
                if prop_type == 'enum':
                    enum_values = prop.get('enum')
                    if not enum_values:
                        errors.append(f"ObjectType {type_name}.{prop_name}: enum类型必须提供enum属性")
        
        # 验证LinkType引用
        for link_type in root.findall('.//LinkType'):
            source = link_type.get('source')
            target = link_type.get('target')
            
            if source and source not in object_types:
                errors.append(f"LinkType {link_type.get('name')}: 引用了不存在的源类型 '{source}'")
            if target and target not in object_types:
                errors.append(f"LinkType {link_type.get('name')}: 引用了不存在的目标类型 '{target}'")
                
    except ET.ParseError as e:
        errors.append(f"XML解析错误: {e}")
    except Exception as e:
        errors.append(f"验证错误: {e}")
    
    return errors

def validate_action_types(file_path: str, object_types: Set[str]) -> List[str]:
    """验证action_types.xml文件"""
    errors = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for action in root.findall('.//action_type'):
            action_id = action.find('id')
            if action_id is None or not action_id.text:
                errors.append("action_type缺少id")
                continue
                
            # 验证颜色标签格式
            color = action.find('color')
            if color is not None and color.text:
                if not re.match(r'^#[0-9a-fA-F]{6}$', color.text):
                    errors.append(f"action {action_id.text}: 颜色格式不正确 '{color.text}'，应为 #RRGGBB 格式")
            
            # 验证object_type引用
            for obj_ref in action.findall('.//object_type'):
                if obj_ref.text and obj_ref.text not in object_types:
                    errors.append(f"action {action_id.text}: 引用了不存在的对象类型 '{obj_ref.text}'")
                    
    except ET.ParseError as e:
        errors.append(f"XML解析错误: {e}")
    except Exception as e:
        errors.append(f"验证错误: {e}")
    
    return errors

def validate_seed_data(file_path: str, object_types: Set[str]) -> List[str]:
    """验证seed_data.xml文件"""
    errors = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # 检查domain属性
        domain = root.get('domain')
        if not domain:
            errors.append("缺少domain属性")
        
        # 验证节点类型
        for node in root.findall('.//Node'):
            node_type = node.get('type')
            if node_type and node_type not in object_types:
                errors.append(f"节点 {node.get('id')}: 使用了未定义的类型 '{node_type}'")
            
            # 验证属性类型
            for prop in node.findall('.//Property'):
                prop_type = prop.get('type')
                if prop_type and prop_type not in SUPPORTED_TYPES:
                    errors.append(f"节点 {node.get('id')}: 属性 {prop.get('key')} 使用了不支持的类型 '{prop_type}'")
        
        # 验证链接引用
        node_ids = {node.get('id') for node in root.findall('.//Node')}
        for link in root.findall('.//Link'):
            source = link.get('source')
            target = link.get('target')
            
            if source and source not in node_ids:
                errors.append(f"链接 {link.get('type')}: 引用了不存在的源节点 '{source}'")
            if target and target not in node_ids:
                errors.append(f"链接 {link.get('type')}: 引用了不存在的目标节点 '{target}'")
                
    except ET.ParseError as e:
        errors.append(f"XML解析错误: {e}")
    except Exception as e:
        errors.append(f"验证错误: {e}")
    
    return errors

def main():
    base_dir = "domains"
    
    for domain in os.listdir(base_dir):
        domain_path = os.path.join(base_dir, domain)
        if not os.path.isdir(domain_path):
            continue
            
        print(f"\n=== 验证领域: {domain} ===")
        
        # 验证object_types.xml
        obj_types_file = os.path.join(domain_path, "object_types.xml")
        if os.path.exists(obj_types_file):
            print(f"验证 {obj_types_file}...")
            errors = validate_object_types(obj_types_file)
            if errors:
                for error in errors:
                    print(f"  [ERROR] {error}")
            else:
                print(f"  [OK] 验证通过")
            
            # 收集对象类型名称用于后续验证
            try:
                tree = ET.parse(obj_types_file)
                object_types = {obj.get('name') for obj in tree.findall('.//ObjectType')}
            except:
                object_types = set()
        else:
            print(f"  [WARN] 缺少object_types.xml")
            object_types = set()
        
        # 验证action_types.xml
        action_types_file = os.path.join(domain_path, "action_types.xml")
        if os.path.exists(action_types_file):
            print(f"验证 {action_types_file}...")
            errors = validate_action_types(action_types_file, object_types)
            if errors:
                for error in errors:
                    print(f"  [ERROR] {error}")
            else:
                print(f"  [OK] 验证通过")
        else:
            print(f"  [WARN] 缺少action_types.xml")
        
        # 验证seed_data.xml
        seed_data_file = os.path.join(domain_path, "seed_data.xml")
        if os.path.exists(seed_data_file):
            print(f"验证 {seed_data_file}...")
            errors = validate_seed_data(seed_data_file, object_types)
            if errors:
                for error in errors:
                    print(f"  [ERROR] {error}")
            else:
                print(f"  [OK] 验证通过")
        else:
            print(f"  [WARN] 缺少seed_data.xml")

if __name__ == "__main__":
    main()