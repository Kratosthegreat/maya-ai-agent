import psutil
import shutil


class HealthEngine:

    def system_health(self):

        mem = psutil.virtual_memory()

        disk = shutil.disk_usage("/")

        cpu = psutil.cpu_percent()

        return {

            "cpu": cpu,

            "memory_percent": mem.percent,

            "disk_percent": (

                disk.used / disk.total

            ) * 100

        }

    ####################################
    # PRESSURE
    ####################################

    def high_memory(self):

        mem = psutil.virtual_memory()

        return mem.percent > 85

    def high_cpu(self):

        return psutil.cpu_percent() > 90
