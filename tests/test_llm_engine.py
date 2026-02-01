import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
sys.path.insert(0, 'E:/Documents/MyGame/.worktrees/mvp-implementation')

from src.llm_engine import LLMEngine


class TestLLMEngineWorldGeneration:
    """测试世界生成功能"""
    
    def test_generate_world_schema_returns_valid_json(self):
        """测试世界生成返回有效的 JSON"""
        with patch.dict('os.environ', {'LLM_API_KEY': 'kimyitao'}):
            with patch('src.llm_engine.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "candidates": [{
                        "content": {
                            "parts": [{
                                "text": json.dumps({
                                    "nodes": [
                                        {"id": "lobby", "label": "Location", "properties": {"name": "大厅"}}
                                    ],
                                    "edges": []
                                })
                            }]
                        }
                    }]
                }
                mock_post.return_value = mock_response
                
                engine = LLMEngine()
                result = engine.generate_world_schema("废弃医院")
                
                assert "nodes" in result
                assert "edges" in result
                assert len(result["nodes"]) > 0
    
    def test_generate_world_schema_handles_api_error(self):
        """测试 API 错误处理"""
        with patch.dict('os.environ', {'LLM_API_KEY': 'kimyitao'}):
            with patch('src.llm_engine.requests.post') as mock_post:
                mock_post.side_effect = Exception("API Error")
                
                engine = LLMEngine()
                # 应该返回备用模板而不是抛出异常
                result = engine.generate_world_schema("测试场景")
                
                assert "nodes" in result  # 返回备用数据


class TestLLMEngineInitialization:
    """测试 LLMEngine 初始化"""
    
    def test_init_reads_api_key_from_env(self):
        """测试从环境变量读取 API 密钥"""
        with patch.dict('os.environ', {'LLM_API_KEY': 'test-key-123'}):
            engine = LLMEngine()
            assert engine.api_key == 'test-key-123'
    
    def test_init_raises_error_without_api_key(self):
        """测试没有 API 密钥时抛出异常"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                engine = LLMEngine()
            assert "必须提供 LLM API 密钥" in str(exc_info.value)
    
    def test_init_uses_provided_api_key(self):
        """测试使用提供的 API 密钥"""
        with patch.dict('os.environ', {}):
            engine = LLMEngine(api_key='custom-key')
            assert engine.api_key == 'custom-key'


class TestLLMEngineIntentParsing:
    """测试意图解析功能"""
    
    def test_interpret_move_intent(self):
        """测试解析移动意图"""
        with patch.dict('os.environ', {'LLM_API_KEY': 'kimyitao'}):
            with patch('src.llm_engine.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "candidates": [{
                        "content": {
                            "parts": [{"text": json.dumps({
                                "intent": "MOVE",
                                "target": "书房",
                                "narrative": "你决定前往书房。"
                            })}]
                        }
                    }]
                }
                mock_post.return_value = mock_response
                
                engine = LLMEngine()
                context = {
                    "location": {"name": "大厅"},
                    "exits": [{"name": "书房"}, {"name": "厨房"}]
                }
                result = engine.interpret_action("去书房", context)
                
                assert result["intent"] == "MOVE"
                assert result["target"] == "书房"
    
    def test_interpret_attack_intent(self):
        """测试解析攻击意图"""
        with patch.dict('os.environ', {'LLM_API_KEY': 'kimyitao'}):
            with patch('src.llm_engine.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "candidates": [{
                        "content": {
                            "parts": [{"text": json.dumps({
                                "intent": "ATTACK",
                                "target": "僵尸",
                                "narrative": "你向僵尸发起攻击！"
                            })}]
                        }
                    }]
                }
                mock_post.return_value = mock_response
                
                engine = LLMEngine()
                context = {"entities": [{"name": "僵尸"}]}
                result = engine.interpret_action("攻击僵尸", context)
                
                assert result["intent"] == "ATTACK"


class TestLLMEngineNarrative:
    def test_generate_narrative_returns_string(self):
        with patch.dict('os.environ', {'LLM_API_KEY': 'kimyitao'}):
            with patch('src.llm_engine.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "candidates": [{"content": {"parts": [{"text": "一道寒光闪过！"}]}}]
                }
                mock_post.return_value = mock_response
                
                engine = LLMEngine()
                result = engine.generate_narrative("攻击", {"damage": 10})
                assert isinstance(result, str)
