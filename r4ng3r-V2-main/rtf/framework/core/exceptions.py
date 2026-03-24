"""RedTeam Framework - Custom Exceptions"""

class FrameworkError(Exception): pass
class ModuleError(FrameworkError): pass
class ModuleNotFoundError(ModuleError): pass
class ModuleLoadError(ModuleError): pass
class ModuleExecutionError(ModuleError): pass
class OptionValidationError(ModuleError):
    def __init__(self, option_name: str, message: str = ""):
        self.option_name = option_name
        super().__init__(message or f"Invalid or missing option: {option_name}")
class ToolNotInstalledError(FrameworkError):
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool not installed or not on PATH: {tool_name}")
class WorkflowError(FrameworkError): pass
class SchedulerError(FrameworkError): pass
class RegistryError(FrameworkError): pass
class DatabaseError(FrameworkError): pass
class APIError(FrameworkError): pass
class InstallerError(FrameworkError): pass
