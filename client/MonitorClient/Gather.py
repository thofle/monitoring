import psutil
from time import time

class Gather():
    def __init__(self):
        pass

    def get_measurements(self, stats = ['ALL']):
        result = {}
        stats = [x.upper() for x in stats]

        if 'CPU' in stats:
            result['cpu'] = self.get_cpu_measurement()
        if 'MEMORY' in stats:
            result['memory'] = self.get_memory_measurement()
        if 'DISK' in stats:
            result['disk'] = self.get_memory_measurement()
        if 'NETWORK' in stats:
            result['network'] = self.get_memory_measurement()
        if 'PROCESS' in stats:
            result['process'] = self.get_memory_measurement()

        
        if len(result) == 0:
            result['cpu'] = self.get_cpu_measurement()
            result['memory'] = self.get_memory_measurement()
            result['disk'] = self.get_disk_measurement()
            result['network'] = self.get_network_measurement()
            result['process'] = self.get_process_measurements()
        
        return result

    def get_cpu_measurement(self):
        i = 0
        measurement = psutil.cpu_percent(interval=0.2, percpu=True)
        return {
            'percent_usage': {'core'+str(i):measurement[i] for i in range(0, len(measurement))},
            'physical_cores': psutil.cpu_count(logical=False),
            'measured_at': int(time()),
            } 

    def get_memory_measurement(self):
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'free': mem.free,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'measured_at': int(time()),
            } 

    def get_disk_measurement(self):
        disks = []
        for partition in psutil.disk_partitions(all=False):
            if partition.opts != 'removable':
                size = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'size': size.total,
                    'used': size.used,
                    'measured_at': int(time())
                })
        return disks
    
    def get_network_measurement(self):
        adapters = []
        all_adapters = psutil.net_io_counters(pernic=True)
        ips = psutil.net_if_addrs()
        for adapter in all_adapters:
            if 'Loopback' not in adapter and adapter != 'lo' and 'Bluetooth' not in adapter:
                adapters.append({
                    'name': adapter,
                    'addresses': ips[adapter],
                    'bytes_sent': all_adapters[adapter].bytes_sent,
                    'bytes_recv': all_adapters[adapter].bytes_recv,
                    'measured_at': int(time())
                })
        return adapters

    def get_process_measurements(self):
        listening_processes = []
        for con in psutil.net_connections():
            if con.status == 'LISTEN':
                listening_processes.append({
                    'process': con.pid,
                    'ip': con.laddr.ip,
                    'port': con.laddr.port
                })

        processes = []
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                
                with p.oneshot():
                    name = 'restricted'
                    executable = 'restricted'

                    try:
                        executable = p.exe()
                    except psutil.AccessDenied:
                        pass

                    try:
                        name = p.name()
                    except psutil.AccessDenied:
                        pass

                    processes.append({
                        'process': pid,
                        'executable': executable,
                        'name': name,
                        
                    })
            except psutil.NoSuchProcess:
                pass
            except psutil.AccessDenied:
                pass
        return {
            'listening_processes': listening_processes,
            'processes': processes,
            'measured_at': int(time())
        }