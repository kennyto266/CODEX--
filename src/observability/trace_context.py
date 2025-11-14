"""
Distributed Tracing Infrastructure (T060k)

This module provides the core infrastructure for distributed tracing across
the quantitative trading system. It implements trace context management,
span lifecycle control, and context propagation.

Key Components:
- TraceContext: Represents a single trace span with timing and metadata
- TraceManager: Manages trace context across the application
- TraceLog: Structured log entries attached to spans

Author: Claude Code
Version: 1.0.0
"""

import time
import uuid
import threading
from typing import Dict, List, Any, Optional, NamedTuple
from contextlib import contextmanager


class TraceLog(NamedTuple):
    """Structured log entry for a trace span"""
    timestamp: float
    event: str
    payload: Optional[Dict[str, Any]] = None


class TraceContext:
    """
    Represents a distributed trace context (span).

    A TraceContext tracks the execution of a single operation including:
    - Timing information (start time, duration)
    - Metadata (tags, logs)
    - Parent-child relationships
    - User context

    This class is thread-safe and can be used in both sync and async contexts.
    """

    def __init__(
        self,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation_name: Optional[str] = None
    ):
        """
        Initialize a new trace context.

        Args:
            trace_id: Unique identifier for the entire trace
            span_id: Unique identifier for this span
            parent_span_id: ID of parent span (for hierarchical tracing)
            user_id: ID of user who initiated this operation
            operation_name: Human-readable name for this operation
        """
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.user_id = user_id
        self.operation_name = operation_name or "unknown_operation"
        self.start_time = time.time()
        self.finish_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.status: str = "OK"

        # Metadata storage
        self.tags: Dict[str, Any] = {}
        self.logs: List[TraceLog] = []
        self.children: List['TraceContext'] = []

        # Thread safety
        self._lock = threading.RLock()

    def add_tag(self, key: str, value: Any) -> None:
        """
        Add a tag to this span.

        Tags are key-value pairs that provide additional context about the operation.
        They are used for querying and aggregating traces.

        Args:
            key: Tag key (e.g., "symbol", "strategy_type", "user_id")
            value: Tag value (must be JSON-serializable)
        """
        with self._lock:
            self.tags[key] = value

    def add_log(self, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a log event to this span.

        Log events record specific moments or milestones during span execution.
        Unlike tags, logs are ordered chronologically and can have complex payloads.

        Args:
            event: Event name (e.g., "data_loaded", "error", "strategy_completed")
            payload: Optional event payload with additional details
        """
        with self._lock:
            log_entry = TraceLog(
                timestamp=time.time(),
                event=event,
                payload=payload
            )
            self.logs.append(log_entry)

    def finish(self, status: str = "OK", error: Optional[Exception] = None) -> None:
        """
        Finish this span and calculate duration.

        This method should be called when the operation completes. It calculates
        the total duration and marks the span with the final status.

        Args:
            status: Final status ("OK", "ERROR", "TIMEOUT", etc.)
            error: Optional exception that occurred during execution
        """
        with self._lock:
            self.finish_time = time.time()
            self.duration = self.finish_time - self.start_time
            self.status = status

            # Log error if provided
            if error is not None:
                self.add_log("error", {
                    "exception_type": type(error).__name__,
                    "exception_message": str(error),
                    "status": status
                })

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert span to dictionary for serialization.

        Returns:
            Dictionary representation of the span
        """
        with self._lock:
            return {
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "parent_span_id": self.parent_span_id,
                "operation_name": self.operation_name,
                "user_id": self.user_id,
                "start_time": self.start_time,
                "finish_time": self.finish_time,
                "duration": self.duration,
                "status": self.status,
                "tags": self.tags.copy(),
                "logs": [
                    {
                        "timestamp": log.timestamp,
                        "event": log.event,
                        "payload": log.payload
                    }
                    for log in self.logs
                ],
                "child_count": len(self.children)
            }

    def __repr__(self) -> str:
        """String representation of TraceContext"""
        return (
            f"TraceContext(trace_id={self.trace_id[:8]}..., "
            f"span_id={self.span_id[:8]}..., "
            f"operation={self.operation_name}, "
            f"status={self.status})"
        )


class TraceManager:
    """
    Manages trace context across the application.

    The TraceManager is responsible for:
    - Creating and managing trace spans
    - Maintaining a stack for nested operations
    - Generating unique IDs
    - Propagating context between components
    - Providing thread-local context

    This class is thread-safe and uses thread-local storage to maintain
    separate trace contexts for each thread.
    """

    _local = threading.local()

    def __init__(self):
        """Initialize the trace manager"""
        self._span_stack: List[TraceContext] = []

    @classmethod
    def get_instance(cls) -> 'TraceManager':
        """
        Get thread-local instance of TraceManager.

        Ensures each thread has its own trace manager instance.

        Returns:
            Thread-local TraceManager instance
        """
        if not hasattr(cls._local, 'trace_manager'):
            cls._local.trace_manager = cls()
        return cls._local.trace_manager

    def start_span(
        self,
        operation_name: str,
        user_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> TraceContext:
        """
        Start a new trace span.

        This method creates a new trace context as a child of the current span
        (if any). The new span becomes the current active span.

        Args:
            operation_name: Name of the operation being traced
            user_id: Optional user ID who initiated this operation
            tags: Optional initial tags for this span

        Returns:
            The newly created TraceContext
        """
        # Generate unique span ID
        span_id = str(uuid.uuid4())

        # Get parent span (current context)
        parent_span = self._span_stack[-1] if self._span_stack else None
        parent_span_id = parent_span.span_id if parent_span else None

        # Determine trace ID: inherit from parent or generate new
        if parent_span:
            trace_id = parent_span.trace_id
        else:
            trace_id = str(uuid.uuid4())

        # Create the span
        span = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            user_id=user_id,
            operation_name=operation_name
        )

        # Add initial tags
        if tags:
            for key, value in tags.items():
                span.add_tag(key, value)

        # Add to hierarchy
        if parent_span_id:
            parent = self._span_stack[-1]
            with parent._lock:
                parent.children.append(span)

        # Push to stack
        self._span_stack.append(span)

        return span

    def finish_span(
        self,
        status: str = "OK",
        error: Optional[Exception] = None
    ) -> Optional[TraceContext]:
        """
        Finish the current span.

        This method pops the current span from the stack, calculates its
        duration, and marks it as finished. The parent span (if any) becomes
        the current active span.

        Args:
            status: Final status of the span
            error: Optional exception that occurred

        Returns:
            The finished span, or None if no span was active
        """
        if not self._span_stack:
            return None

        span = self._span_stack.pop()
        span.finish(status=status, error=error)
        return span

    def get_current_context(self) -> Optional[TraceContext]:
        """
        Get the current active trace context.

        Returns:
            Current TraceContext, or None if no span is active
        """
        if self._span_stack:
            return self._span_stack[-1]
        return None

    def propagate_context(self) -> Dict[str, str]:
        """
        Get headers for context propagation.

        This method returns a dictionary of headers that should be passed
        to remote services or async boundaries to maintain trace continuity.

        Returns:
            Dictionary of trace headers for propagation
        """
        context = self.get_current_context()
        if context is None:
            return {}

        headers = {
            "X-Trace-Id": context.trace_id,
            "X-Span-Id": context.span_id,
            "X-Parent-Span-Id": context.parent_span_id or "",
        }

        if context.user_id:
            headers["X-User-Id"] = context.user_id

        if context.operation_name:
            headers["X-Operation-Name"] = context.operation_name

        return headers

    @contextmanager
    def span(
        self,
        operation_name: str,
        user_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for span lifecycle.

        This is a convenience method that automatically starts and finishes
        a span using a context manager pattern.

        Example:
            with trace_manager.span("data_loading", user_id="user123") as span:
                # Operation code here
                span.add_tag("data_points", 1000)

        Args:
            operation_name: Name of the operation
            user_id: Optional user ID
            tags: Optional initial tags

        Yields:
            The created TraceContext
        """
        span = self.start_span(operation_name, user_id, tags)
        try:
            yield span
        except Exception as e:
            span.finish(status="ERROR", error=e)
            raise
        else:
            span.finish(status="OK")

    def get_trace_tree(self) -> Optional[Dict[str, Any]]:
        """
        Get the complete trace tree as a dictionary.

        Returns:
            Root span with all children, or None if no trace is active
        """
        context = self.get_current_context()
        if context is None or not self._span_stack:
            return None

        # Find root span
        root = self._span_stack[0]
        return self._serialize_tree(root)

    def _serialize_tree(self, span: TraceContext) -> Dict[str, Any]:
        """Recursively serialize a trace tree"""
        with span._lock:
            return {
                "span": span.to_dict(),
                "children": [
                    self._serialize_tree(child)
                    for child in span.children
                ]
            }

    def clear(self) -> None:
        """
        Clear all spans from the stack.

        This should be used with caution as it doesn't properly finish spans.
        It's mainly useful for testing or cleaning up after errors.
        """
        self._span_stack.clear()


# Convenience function for getting trace manager
def get_trace_manager() -> TraceManager:
    """
    Get the global trace manager instance.

    Returns:
        Thread-local TraceManager instance
    """
    return TraceManager.get_instance()


# Export public API
__all__ = [
    'TraceContext',
    'TraceLog',
    'TraceManager',
    'get_trace_manager'
]
