#!/usr/bin/env python3
"""
批量修复domains目录下所有XML文件中的表情符号
"""

import os
import re
from pathlib import Path

# 扩展的表情符号到文本图标的映射
EMOJI_MAP = {
    # 通用图标
    "📦": "package",           # 包裹
    "🚚": "truck",            # 卡车
    "📊": "chart",            # 图表
    "💹": "exchange",         # 交易
    "🛡️": "shield-check",    # 盾牌检查
    "👁️": "eye",             # 眼睛
    "⚠️": "alert-triangle",  # 警告三角
    "🏭": "factory",          # 工厂
    "🏥": "hospital",         # 医院
    "💊": "pill",             # 药丸
    "🖥️": "monitor",         # 显示器
    "🔒": "lock",             # 锁
    "🏙️": "building",        # 建筑
    "🚦": "traffic-light",   # 交通灯
    "💡": "lightbulb",        # 灯泡
    "⛽": "fuel",             # 加油站
    "📝": "document",         # 文档
    "🚛": "truck",           # 大卡车
    "📦": "box",             # 箱子
    "🏪": "store",           # 商店
    "🏢": "office-building", # 办公楼
    "🚗": "car",             # 汽车
    "🚕": "taxi",            # 出租车
    "🚌": "bus",             # 公交车
    "🚑": "ambulance",       # 救护车
    "🚒": "fire-truck",      # 消防车
    "🚓": "police-car",      # 警车
    "🚨": "siren",           # 警笛
    "🚔": "police",          # 警察
    "🚍": "trolleybus",      # 无轨电车
    "🚎": "tram",            # 有轨电车
    "🚐": "minibus",         # 小巴
    "🚙": "suv",             # SUV
    "🚜": "tractor",         # 拖拉机
    "🚲": "bicycle",         # 自行车
    "🛵": "scooter",         # 摩托车
    "🚁": "helicopter",      # 直升机
    "✈️": "airplane",        # 飞机
    "🚀": "rocket",          # 火箭
    "🛸": "ufo",             # UFO
    "🛶": "canoe",           # 独木舟
    "⛵": "sailboat",        # 帆船
    "🛳️": "ship",           # 轮船
    "🚂": "train",           # 火车
    "🚆": "train2",          # 火车2
    "🚇": "metro",           # 地铁
    "🚊": "tram2",           # 有轨电车2
    "🚉": "station",         # 车站
    "🗼": "tower",           # 塔
    "🗽": "statue",          # 雕像
    "🗿": "moyai",           # 摩艾石像
    "🌁": "foggy",           # 雾
    "🌃": "night",           # 夜晚
    "🌄": "sunrise",         # 日出
    "🌅": "sunset",          # 日落
    "🌆": "cityscape",       # 城市景观
    "🌇": "sunset2",         # 日落2
    "🌉": "bridge",          # 桥
    "♨️": "hotsprings",     # 温泉
    "🌌": "milky-way",       # 银河
    "🎠": "carousel",        # 旋转木马
    "🎡": "ferris-wheel",    # 摩天轮
    "🎢": "roller-coaster",  # 过山车
    "💈": "barber",          # 理发店
    "🎪": "circus",          # 马戏团
    "🎭": "performing-arts", # 表演艺术
    "🖼️": "frame",          # 画框
    "🎨": "art",             # 艺术
    "🧵": "thread",          # 线
    "🧶": "yarn",            # 毛线
    "👓": "glasses",         # 眼镜
    "🕶️": "sunglasses",     # 太阳镜
    "🥽": "goggles",         # 护目镜
    "🥼": "lab-coat",        # 实验服
    "🦺": "safety-vest",     # 安全背心
    "👔": "necktie",         # 领带
    "👕": "shirt",           # T恤
    "👖": "jeans",           # 牛仔裤
    "🧣": "scarf",           # 围巾
    "🧤": "gloves",          # 手套
    "🧥": "coat",            # 外套
    "🧦": "socks",           # 袜子
    "👗": "dress",           # 连衣裙
    "👘": "kimono",          # 和服
    "🥻": "sari",            # 纱丽
    "🩱": "swimsuit",        # 泳衣
    "🩲": "briefs",          # 内裤
    "🩳": "shorts",          # 短裤
    "👙": "bikini",          # 比基尼
    "👚": "womans-clothes",  # 女装
    "👛": "purse",           # 钱包
    "👜": "handbag",         # 手提包
    "👝": "pouch",           # 小袋子
    "🎒": "backpack",        # 背包
    "🩴": "sandal",          # 凉鞋
    "👞": "shoe",            # 鞋
    "👟": "sneaker",         # 运动鞋
    "🥾": "hiking-boot",     # 登山靴
    "🥿": "flat-shoe",       # 平底鞋
    "👠": "high-heel",       # 高跟鞋
    "👡": "sandal2",         # 凉鞋2
    "🩰": "ballet-shoes",    # 芭蕾舞鞋
    "👢": "boot",            # 靴子
    "👑": "crown",           # 皇冠
    "👒": "hat",             # 帽子
    "🎩": "top-hat",         # 高顶礼帽
    "🎓": "graduation-cap",  # 毕业帽
    "🧢": "cap",             # 鸭舌帽
    "🪖": "military-helmet", # 军用头盔
    "⛑️": "rescue-helmet",  # 救援头盔
    "📿": "prayer-beads",    # 念珠
    "💄": "lipstick",        # 口红
    "💍": "ring",            # 戒指
    "💎": "gem",             # 宝石
}

def fix_xml_file(file_path):
    """修复单个XML文件中的表情符号"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换表情符号
        fixed_content = content
        for emoji, text_icon in EMOJI_MAP.items():
            # 处理可能带有变体选择器的表情符号
            emoji_clean = emoji.strip()
            if emoji_clean:
                fixed_content = fixed_content.replace(emoji_clean, text_icon)
        
        # 如果内容有变化，保存文件
        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"[修复] {file_path}")
            return True
        else:
            print(f"[正常] {file_path}")
            return False
            
    except Exception as e:
        print(f"[错误] {file_path}: {e}")
        return False

def find_xml_files(directory):
    """查找目录下的所有XML文件"""
    xml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    return xml_files

def main():
    # 修复domains目录下的所有XML文件
    domains_dir = Path("E:/Documents/MyGame/domains")
    
    if not domains_dir.exists():
        print(f"错误: 找不到domains目录: {domains_dir}")
        return
    
    print(f"正在扫描目录: {domains_dir}")
    xml_files = find_xml_files(domains_dir)
    
    if not xml_files:
        print("未找到XML文件")
        return
    
    print(f"找到 {len(xml_files)} 个XML文件")
    
    fixed_count = 0
    error_count = 0
    
    for xml_file in xml_files:
        if fix_xml_file(xml_file):
            fixed_count += 1
    
    print(f"\n修复完成:")
    print(f"  扫描文件数: {len(xml_files)}")
    print(f"  修复文件数: {fixed_count}")
    print(f"  错误文件数: {error_count}")

if __name__ == "__main__":
    main()