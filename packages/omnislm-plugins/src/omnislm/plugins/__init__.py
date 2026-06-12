"""
OmniSLM Plugins — Plugin system for extending OmniSLM.

Provides plugin discovery, lifecycle management, and built-in tools.
"""

from omnislm.plugins.registry import PluginRegistry
from omnislm.plugins.discovery import PluginDiscovery
from omnislm.plugins.lifecycle import PluginLifecycleManager

__all__ = ["PluginRegistry", "PluginDiscovery", "PluginLifecycleManager"]
