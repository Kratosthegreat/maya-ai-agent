import psutil
import shutil
import docker

class SystemTools:

    def __init__(self):

        self.docker_client = docker.from_env()

    # ─────────────────────────
    # CPU
    # ─────────────────────────

    def cpu_usage(self):

        return psutil.cpu_percent(interval=1)

    # ─────────────────────────
    # RAM
    # ─────────────────────────

    def ram_usage(self):

        mem = psutil.virtual_memory()

        return {
            "percent": mem.percent,
            "used_gb": round(
                mem.used / (1024**3),
                2
            ),
            "total_gb": round(
                mem.total / (1024**3),
                2
            )
        }

    # ─────────────────────────
    # DISK
    # ─────────────────────────

    def disk_usage(self):

        disk = shutil.disk_usage("/")

        used = round(
            disk.used / (1024**3),
            2
        )

        total = round(
            disk.total / (1024**3),
            2
        )

        percent = round(
            (used / total) * 100,
            1
        )

        return {
            "percent": percent,
            "used_gb": used,
            "total_gb": total
        }

    # ─────────────────────────
    # DOCKER
    # ─────────────────────────

    def containers_status(self):

        containers = self.docker_client.containers.list(
            all=True
        )

        result = []

        for c in containers:

            try:

                c.reload()

                result.append({
                    "name": c.name,
                    "status": c.status
                })

            except Exception:

                continue

        return result

    # ─────────────────────────
    # FULL STATUS
    # ─────────────────────────

    def full_status(self):

        cpu = self.cpu_usage()

        ram = self.ram_usage()

        disk = self.disk_usage()

        containers = self.containers_status()

        output = []

        output.append(
            f"CPU: {cpu}%"
        )

        output.append(
            f"RAM: "
            f"{ram['used_gb']}GB / "
            f"{ram['total_gb']}GB "
            f"({ram['percent']}%)"
        )

        output.append(
            f"Disk: "
            f"{disk['used_gb']}GB / "
            f"{disk['total_gb']}GB "
            f"({disk['percent']}%)"
        )

        output.append("")
        output.append(
            "Docker Containers:"
        )

        for c in containers:

            output.append(
                f"• {c['name']} → {c['status']}"
            )

        return "\n".join(output)
