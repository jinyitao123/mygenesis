#!/usr/bin/env python3
"""
初始化Neo4j图数据库数据
"""

from backend.services.neo4j_loader import Neo4jLoader
import json

def init_supply_chain_data():
    """初始化供应链数据到Neo4j"""
    loader = Neo4jLoader()
    
    # 清空现有数据
    print("清空现有数据...")
    loader.clear_graph()
    
    # 创建供应链节点
    print("创建供应链节点...")
    
    # 卡车节点
    trucks = [
        {"id": "truck_001", "label": "运输卡车A", "type": "TRUCK", "location": "仓库A", "status": "空闲", "capacity": 10, "fuel_level": 100},
        {"id": "truck_002", "label": "运输卡车B", "type": "TRUCK", "location": "仓库B", "status": "运输中", "capacity": 15, "fuel_level": 80},
        {"id": "truck_003", "label": "冷藏卡车", "type": "TRUCK", "location": "冷库", "status": "维护中", "capacity": 8, "fuel_level": 50}
    ]
    
    # 仓库节点
    warehouses = [
        {"id": "warehouse_001", "label": "中央仓库", "type": "WAREHOUSE", "location": "工业区", "capacity": 1000, "current_load": 200},
        {"id": "warehouse_002", "label": "分拨中心", "type": "WAREHOUSE", "location": "物流园", "capacity": 500, "current_load": 150},
        {"id": "warehouse_003", "label": "冷库", "type": "WAREHOUSE", "location": "冷链基地", "capacity": 300, "current_load": 100, "temperature": -18}
    ]
    
    # 包裹节点
    packages = [
        {"id": "package_001", "label": "电子产品包裹", "type": "PACKAGE", "location": "仓库A", "weight": 5, "destination": "客户地址A", "status": "待发货"},
        {"id": "package_002", "label": "服装包裹", "type": "PACKAGE", "location": "仓库B", "weight": 3, "destination": "客户地址B", "status": "运输中"},
        {"id": "package_003", "label": "食品冷链包裹", "type": "PACKAGE", "location": "冷库", "weight": 8, "destination": "超市A", "status": "冷藏中", "temperature_required": -5}
    ]
    
    # 订单节点
    orders = [
        {"id": "order_001", "label": "电子产品订单", "type": "ORDER", "customer": "客户A", "total_amount": 5000, "status": "已发货", "delivery_date": "2026-02-10"},
        {"id": "order_002", "label": "服装订单", "type": "ORDER", "customer": "客户B", "total_amount": 1200, "status": "处理中", "delivery_date": "2026-02-12"},
        {"id": "order_003", "label": "食品订单", "type": "ORDER", "customer": "超市A", "total_amount": 800, "status": "待处理", "delivery_date": "2026-02-09"}
    ]
    
    # 供应商节点
    suppliers = [
        {"id": "supplier_001", "label": "电子元件供应商", "type": "SUPPLIER", "name": "华强电子", "location": "深圳", "rating": 4.5},
        {"id": "supplier_002", "label": "服装供应商", "type": "SUPPLIER", "name": "纺织集团", "location": "杭州", "rating": 4.2},
        {"id": "supplier_003", "label": "食品供应商", "type": "SUPPLIER", "name": "冷链食品", "location": "青岛", "rating": 4.8}
    ]
    
    # 创建所有节点
    all_nodes = trucks + warehouses + packages + orders + suppliers
    
    for node_data in all_nodes:
        node_id = node_data.pop('id')
        loader.create_node(node_id, node_data)
        print(f"创建节点: {node_id} - {node_data.get('label', '未知')}")
    
    # 创建关系
    print("创建关系...")
    
    # 卡车位于仓库
    loader.create_relationship("truck_001", "warehouse_001", "LOCATED_AT", {"since": "2026-02-01"})
    loader.create_relationship("truck_002", "warehouse_002", "LOCATED_AT", {"since": "2026-02-05"})
    loader.create_relationship("truck_003", "warehouse_003", "LOCATED_AT", {"since": "2026-02-03"})
    
    # 包裹在仓库中
    loader.create_relationship("package_001", "warehouse_001", "CONTAINS", {})
    loader.create_relationship("package_002", "warehouse_002", "CONTAINS", {})
    loader.create_relationship("package_003", "warehouse_003", "CONTAINS", {})
    
    # 订单包含包裹
    loader.create_relationship("order_001", "package_001", "CONTAINS", {})
    loader.create_relationship("order_002", "package_002", "CONTAINS", {})
    loader.create_relationship("order_003", "package_003", "CONTAINS", {})
    
    # 供应商提供商品
    loader.create_relationship("supplier_001", "order_001", "SUPPLIES", {"product_type": "电子产品"})
    loader.create_relationship("supplier_002", "order_002", "SUPPLIES", {"product_type": "服装"})
    loader.create_relationship("supplier_003", "order_003", "SUPPLIES", {"product_type": "食品"})
    
    # 卡车运输包裹
    loader.create_relationship("truck_002", "package_002", "TRANSPORTS", {"start_time": "2026-02-09 08:00", "estimated_arrival": "2026-02-09 14:00"})
    
    print("供应链数据初始化完成！")

def init_finance_risk_data():
    """初始化金融风控数据到Neo4j"""
    loader = Neo4jLoader()
    
    print("初始化金融风控数据...")
    
    # 账户节点
    accounts = [
        {"id": "account_001", "label": "企业账户A", "type": "ACCOUNT", "balance": 1000000, "currency": "CNY", "status": "正常", "risk_level": "低"},
        {"id": "account_002", "label": "个人账户B", "type": "ACCOUNT", "balance": 50000, "currency": "CNY", "status": "正常", "risk_level": "中"},
        {"id": "account_003", "label": "高风险账户", "type": "ACCOUNT", "balance": 10000, "currency": "USD", "status": "监控中", "risk_level": "高"}
    ]
    
    # 客户节点
    customers = [
        {"id": "customer_001", "label": "张三", "type": "CUSTOMER", "name": "张三", "age": 35, "occupation": "工程师", "credit_score": 750},
        {"id": "customer_002", "label": "李四", "type": "CUSTOMER", "name": "李四", "age": 42, "occupation": "企业家", "credit_score": 820},
        {"id": "customer_003", "label": "王五", "type": "CUSTOMER", "name": "王五", "age": 28, "occupation": "自由职业", "credit_score": 650}
    ]
    
    # 交易节点
    transactions = [
        {"id": "tx_001", "label": "大额转账", "type": "TRANSACTION", "amount": 500000, "currency": "CNY", "date": "2026-02-08", "status": "完成", "description": "企业间转账"},
        {"id": "tx_002", "label": "跨境支付", "type": "TRANSACTION", "amount": 10000, "currency": "USD", "date": "2026-02-09", "status": "处理中", "description": "国际采购"},
        {"id": "tx_003", "label": "可疑交易", "type": "TRANSACTION", "amount": 5000, "currency": "CNY", "date": "2026-02-07", "status": "审核中", "description": "多次小额转账"}
    ]
    
    # 贷款节点
    loans = [
        {"id": "loan_001", "label": "企业贷款", "type": "LOAN", "amount": 5000000, "term": 36, "interest_rate": 4.5, "status": "已批准", "purpose": "设备采购"},
        {"id": "loan_002", "label": "个人消费贷", "type": "LOAN", "amount": 100000, "term": 12, "interest_rate": 6.8, "status": "审核中", "purpose": "装修"},
        {"id": "loan_003", "label": "抵押贷款", "type": "LOAN", "amount": 2000000, "term": 240, "interest_rate": 3.9, "status": "已发放", "purpose": "购房"}
    ]
    
    # 担保节点
    guarantees = [
        {"id": "guarantee_001", "label": "房产抵押", "type": "GUARANTEE", "value": 3000000, "type_detail": "房产", "status": "有效", "expiry_date": "2046-02-09"},
        {"id": "guarantee_002", "label": "保证金", "type": "GUARANTEE", "value": 500000, "type_detail": "现金", "status": "有效", "expiry_date": "2027-02-09"},
        {"id": "guarantee_003", "label": "第三方担保", "type": "GUARANTEE", "value": 1000000, "type_detail": "企业担保", "status": "有效", "expiry_date": "2028-02-09"}
    ]
    
    # 创建所有节点
    all_nodes = accounts + customers + transactions + loans + guarantees
    
    for node_data in all_nodes:
        node_id = node_data.pop('id')
        loader.create_node(node_id, node_data)
        print(f"创建节点: {node_id} - {node_data.get('label', '未知')}")
    
    # 创建关系
    print("创建金融关系...")
    
    # 客户拥有账户
    loader.create_relationship("customer_001", "account_001", "OWNS", {"since": "2020-01-15"})
    loader.create_relationship("customer_002", "account_002", "OWNS", {"since": "2021-03-20"})
    loader.create_relationship("customer_003", "account_003", "OWNS", {"since": "2022-05-10"})
    
    # 账户间转账
    loader.create_relationship("account_001", "account_002", "TRANSFERS_TO", {"transaction_id": "tx_001", "amount": 500000})
    loader.create_relationship("account_002", "account_003", "TRANSFERS_TO", {"transaction_id": "tx_002", "amount": 10000})
    
    # 客户申请贷款
    loader.create_relationship("customer_001", "loan_001", "APPLIES_FOR", {"application_date": "2026-01-15", "status": "approved"})
    loader.create_relationship("customer_002", "loan_002", "APPLIES_FOR", {"application_date": "2026-02-01", "status": "pending"})
    loader.create_relationship("customer_003", "loan_003", "APPLIES_FOR", {"application_date": "2025-12-10", "status": "approved"})
    
    # 贷款有担保
    loader.create_relationship("loan_001", "guarantee_001", "GUARANTEED_BY", {"coverage": "full"})
    loader.create_relationship("loan_002", "guarantee_002", "GUARANTEED_BY", {"coverage": "partial"})
    loader.create_relationship("loan_003", "guarantee_003", "GUARANTEED_BY", {"coverage": "full"})
    
    # 交易属于账户
    loader.create_relationship("tx_001", "account_001", "BELONGS_TO", {})
    loader.create_relationship("tx_002", "account_002", "BELONGS_TO", {})
    loader.create_relationship("tx_003", "account_003", "BELONGS_TO", {})
    
    print("金融风控数据初始化完成！")

def main():
    """主函数"""
    print("开始初始化Neo4j图数据库数据...")
    
    try:
        # 初始化供应链数据
        init_supply_chain_data()
        
        # 初始化金融风控数据
        init_finance_risk_data()
        
        # 获取统计信息
        loader = Neo4jLoader()
        stats = loader.get_graph_stats()
        
        print("\n图数据库统计信息:")
        print(f"节点总数: {stats.get('node_count', 0)}")
        print(f"关系总数: {stats.get('link_count', 0)}")
        print(f"节点类型: {stats.get('node_types', [])}")
        
        print("\n数据初始化完成！")
        print("前端可视化编辑器现在可以显示真实的图数据库数据。")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()