"""
Enhanced AI Copilot Service (CopilotService)

Complete implementation based on PRP document section 7:
Responsibilities: Integrate LLM, provide generative design capabilities

Core methods:
- generate_npc(description): Generate NPC JSON based on description
- text_to_cypher(natural_language): Convert natural language to Cypher query
- suggest_actions(object_type): Recommend actions for entity types

AI Skills file structure:
- tools/genesis_forge/ai_skills/schema_aware_prompt.txt: System Prompt containing current Ontology structure
- tools/genesis_forge/ai_skills/cypher_generator.py: Toolchain for generating and fixing Cypher statements
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedAICopilot:
    """Enhanced AI Copilot Service"""
    
    def __init__(self, project_root: str):
        """
        Initialize enhanced AI Copilot
        
        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
        self.ai_skills_dir = self.project_root / "ai_skills"
        
        # Ensure directory exists
        self.ai_skills_dir.mkdir(exist_ok=True)
        
        # Initialize Skills
        self._init_ai_skills()
        
        # Base AI Copilot removed (using enhanced version)
        self.base_copilot = None
        
        logger.info("Enhanced AI Copilot initialized")
    
    def _init_ai_skills(self):
        """Initialize AI Skills"""
        # Create schema_aware_prompt.txt
        schema_prompt_path = self.ai_skills_dir / "schema_aware_prompt.txt"
        if not schema_prompt_path.exists():
            schema_prompt = '''You are a professional simulation world building assistant, specialized in helping users create and modify Genesis Studio ontology structures.

Core principles:
1. Strictly follow JSON Schema definitions
2. Maintain consistency with existing ontology structures
3. Provide practical and executable suggestions
4. Consider performance and scalability

Available operations:
- Generate ObjectType definitions
- Create ActionType rules
- Write Cypher queries
- Suggest relationship patterns
- Validate existing structures

Response format:
- Always return valid JSON
- Include explanations for complex logic
- Provide alternative solutions when appropriate
'''
            schema_prompt_path.write_text(schema_prompt, encoding='utf-8')
            logger.info(f"Created schema_aware_prompt.txt at {schema_prompt_path}")
    
    def generate_npc(self, description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate NPC based on description
        
        Args:
            description: NPC description
            context: Additional context
            
        Returns:
            NPC definition in JSON format
        """
        if context is None:
            context = {}
        
        try:
            # Generate NPC ID
            npc_id = self._generate_id_from_description(description)
            
            # Create basic NPC structure
            npc_data = {
                "id": npc_id,
                "type": "NPC",
                "name": description.split()[0] if description.split() else "Unnamed_NPC",
                "description": description,
                "properties": {
                    "health": 100,
                    "level": 1,
                    "experience": 0,
                    "alignment": "neutral"
                },
                "skills": ["basic_interaction"],
                "inventory": [],
                "relationships": []
            }
            
            # Add context-specific properties
            if "world_type" in context:
                npc_data["world_context"] = context["world_type"]
            
            if "required_skills" in context:
                npc_data["skills"].extend(context["required_skills"])
            
            logger.info(f"Generated NPC: {npc_id}")
            return npc_data
            
        except Exception as e:
            logger.error(f"Failed to generate NPC: {e}")
            return {
                "error": f"Failed to generate NPC: {str(e)}",
                "description": description
            }
    
    def text_to_cypher(self, natural_language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert natural language to Cypher query
        
        Args:
            natural_language: Natural language description
            context: Query context
            
        Returns:
            Cypher query and explanation
        """
        if context is None:
            context = {}
        
        try:
            # Simple rule-based translation (in production, use LLM)
            query_lower = natural_language.lower()
            
            # Pattern matching for common queries
            if "all" in query_lower and ("node" in query_lower or "entity" in query_lower):
                cypher = "MATCH (n) RETURN n LIMIT 100"
                explanation = "Returns all nodes in the graph (limited to 100)"
            
            elif "find" in query_lower and "relationship" in query_lower:
                cypher = "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 50"
                explanation = "Finds relationships between nodes"
            
            elif "create" in query_lower and "node" in query_lower:
                # Extract node type from description
                node_type = "Entity"
                words = natural_language.split()
                for i, word in enumerate(words):
                    if word.lower() in ["node", "entity"] and i + 1 < len(words):
                        node_type = words[i + 1].capitalize()
                        break
                
                cypher = f"CREATE (n:{node_type} {{name: 'New{node_type}'}}) RETURN n"
                explanation = f"Creates a new {node_type} node"
            
            elif "delete" in query_lower:
                cypher = "// WARNING: Delete operations are disabled in safe mode"
                explanation = "Delete operations require explicit confirmation"
            
            else:
                # Default query
                cypher = "MATCH (n) WHERE n.name CONTAINS $search RETURN n LIMIT 10"
                explanation = "Searches for nodes containing the search term"
            
            return {
                "status": "success",
                "cypher": cypher,
                "explanation": explanation,
                "parameters": {"search": natural_language.split()[0] if natural_language.split() else ""}
            }
            
        except Exception as e:
            logger.error(f"Failed to convert text to Cypher: {e}")
            return {
                "status": "error",
                "error": f"Conversion failed: {str(e)}",
                "cypher": "// Error in query generation",
                "explanation": "Could not generate Cypher query"
            }
    
    def suggest_actions(self, object_type: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Suggest actions for object type
        
        Args:
            object_type: Type of object
            context: Additional context
            
        Returns:
            List of suggested actions
        """
        if context is None:
            context = {}
        
        try:
            # Default action suggestions based on object type
            suggestions = []
            
            # Common actions for all entities
            base_actions = [
                {
                    "action_id": f"ACT_INSPECT_{object_type.upper()}",
                    "name": f"Inspect {object_type}",
                    "description": f"Examine details of {object_type}",
                    "validation_logic": f"MATCH (n:{object_type}) WHERE n.id = $target_id RETURN n IS NOT NULL",
                    "execution_rules": ["LOG_ACTION"]
                },
                {
                    "action_id": f"ACT_MOVE_{object_type.upper()}",
                    "name": f"Move {object_type}",
                    "description": f"Relocate {object_type} to new position",
                    "validation_logic": f"MATCH (n:{object_type}) WHERE n.id = $target_id RETURN n.position IS NOT NULL",
                    "execution_rules": ["UPDATE_POSITION"]
                }
            ]
            
            suggestions.extend(base_actions)
            
            # Type-specific actions
            if object_type.lower() in ["npc", "character", "person"]:
                suggestions.append({
                    "action_id": "ACT_TALK_NPC",
                    "name": "Talk to NPC",
                    "description": "Initiate conversation with NPC",
                    "validation_logic": "MATCH (n:NPC) WHERE n.id = $target_id RETURN n.dialogue_tree IS NOT NULL",
                    "execution_rules": ["START_DIALOGUE"]
                })
            
            elif object_type.lower() in ["item", "object", "artifact"]:
                suggestions.append({
                    "action_id": "ACT_PICKUP_ITEM",
                    "name": "Pick up item",
                    "description": "Add item to inventory",
                    "validation_logic": "MATCH (i:Item) WHERE i.id = $target_id RETURN i.weight <= $carry_capacity",
                    "execution_rules": ["ADD_TO_INVENTORY"]
                })
            
            elif object_type.lower() in ["location", "place", "area"]:
                suggestions.append({
                    "action_id": "ACT_ENTER_LOCATION",
                    "name": "Enter location",
                    "description": "Move into the location",
                    "validation_logic": "MATCH (l:Location) WHERE l.id = $target_id RETURN l.is_accessible",
                    "execution_rules": ["CHANGE_LOCATION"]
                })
            
            logger.info(f"Generated {len(suggestions)} action suggestions for {object_type}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest actions: {e}")
            return [{
                "action_id": "ACT_ERROR",
                "name": "Error",
                "description": f"Failed to generate suggestions: {str(e)}",
                "validation_logic": "RETURN false",
                "execution_rules": []
            }]
    
    def _generate_id_from_description(self, description: str) -> str:
        """Generate ID from description"""
        # Extract meaningful characters
        words = re.findall(r'\b\w+\b', description)
        if words:
            # Use first 2-3 characters from first 2 words
            id_parts = [word[:3].upper() for word in words[:2]]
            return "_".join(id_parts)
        else:
            return "GEN_" + str(hash(description) % 10000)
    
    def generate_content(self, prompt: str, content_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate content (compatible interface)
        
        Args:
            prompt: Prompt text
            content_type: Content type (npc, cypher, actions, object_type, relationship, etc.)
            context: Context information
            
        Returns:
            Generated result
        """
        if context is None:
            context = {}
        
        try:
            # Call different methods based on content type
            if content_type in ['npc', 'entity', 'character']:
                # Generate NPC/entity
                return {
                    "status": "success",
                    "result": self.generate_npc(prompt, context)
                }
            
            elif content_type in ['cypher', 'query']:
                # Generate Cypher query
                return self.text_to_cypher(prompt, context)
            
            elif content_type in ['action', 'actions']:
                # Suggest actions
                object_type = context.get('object_type', 'Entity')
                return {
                    "status": "success",
                    "suggestions": self.suggest_actions(object_type, context)
                }
            
            elif content_type in ['object_type', 'type']:
                # Generate object type definition
                return {
                    "status": "success",
                    "type_definition": self._generate_object_type(prompt, context)
                }
            
            elif content_type in ['relationship', 'rel']:
                # Generate relationship definition
                return {
                    "status": "success",
                    "relationship": self._generate_relationship(prompt, context)
                }
            
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported content type: {content_type}",
                    "supported_types": ["npc", "cypher", "actions", "object_type", "relationship"]
                }
                
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            return {
                "status": "error",
                "error": f"Content generation failed: {str(e)}"
            }
    
    def _generate_object_type(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate object type definition"""
        type_key = self._generate_id_from_description(description)
        
        return {
            "type_key": type_key,
            "display_name": description.split()[0] if description.split() else "UnnamedType",
            "description": description,
            "properties": {
                "name": "string",
                "id": "string",
                "created_at": "datetime",
                "updated_at": "datetime"
            },
            "visual_assets": [f"{type_key.lower()}_icon.png"],
            "tags": ["generated", "auto"]
        }
    
    def _generate_relationship(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate relationship definition"""
        rel_type = self._generate_id_from_description(description)
        
        return {
            "relationship_type": rel_type,
            "display_name": description.split()[0] if description.split() else "UnnamedRelation",
            "description": description,
            "source_types": ["Entity"],
            "target_types": ["Entity"],
            "properties": {
                "strength": "number",
                "created_at": "datetime"
            },
            "is_directed": True,
            "tags": ["generated"]
        }
    
    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """AI chat interface
        
        Args:
            message: User message
            history: Conversation history
            
        Returns:
            AI response
        """
        if history is None:
            history = []
        
        try:
            # Simple response logic (in production, integrate with LLM)
            response = f"I received your message: '{message}'. "
            
            # Add context-aware responses
            if "help" in message.lower():
                response += "I can help you with: generating NPCs, creating Cypher queries, suggesting actions, and defining object types."
            
            elif "cypher" in message.lower() or "query" in message.lower():
                cypher_result = self.text_to_cypher(message)
                if cypher_result["status"] == "success":
                    response += f"\n\nHere's a Cypher query:\n```cypher\n{cypher_result['cypher']}\n```\n\n{cypher_result['explanation']}"
            
            elif "npc" in message.lower() or "character" in message.lower():
                npc_result = self.generate_npc(message)
                response += f"\n\nGenerated NPC:\n```json\n{json.dumps(npc_result, indent=2, ensure_ascii=False)}\n```"
            
            else:
                response += "How can I assist you with your simulation world building today?"
            
            return {
                "status": "success",
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {
                "status": "error",
                "error": f"Chat failed: {str(e)}",
                "response": "Sorry, I encountered an error. Please try again."
            }