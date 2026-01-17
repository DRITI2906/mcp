"""
MCP System Info Server

A lightweight MCP server that provides real-time system information
including CPU, memory, disk, and GPU statistics.
"""

import platform
from typing import Any

import psutil
from mcp.server.fastmcp import FastMCP

# Try to import optional dependencies
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

try:
    import cpuinfo
    CPUINFO_AVAILABLE = True
except ImportError:
    CPUINFO_AVAILABLE = False


# Initialize the MCP server
mcp = FastMCP("sysinfo")


def bytes_to_gb(bytes_value: int) -> float:
    """Convert bytes to gigabytes, rounded to 2 decimal places."""
    return round(bytes_value / (1024 ** 3), 2)


def get_system_info() -> dict[str, Any]:
    """Collect basic system information."""
    uname = platform.uname()
    return {
        "system_name": uname.system,
        "node_name": uname.node,
        "os_release": uname.release,
        "os_version": uname.version,
        "machine_type": uname.machine,
        "processor": uname.processor,
    }


def get_cpu_info() -> dict[str, Any]:
    """Collect CPU information."""
    cpu_data = {
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
    }
    
    # Get CPU frequency if available
    cpu_freq = psutil.cpu_freq()
    if cpu_freq:
        cpu_data["cpu_frequency_mhz"] = round(cpu_freq.current, 2)
    
    # Get detailed CPU name if py-cpuinfo is available
    if CPUINFO_AVAILABLE:
        try:
            info = cpuinfo.get_cpu_info()
            cpu_data["processor_name"] = info.get("brand_raw", "Unknown")
        except Exception:
            cpu_data["processor_name"] = platform.processor() or "Unknown"
    else:
        cpu_data["processor_name"] = platform.processor() or "Unknown"
    
    return cpu_data


def get_memory_info() -> dict[str, Any]:
    """Collect memory information."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": bytes_to_gb(mem.total),
        "available_gb": bytes_to_gb(mem.available),
        "used_gb": bytes_to_gb(mem.used),
        "utilization_percent": mem.percent,
    }


def get_disk_info() -> dict[str, Any]:
    """Collect disk information for the main drive."""
    try:
        # Get the root partition (C: on Windows, / on Unix)
        if platform.system() == "Windows":
            disk = psutil.disk_usage("C:\\")
        else:
            disk = psutil.disk_usage("/")
        
        return {
            "total_gb": bytes_to_gb(disk.total),
            "used_gb": bytes_to_gb(disk.used),
            "free_gb": bytes_to_gb(disk.free),
            "utilization_percent": disk.percent,
        }
    except Exception as e:
        return {"error": str(e)}


def get_gpu_info() -> list[dict[str, Any]] | dict[str, str]:
    """Collect GPU information if available."""
    if not GPU_AVAILABLE:
        return {"status": "GPUtil not installed or no NVIDIA GPU detected"}
    
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return {"status": "No NVIDIA GPU detected"}
        
        gpu_list = []
        for gpu in gpus:
            gpu_list.append({
                "id": gpu.id,
                "name": gpu.name,
                "memory_total_mb": round(gpu.memoryTotal, 2),
                "memory_used_mb": round(gpu.memoryUsed, 2),
                "memory_free_mb": round(gpu.memoryFree, 2),
                "gpu_utilization_percent": gpu.load * 100,
                "temperature_c": gpu.temperature,
            })
        return gpu_list
    except Exception as e:
        return {"status": f"Error getting GPU info: {str(e)}"}


@mcp.tool()
def get_sysinfo() -> dict[str, Any]:
    """
    Get comprehensive system information.
    
    Returns detailed information about the system including:
    - System: OS name, version, machine type
    - CPU: Processor name, cores, frequency, usage
    - Memory: Total, available, used memory and utilization
    - Disk: Total, used, free disk space and utilization
    - GPU: NVIDIA GPU details if available (name, memory, utilization, temperature)
    """
    return {
        "system": get_system_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disk": get_disk_info(),
        "gpu": get_gpu_info(),
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
