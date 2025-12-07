from typing import Any, Optional
from pydantic import BaseModel, Field

class ToolResult(BaseModel):
    output: Optional[Any] = Field(default=None)
    error: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)
    system: Optional[str] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    def __bool__(self):
        return any(getattr(self, field) for field in self.__fields__)

    def __add__(self, other: "ToolResult"):
        def combine_fields(field, other_field, concatenate=True):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("Cannot combine tool results")
            return field or other_field
        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            base64_image=combine_fields(self.base64_image, other.base64_image, False),
            system=combine_fields(self.system, other.system),
        )

    def __str__(self):
        return f"Error: {self.error}" if self.error else str(self.output)

    def __repr__(self):
        return self.__str__()

    def replace(self, **kwargs):
        return type(self)(**{**self.dict(), **kwargs})

class Tool:
    name: str
    description: str
    parameters: dict
    output_type: str
    def __init__(self, *args, **kwargs):
        self.is_initialized = False
    def forward(self, *args, **kwargs):
        raise NotImplementedError("Write this method in your subclass of `Tool`.")
    def __call__(self, *args, **kwargs):
        if not self.is_initialized:
            self.setup()
        return self.forward(*args, **kwargs)
    def setup(self):
        self.is_initialized = True

class AsyncTool(Tool):
    async def forward(self, *args, **kwargs):
        raise NotImplementedError("Write this method in your subclass of `Tool`.")
    async def __call__(self, *args, sanitize_inputs_outputs: bool = False, **kwargs):
        if not self.is_initialized:
            self.setup()
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], dict):
            potential_kwargs = args[0]
            if all(key in self.parameters["properties"] for key in potential_kwargs):
                args = ()
                kwargs = potential_kwargs
        outputs = await self.forward(*args, **kwargs)
        return outputs


# Minimal TOOL registry used by modules that decorate tool classes
class _ToolRegistry:
    def register_module(self, *args, **kwargs):
        def decorator(cls):
            # Optionally, you could store metadata about registered tools here.
            return cls
        return decorator


TOOL = _ToolRegistry()
