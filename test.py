## for testing without a webserver.

from client.MonitorGather import MonitorGather
from client.MonitorDeliver import MonitorDeliver
from server.MonitorServer import MonitorServer
from time import sleep
import json

gather = MonitorGather()


deliver = MonitorDeliver()

server = MonitorServer({'client_ip': '12'})

while (1):
    measurements = json.dumps(gather.get_measurements('CPU'))
    server.deliver_measurement(measurements, deliver.sign_message(measurements), deliver.get_api_key())
    print('.', end='',flush=True)
    sleep(2)