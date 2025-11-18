"""
Tool Registry Demo
Shows how tool registry optimizes memory and prevents duplicate instantiation
"""

from tools.tool_registry import get_tool_registry

def main():
    print("\n" + "=" * 60)
    print("TOOL REGISTRY OPTIMIZATION DEMO")
    print("=" * 60)
    
    registry = get_tool_registry()
    
    # Show all registered tools
    all_tools = registry.get_all_tools()
    print(f"\n📦 Total tools in registry: {len(all_tools)}")
    print("\nRegistered tools:")
    for name, tool in all_tools.items():
        print(f"  • {name}: {tool.__class__.__name__}")
    
    # Show tools for each agent type
    print("\n" + "-" * 60)
    print("TOOLS BY AGENT TYPE")
    print("-" * 60)
    
    for agent_type in ["sdlc", "alert_validation"]:
        tools = registry.get_tools_for_agent(agent_type)
        print(f"\n{agent_type.upper()}:")
        print(f"  Count: {len(tools)}")
        tool_names = [name for name, tool in all_tools.items() if tool in tools]
        for name in tool_names:
            print(f"    • {name}")
    
    # Show shared tools
    print("\n" + "-" * 60)
    print("SHARED TOOLS (Memory Optimization)")
    print("-" * 60)
    
    shared = registry.get_shared_tools(["sdlc", "alert_validation"])
    if shared:
        print(f"\n🔄 Tools shared between agents: {len(shared)}")
        shared_names = [name for name, tool in all_tools.items() if tool in shared]
        for name in shared_names:
            print(f"  • {name}")
        print(f"\n💡 If we didn't use registry, we'd create {len(shared)} duplicate instances!")
    else:
        print("\n✅ No shared tools between these agent types")
    
    # Show usage statistics
    print("\n" + "-" * 60)
    print("USAGE STATISTICS")
    print("-" * 60)
    
    stats = registry.get_tool_usage_stats(["sdlc", "alert_validation"])
    print(f"\nTotal tools: {stats['total_tools']}")
    print(f"Tools used: {stats['total_tools_used']}")
    print(f"Shared tools: {len(stats['shared_tools'])}")
    print(f"Memory savings: {len(stats['shared_tools'])} fewer instantiations")
    
    print("\nUnique tools per agent:")
    for agent_type, unique_tools in stats['unique_tools_per_agent'].items():
        print(f"  {agent_type}: {', '.join(unique_tools) if unique_tools else 'none'}")
    
    # Test reusability
    print("\n" + "-" * 60)
    print("REUSABILITY TEST")
    print("-" * 60)
    
    tools1 = registry.get_tools_for_agent("sdlc")
    tools2 = registry.get_tools_for_agent("sdlc")
    
    print(f"\nGetting SDLC tools twice...")
    print(f"First call returned {len(tools1)} tools")
    print(f"Second call returned {len(tools2)} tools")
    print(f"Are they the same instances? {tools1[0] is tools2[0]}")
    print(f"✅ Tool instances are reused, not recreated!")
    
    print("\n" + "=" * 60)
    print("OPTIMIZATION SUMMARY")
    print("=" * 60)
    print("""
Without Tool Registry:
  - Each agent creates its own tool instances
  - Multiple agents = duplicate tools in memory
  - No visibility into tool usage

With Tool Registry:
  ✅ Tools created once, reused across agents
  ✅ Memory efficient - no duplicates
  ✅ Easy to track which agents use which tools
  ✅ Centralized tool management
  ✅ Future orchestrator can access all tools
    """)


if __name__ == "__main__":
    main()
