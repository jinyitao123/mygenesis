"""测试 LLM 世界生成"""
import os
from dotenv import load_dotenv
from src.llm_engine import LLMEngine
import json

load_dotenv()

llm = LLMEngine()

scenario = "战国时代，我是史官"
print(f"测试场景: {scenario}\n")

world_json = llm.generate_world_schema(scenario)

print("生成的 JSON 结构:")
print(json.dumps(world_json, ensure_ascii=False, indent=2))
