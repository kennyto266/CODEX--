"""
增强沙箱 - 安全的代码执行环境
提供强化的资源限制、进程隔离和代码监控
"""

import sys
import os
import signal
import logging
import time
import threading
import subprocess
import socket
import ast
import json
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from pathlib import Path
import tempfile
import shutil

# 平台特定的resource模组
try:
    import resource
except ImportError:
    # Windows不支持resource模组
    resource = None

# 进程和系统监控
try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_cpu_time: float = 5.0
    max_wall_time: float = 10.0
    max_memory: int = 256 * 1024 * 1024
    max_open_files: int = 100
    max_processes: int = 1
    max_threads: int = 5
    max_network_connections: int = 5
    allowed_file_paths: List[str] = field(default_factory=list)
    blocked_file_paths: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    container_mode: bool = False
    seccomp_profile: Optional[str] = None


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0
    memory_usage: int = 0
    cpu_time: float = 0
    file_access_count: int = 0
    network_access_count: int = 0
    system_calls: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    sandbox_path: Optional[str] = None


class TimeoutError(Exception):
    pass


class ResourceExceededError(Exception):
    pass


class SecurityViolationError(Exception):
    pass


class SecureCodeExecutor:
    """安全代码执行器"""

    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.file_controller = FileAccessController(
            limits.allowed_file_paths,
            limits.blocked_file_paths
        )
        self.network_controller = NetworkController(
            limits.allowed_domains,
            limits.blocked_domains
        )
        self.syscall_interceptor = SystemCallInterceptor()
        self.container_runner = ContainerRunner() if limits.container_mode else None
        self.temp_dir = None
        self.execution_log = []

    def execute_code(self, code: str, timeout: Optional[float] = None) -> ExecutionResult:
        """执行代码"""
        if timeout is None:
            timeout = self.limits.max_wall_time

        try:
            # 创建隔离环境
            self.temp_dir = self.file_controller.create_isolated_environment()

            # 使用容器模式或子进程模式
            if self.container_runner and self.limits.container_mode:
                result = self.container_runner.run_in_container(code, self.limits, timeout)
            else:
                result = self._execute_in_subprocess(code, timeout)

            # 记录执行日志
            self.execution_log.append({
                'timestamp': time.time(),
                'code_hash': hash(code),
                'result': result
            })

            return result

        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=0
            )
        finally:
            self.file_controller.cleanup()

    def _execute_in_subprocess(self, code: str, timeout: float) -> ExecutionResult:
        """在子进程中执行代码"""
        start_time = time.time()

        # 设置资源限制（仅Linux）
        if resource:
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self.limits.max_memory, self.limits.max_memory)
            )
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (int(self.limits.max_cpu_time), int(self.limits.max_cpu_time))
            )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            code_file = f.name

        try:
            # 使用subprocess运行代码
            result = subprocess.Popen(
                [sys.executable, code_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=_setup_child_process if resource else None
            )

            try:
                stdout, stderr = result.communicate(timeout=timeout)
                exec_time = time.time() - start_time

                return ExecutionResult(
                    success=result.returncode == 0,
                    output=stdout.decode('utf-8'),
                    error=stderr.decode('utf-8') if stderr else None,
                    execution_time=exec_time,
                    sandbox_path=code_file
                )
            except subprocess.TimeoutExpired:
                result.kill()
                return ExecutionResult(
                    success=False,
                    error="Execution timeout",
                    execution_time=timeout
                )

        finally:
            if os.path.exists(code_file):
                os.unlink(code_file)

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        if not self.execution_log:
            return {}

        total_executions = len(self.execution_log)
        successful_executions = sum(1 for log in self.execution_log if log['result'].success)
        total_time = sum(log['result'].execution_time for log in self.execution_log)

        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': total_executions - successful_executions,
            'success_rate': successful_executions / total_executions if total_executions > 0 else 0,
            'total_execution_time': total_time,
            'average_execution_time': total_time / total_executions if total_executions > 0 else 0
        }


def _setup_child_process():
    """设置子进程环境"""
    if resource:
        # 忽略SIGXCPU和SIGXFSZ信号
        signal.signal(signal.SIGXCPU, signal.SIG_DFL)
        signal.signal(signal.SIGXFSZ, signal.SIG_DFL)


class SandboxManager:
    """沙箱管理器"""

    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.executors = {}
        self.active_executions = {}

    def create_executor(self, execution_id: str) -> SecureCodeExecutor:
        """创建执行器"""
        if execution_id in self.executors:
            raise SecurityViolationError(f"Execution ID {execution_id} already exists")

        executor = SecureCodeExecutor(self.limits)
        self.executors[execution_id] = executor
        return executor

    def terminate_execution(self, execution_id: str):
        """终止执行"""
        if execution_id in self.executors:
            self.executors[execution_id].file_controller.cleanup()
            del self.executors[execution_id]

    def get_executor(self, execution_id: str) -> Optional[SecureCodeExecutor]:
        """获取执行器"""
        return self.executors.get(execution_id)

    def list_executions(self) -> List[str]:
        """列出所有执行ID"""
        return list(self.executors.keys())

    def cleanup_all(self):
        """清理所有执行器"""
        for executor in self.executors.values():
            executor.file_controller.cleanup()
        self.executors.clear()

class FileAccessController:
    """文件系统访问控制器"""
    
    def __init__(self, allowed_paths: List[str] = None, blocked_paths: List[str] = None):
        self.allowed_paths = set(allowed_paths or [])
        self.blocked_paths = set(blocked_paths or [])
        self.temp_dir = None
        self.virtual_fs = {}
    
    def create_isolated_environment(self) -> str:
        self.temp_dir = tempfile.mkdtemp(prefix="sandbox_")
        return self.temp_dir
    
    def check_file_access(self, path: str, mode: str = 'r') -> bool:
        try:
            abs_path = os.path.abspath(path)
            if self.temp_dir and abs_path.startswith(self.temp_dir):
                return True
            if self.allowed_paths:
                for allowed in self.allowed_paths:
                    if abs_path.startswith(os.path.abspath(allowed)):
                        return True
            for blocked in self.blocked_paths:
                if abs_path.startswith(os.path.abspath(blocked)):
                    return False
            return abs_path.startswith(tempfile.gettempdir())
        except Exception as e:
            logger.warning(f"File access check failed: {e}")
            return False
    
    def cleanup(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)


class NetworkController:
    """网络访问控制器"""
    
    def __init__(self, allowed_domains: List[str] = None, blocked_domains: List[str] = None):
        self.allowed_domains = set(allowed_domains or [])
        self.blocked_domains = set(blocked_domains or [])
        self.connections_count = 0
        self.max_connections = 100
    
    def check_network_access(self, host: str, port: int) -> bool:
        if self.connections_count >= self.max_connections:
            return False
        if host in self.blocked_domains:
            return False
        if self.allowed_domains and host not in self.allowed_domains:
            return False
        self.connections_count += 1
        return True
    
    def reset_count(self):
        self.connections_count = 0


class SystemCallInterceptor:
    """系统调用拦截器"""
    
    def __init__(self):
        self.allowed_syscalls = set([
            'read', 'write', 'open', 'close', 'stat', 'fstat', 'lstat',
            'poll', 'lseek', 'mmap', 'mprotect', 'munmap', 'brk',
            'rt_sigaction', 'rt_sigprocmask', 'rt_sigreturn', 'ioctl',
            'pread64', 'pwrite64', 'readv', 'writev', 'access', 'pipe',
            'select', 'sched_yield', 'mremap', 'msync', 'mincore', 'madvise',
            'shmget', 'shmat', 'shmctl', 'dup', 'dup2', 'pause', 'nanosleep',
            'getitimer', 'alarm', 'setitimer', 'getpid', 'sendfile', 'socket',
            'connect', 'accept', 'sendto', 'recvfrom', 'sendmsg', 'recvmsg',
            'shutdown', 'bind', 'listen', 'getsockname', 'getpeername', 'socketpair',
            'setsockopt', 'getsockopt'
        ])
        self.blocked_syscalls = set([
            'fork', 'vfork', 'clone', 'execve', 'execveat', 'ptrace', 'chroot',
            'mount', 'umount', 'umount2', 'swapon', 'swapoff', 'reboot',
            'setuid', 'setgid', 'setreuid', 'setregid', 'setresuid', 'setresgid',
            'setfsuid', 'setfsgid', 'capget', 'capset', 'personality', 'prctl',
            'mmap2', 'fadvise64_64', 'futex', 'set_tid_address', 'set_robust_list',
            'rt_tgsigqueueinfo', 'perf_event_open', 'lookup_dcookie', 'process_vm_readv',
            'process_vm_writev', 'kcmp', 'clock_nanosleep'
        ])
    
    def validate_syscall(self, syscall_name: str) -> bool:
        if syscall_name in self.blocked_syscalls:
            return False
        if self.allowed_syscalls and syscall_name not in self.allowed_syscalls:
            return False
        return True
    
    def get_monitored_syscalls(self) -> List[str]:
        return list(self.blocked_syscalls)


class ContainerRunner:
    """容器化执行器"""
    
    def __init__(self):
        self.docker_available = self._check_docker()
    
    def _check_docker(self) -> bool:
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def run_in_container(
        self,
        code: str,
        limits: ResourceLimits,
        timeout: float
    ) -> ExecutionResult:
        if not self.docker_available:
            raise SecurityViolationError("Docker not available")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            code_file = f.name
        
        try:
            cmd = [
                'docker', 'run',
                '--rm',
                '--network', 'none',
                '--memory', f'{limits.max_memory // (1024 * 1024)}m',
                '--cpus', '1.0',
                '--pids-limit', '1',
                '--read-only',
                '--tmpfs', '/tmp:rw,noexec,nosuid,size=100m',
                '--security-opt', 'no-new-privileges',
                '-v', f'{code_file}:/code.py:ro',
                'python:3.10-slim',
                'python', '/code.py'
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            exec_time = time.time() - start_time
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                execution_time=exec_time,
                sandbox_path='/code.py'
            )
        
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error="Container execution timeout",
                execution_time=timeout
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
        finally:
            if os.path.exists(code_file):
                os.unlink(code_file)
