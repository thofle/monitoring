from MonitorClient.Gather import Gather
from MonitorClient.ClientDatabase import ClientDatabase
import json
from time import sleep

if __name__ == '__main__':
    g = Gather()
    d = ClientDatabase()
    measurements = d.get_measurements_to_capture()
    d.add_monitoring_data(json.dumps(g.get_measurements(measurements))) 