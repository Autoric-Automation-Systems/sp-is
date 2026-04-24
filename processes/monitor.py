"""Módulo de monitoramento do sistema - CPU, RAM, Disco e Rede"""
import psutil
import platform
import socket
import time


class SystemMonitor:
    @staticmethod
    def cpu_info():
        """Informações do processador"""
        return {
            "modelo": platform.processor() or "Desconhecido",
            "arquitetura": platform.machine(),
            "nucleos_fisicos": psutil.cpu_count(logical=False),
            "nucleos_logicos": psutil.cpu_count(logical=True),
        }

    @staticmethod
    def cpu_percent():
        return psutil.cpu_percent(interval=None)

    @staticmethod
    def cpu_percent_per_core():
        return psutil.cpu_percent(percpu=True)

    @staticmethod
    def ram():
        return psutil.virtual_memory()

    @staticmethod
    def swap():
        return psutil.swap_memory()

    @staticmethod
    def disk_partitions():
        return psutil.disk_partitions()

    @staticmethod
    def disk_usage(mountpoint):
        return psutil.disk_usage(mountpoint)

    @staticmethod
    def net_io():
        return psutil.net_io_counters()

    @staticmethod
    def net_ifaces():
        return psutil.net_if_addrs(), psutil.net_if_stats()

    @staticmethod
    def net_connections():
        return psutil.net_connections(kind="inet")

    @staticmethod
    def top_processes(limit=10):
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return sorted(procs, key=lambda x: x.get("cpu_percent") or 0, reverse=True)[:limit]

    @staticmethod
    def system_info():
        uname = platform.uname()
        boot = psutil.boot_time()
        uptime = time.time() - boot
        return {
            "sistema": f"{uname.system} {uname.release}",
            "versao": uname.version,
            "arquitetura": platform.machine(),
            "hostname": uname.node,
            "processador": uname.processor or "Desconhecido",
            "uptime_segundos": uptime,
        }

    @staticmethod
    def hostname_ip():
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except:
            hostname = platform.node()
            ip = "Desconhecido"
        return hostname, ip

    @staticmethod
    def format_bytes(b):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if b < 1024.0:
                return f"{b:.1f} {unit}"
            b /= 1024.0
        return f"{b:.1f} PB"

    @staticmethod
    def format_uptime(seconds):
        d = int(seconds // 86400)
        h = int((seconds % 86400) // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        parts = []
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        parts.append(f"{s}s")
        return " ".join(parts)
