import pytest
from unittest.mock import Mock, patch
from src.graph_client import GraphClient


class TestGraphClientConnection:
    """测试 GraphClient 连接功能"""
    
    def test_init_creates_driver(self):
        """测试初始化时创建 Neo4j 驱动"""
        with patch('src.graph_client.GraphDatabase') as mock_db:
            mock_driver = Mock()
            mock_db.driver.return_value = mock_driver
            
            client = GraphClient("bolt://localhost:7687", "neo4j", "password")
            
            mock_db.driver.assert_called_once_with(
                "bolt://localhost:7687", 
                auth=("neo4j", "password")
            )
            assert client.driver == mock_driver
    
    def test_close_invokes_driver_close(self):
        """测试关闭时调用驱动的 close 方法"""
        with patch('src.graph_client.GraphDatabase') as mock_db:
            mock_driver = Mock()
            mock_db.driver.return_value = mock_driver
            
            client = GraphClient("bolt://localhost:7687", "neo4j", "password")
            client.close()
            
            mock_driver.close.assert_called_once()


class TestGraphClientWorldManagement:
    """测试世界管理功能"""
    
    def test_clear_world_deletes_all_nodes(self):
        """测试清空世界删除所有节点和关系"""
        with patch('src.graph_client.GraphDatabase') as mock_db:
            mock_driver = Mock()
            mock_session = Mock()
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=False)
            mock_db.driver.return_value = mock_driver
            
            client = GraphClient("bolt://localhost:7687", "neo4j", "password")
            client.clear_world()
            
            mock_session.run.assert_called_once_with("MATCH (n) DETACH DELETE n")
    
    def test_create_world_with_valid_json(self):
        """测试使用有效 JSON 创建世界"""
        world_json = {
            "nodes": [
                {
                    "id": "lobby",
                    "label": "Location",
                    "properties": {"name": "大厅", "description": "维多利亚式豪宅入口"}
                },
                {
                    "id": "player1",
                    "label": "Player",
                    "properties": {"name": "侦探", "hp": 100}
                }
            ],
            "edges": [
                {
                    "source": "player1",
                    "target": "lobby",
                    "type": "LOCATED_AT",
                    "properties": {}
                }
            ]
        }
        
        with patch('src.graph_client.GraphDatabase') as mock_db:
            mock_driver = Mock()
            mock_session = Mock()
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=False)
            mock_db.driver.return_value = mock_driver
            
            client = GraphClient("bolt://localhost:7687", "neo4j", "password")
            client.create_world(world_json)
            
            # 验证节点创建
            assert mock_session.run.call_count == 3  # 2 nodes + 1 edge


class TestGraphClientPlayerStatus:
    """测试玩家状态查询"""
    
    def test_get_player_status_returns_context(self):
        """测试获取玩家状态返回完整上下文"""
        with patch('src.graph_client.GraphDatabase') as mock_db:
            mock_driver = Mock()
            mock_session = Mock()
            mock_result = Mock()
            
            # 模拟返回数据
            mock_player = {"id": "player1", "name": "侦探", "hp": 100}
            mock_location = {"id": "lobby", "name": "大厅", "description": "入口"}
            mock_exits = [{"id": "library", "name": "书房"}]
            mock_entities = [{"id": "zombie1", "name": "僵尸", "damage": 10}]
            
            mock_result.single.return_value = {
                "player": mock_player,
                "location": mock_location,
                "exits": mock_exits,
                "entities": mock_entities
            }
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=False)
            mock_db.driver.return_value = mock_driver
            
            client = GraphClient("bolt://localhost:7687", "neo4j", "password")
            result = client.get_player_status()
            
            assert result["player"]["name"] == "侦探"
            assert result["location"]["name"] == "大厅"
            assert len(result["exits"]) == 1
            assert len(result["entities"]) == 1


class TestGraphClientActions:
    """测试游戏动作"""
    
    def test_execute_move_to_connected_location(self):
        """测试移动到连通的地点"""
        with patch('src.graph_client.GraphDatabase') as mock_db:
            mock_driver = Mock()
            mock_session = Mock()
            mock_check_result = Mock()
            mock_check_result.single.return_value = {"tgt": {"id": "library"}}
            
            mock_session.run.side_effect = [mock_check_result, None]
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=False)
            mock_db.driver.return_value = mock_driver
            
            client = GraphClient("bolt://localhost:7687", "neo4j", "password")
            success, msg = client.execute_move("书房")
            
            assert success is True
            assert "书房" in msg
    
    def test_execute_move_to_unconnected_location_fails(self):
        """测试移动到不连通的地点失败"""
        with patch('src.graph_client.GraphDatabase') as mock_db:
            mock_driver = Mock()
            mock_session = Mock()
            mock_check_result = Mock()
            mock_check_result.single.return_value = None  # 无连通路径
            
            mock_session.run.return_value = mock_check_result
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=False)
            mock_db.driver.return_value = mock_driver
            
            client = GraphClient("bolt://localhost:7687", "neo4j", "password")
            success, msg = client.execute_move("地下室")
            
            assert success is False
            assert "去不了" in msg or "路不通" in msg
    
    def test_update_player_hp(self):
        """测试更新玩家血量"""
        with patch('src.graph_client.GraphDatabase') as mock_db:
            mock_driver = Mock()
            mock_session = Mock()
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=False)
            mock_db.driver.return_value = mock_driver
            
            client = GraphClient("bolt://localhost:7687", "neo4j", "password")
            client.update_player_hp(-10)
            
            mock_session.run.assert_called_once()
            call_args = mock_session.run.call_args
            assert "hp = p.hp + $delta" in call_args[0][0]
            assert call_args[1]["delta"] == -10
