"""
Architecture Boundary Validation
"""
import inspect
from functools import wraps
from typing import List, Set, Tuple


class LayerViolation(Exception):
    """Raised when architecture layer boundaries are violated"""
    pass


class ArchitectureValidator:
    """Validates architectural layer boundaries"""

    # Define allowed dependencies
    ALLOWED_DEPENDENCIES = {
        'ui': ['application'],
        'application': ['domain', 'infrastructure'],
        'domain': [],  # Domain should not depend on infrastructure
        'infrastructure': []
    }

    _module_layers: dict = {}
    _checked_modules: Set[str] = set()

    @classmethod
    def register_module_layer(cls, module_path: str, layer: str):
        """Register a module to a specific layer"""
        cls._module_layers[module_path] = layer

    @classmethod
    def validate_layer_dependency(cls, caller_module: str, called_module: str):
        """Validate that a dependency is allowed"""
        if caller_module in cls._checked_modules:
            return

        caller_layer = cls._module_layers.get(caller_module.split('.')[0])
        called_layer = cls._module_layers.get(called_module.split('.')[0])

        if caller_layer and called_layer:
            if called_layer not in cls.ALLOWED_DEPENDENCIES.get(caller_layer, []):
                raise LayerViolation(
                    f"Layer violation: {caller_layer} module '{caller_module}' "
                    f"cannot depend on {called_layer} module '{called_module}'"
                )

        cls._checked_modules.add(caller_module)


def validate_architecture(func):
    """Decorator to validate architecture boundaries"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get calling module
        frame = inspect.currentframe().f_back
        calling_module = frame.f_globals.get('__name__', '')

        # In a real implementation, we would check all imports
        # For now, this is a placeholder

        return func(*args, **kwargs)

    return wrapper


# Register core modules to layers
ArchitectureValidator.register_module_layer('src.domain', 'domain')
ArchitectureValidator.register_module_layer('src.application', 'application')
ArchitectureValidator.register_module_layer('src.infrastructure', 'infrastructure')
ArchitectureValidator.register_module_layer('src.dashboard', 'ui')
