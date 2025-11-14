"""
T060e: CorrelationIdManager - Manage correlation IDs for distributed tracing
"""
import uuid
import threading
from typing import Dict, Any, Optional
from contextvars import ContextVar
from datetime import datetime


class CorrelationIdManager:
    """Manage correlation IDs for distributed tracing across services"""
    
    # Thread-local storage for correlation context
    _local = threading.local()
    
    # Context variables for async support
    _correlation_context: ContextVar[Dict[str, Any]] = ContextVar(
        'correlation_context', 
        default={}
    )
    
    def __init__(self):
        """Initialize correlation ID manager"""
        pass
    
    def generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req-{uuid.uuid4().hex[:8]}"
    
    def generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        return f"trace-{uuid.uuid4().hex[:12]}"
    
    def generate_span_id(self) -> str:
        """Generate unique span ID"""
        return f"span-{uuid.uuid4().hex[:8]}"
    
    def create_span(
        self,
        parent_id: str,
        operation_name: str,
        user_id: str,
        trace_id: Optional[str] = None
    ) -> str:
        """Create new span with parent reference
        
        Args:
            parent_id: Parent span or request ID
            operation_name: Name of the operation
            user_id: User identifier
            trace_id: Optional trace ID (generates if not provided)
            
        Returns:
            New span ID
        """
        # Generate span ID
        span_id = self.generate_span_id()
        
        # Get or create trace ID
        if trace_id is None:
            trace_id = self.generate_trace_id()
        
        # Get current context
        context = self.get_current_context()
        
        # Update context with new span
        context.update({
            "span_id": span_id,
            "parent_id": parent_id,
            "operation_context": operation_name,
            "trace_id": trace_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Set updated context
        self.set_correlation_context(context)
        
        return span_id
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current correlation context"""
        return self._correlation_context.get()
    
    def set_correlation_context(self, context: Dict[str, Any]):
        """Set correlation context"""
        self._correlation_context.set(context)
    
    def set_user_context(self, user_id: str):
        """Set user context for correlation"""
        context = self.get_current_context()
        context["user_id"] = user_id
        self.set_correlation_context(context)
    
    def set_request_id(self, request_id: str):
        """Set request ID in context"""
        context = self.get_current_context()
        context["request_id"] = request_id
        self.set_correlation_context(context)
    
    def get_correlation_id(self) -> str:
        """Get current correlation ID (request_id or span_id)"""
        context = self.get_current_context()
        return context.get("request_id") or context.get("span_id")
    
    def clear_context(self):
        """Clear correlation context"""
        self._correlation_context.set({})
    
    def get_operation_name(self) -> Optional[str]:
        """Get current operation name"""
        context = self.get_current_context()
        return context.get("operation_context")
    
    def propagate_context(self) -> Dict[str, str]:
        """Get context for propagation to other services"""
        context = self.get_current_context()
        return {
            "trace_id": context.get("trace_id", ""),
            "span_id": context.get("span_id", ""),
            "parent_id": context.get("parent_id", ""),
            "user_id": context.get("user_id", ""),
            "request_id": context.get("request_id", "")
        }
    
    def import_context(self, context_dict: Dict[str, str]):
        """Import context from another service"""
        context = self.get_current_context()
        
        # Preserve existing data
        if "user_id" not in context and "user_id" in context_dict:
            context["user_id"] = context_dict["user_id"]
        
        # Update trace/span IDs
        if "trace_id" in context_dict:
            context["trace_id"] = context_dict["trace_id"]
        if "span_id" in context_dict:
            context["span_id"] = context_dict["span_id"]
        if "parent_id" in context_dict:
            context["parent_id"] = context_dict["parent_id"]
        if "request_id" in context_dict:
            context["request_id"] = context_dict["request_id"]
        
        self.set_correlation_context(context)


class CorrelationIdMiddleware:
    """FastAPI middleware for automatic correlation ID injection"""
    
    def __init__(self, manager: CorrelationIdManager):
        self.manager = manager
    
    async def __call__(self, request, call_next):
        """Middleware to extract/create correlation IDs"""
        # Try to get correlation ID from headers
        correlation_id = (
            request.headers.get("X-Correlation-ID") or
            request.headers.get("X-Request-ID") or
            self.manager.generate_request_id()
        )
        
        # Get trace ID from headers
        trace_id = (
            request.headers.get("X-Trace-ID") or
            self.manager.generate_trace_id()
        )
        
        # Set context
        self.manager.set_request_id(correlation_id)
        self.manager.set_correlation_context({
            "trace_id": trace_id,
            "request_id": correlation_id,
            "operation_context": f"{request.method} {request.url.path}"
        })
        
        # Add user ID if available
        if hasattr(request.state, 'user_id'):
            self.manager.set_user_context(request.state.user_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation headers to response
        context = self.manager.get_current_context()
        response.headers["X-Correlation-ID"] = context.get("request_id", "")
        response.headers["X-Trace-ID"] = context.get("trace_id", "")
        
        # Clean up context
        self.manager.clear_context()
        
        return response


class SpanContext:
    """Context manager for span creation and cleanup"""
    
    def __init__(
        self,
        manager: CorrelationIdManager,
        operation_name: str,
        user_id: str
    ):
        self.manager = manager
        self.operation_name = operation_name
        self.user_id = user_id
        self.parent_span = None
        self.span_id = None
    
    def __enter__(self):
        """Enter span context"""
        # Get current context
        current_context = self.manager.get_current_context()
        
        # Determine parent ID
        parent_id = (
            current_context.get("span_id") or
            current_context.get("request_id") or
            self.manager.generate_request_id()
        )
        
        # Create new span
        self.span_id = self.manager.create_span(
            parent_id=parent_id,
            operation_name=self.operation_name,
            user_id=self.user_id
        )
        
        return self.span_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit span context"""
        # Could log span completion here
        pass
