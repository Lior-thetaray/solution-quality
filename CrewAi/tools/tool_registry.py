"""
Tool Registry
Centralized tool management to avoid duplicate instantiation
"""

from typing import Dict, List, Any
from tools.code_analysis_tools import (
    PythonFeatureAnalyzerTool,
    YAMLConfigAnalyzerTool,
    DatasetAnalyzerTool,
    DAGAnalyzerTool,
    NotebookAnalyzerTool
)
from tools.csv_tools import CSVDatasetReaderTool, CSVListTool
from tools.alert_analysis_tools import JoinDatasetsTool, AggregateDatasetTool, CrossTableAnalysisTool


class ToolRegistry:
    """Singleton registry for tool instances"""
    
    _instance = None
    _tools: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._initialize_tools()
        return cls._instance
    
    def _initialize_tools(self):
        """Initialize all tool instances once"""
        # SDLC tools
        self._tools['python_feature_analyzer'] = PythonFeatureAnalyzerTool()
        self._tools['yaml_config_analyzer'] = YAMLConfigAnalyzerTool()
        self._tools['dataset_analyzer'] = DatasetAnalyzerTool()
        self._tools['dag_analyzer'] = DAGAnalyzerTool()
        self._tools['notebook_analyzer'] = NotebookAnalyzerTool()
        
        # CSV tools (shared between alert validation and potentially others)
        self._tools['csv_list'] = CSVListTool()
        self._tools['csv_reader'] = CSVDatasetReaderTool()
        
        # Alert analysis tools
        self._tools['join_datasets'] = JoinDatasetsTool()
        self._tools['aggregate_dataset'] = AggregateDatasetTool()
        self._tools['cross_table_analysis'] = CrossTableAnalysisTool()
    
    def get_tools_for_agent(self, agent_type: str) -> List[Any]:
        """Get tool instances for a specific agent type"""
        if agent_type == "sdlc":
            return [
                self._tools['python_feature_analyzer'],
                self._tools['yaml_config_analyzer'],
                self._tools['dataset_analyzer'],
                self._tools['dag_analyzer'],
                self._tools['notebook_analyzer'],
            ]
        elif agent_type == "alert_validation":
            return [
                self._tools['csv_list'],
                self._tools['csv_reader'],
                self._tools['join_datasets'],
                self._tools['aggregate_dataset'],
                self._tools['cross_table_analysis'],
            ]
        elif agent_type == "orchestrator":
            # Orchestrator might need access to all tools or subset
            return list(self._tools.values())
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    def get_tool(self, tool_name: str) -> Any:
        """Get a specific tool by name"""
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        return self._tools[tool_name]
    
    def add_custom_tool(self, name: str, tool_instance: Any):
        """Add a custom tool to the registry"""
        if name in self._tools:
            print(f"⚠️  Warning: Overwriting existing tool '{name}'")
        self._tools[name] = tool_instance
    
    def get_all_tools(self) -> Dict[str, Any]:
        """Get all registered tools"""
        return self._tools.copy()
    
    def get_shared_tools(self, agent_types: List[str]) -> List[Any]:
        """Get tools that are shared between multiple agent types"""
        if not agent_types:
            return []
        
        # Get tool name sets for each agent (use names instead of instances)
        tool_name_sets = []
        for agent_type in agent_types:
            tools = self.get_tools_for_agent(agent_type)
            tool_names = {name for name, tool in self._tools.items() if tool in tools}
            tool_name_sets.append(tool_names)
        
        # Find intersection (shared tool names)
        shared_names = set.intersection(*tool_name_sets) if tool_name_sets else set()
        
        # Return actual tool instances
        return [self._tools[name] for name in shared_names]
    
    def get_tool_usage_stats(self, agent_types: List[str]) -> Dict[str, Any]:
        """Get statistics about tool usage across agents"""
        stats = {
            'total_tools': len(self._tools),
            'tools_by_agent': {},
            'shared_tools': [],
            'unique_tools_per_agent': {}
        }
        
        all_tool_names_used = set()
        
        for agent_type in agent_types:
            tools = self.get_tools_for_agent(agent_type)
            tool_names = [name for name, tool in self._tools.items() if tool in tools]
            stats['tools_by_agent'][agent_type] = {
                'count': len(tools),
                'tools': tool_names
            }
            all_tool_names_used.update(tool_names)
        
        # Find shared tools
        if len(agent_types) > 1:
            shared_tools = self.get_shared_tools(agent_types)
            shared_names = [name for name, tool in self._tools.items() if tool in shared_tools]
            stats['shared_tools'] = shared_names
            
            # Find unique tools per agent
            for agent_type in agent_types:
                agent_tool_names = {name for name, tool in self._tools.items() 
                                   if tool in self.get_tools_for_agent(agent_type)}
                shared_tool_names = set(shared_names)
                unique_names = list(agent_tool_names - shared_tool_names)
                stats['unique_tools_per_agent'][agent_type] = unique_names
        
        stats['total_tools_used'] = len(all_tool_names_used)
        stats['tool_reuse_savings'] = len(self._tools) - len(all_tool_names_used)
        
        return stats


# Global registry instance
_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    return _registry


def get_tools_for_agent(agent_type: str) -> List[Any]:
    """Convenience function to get tools for an agent"""
    return _registry.get_tools_for_agent(agent_type)
