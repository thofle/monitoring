from MonitorClient.Deliver import Deliver
import json

if __name__ == '__main__':
    d = Deliver('http://127.0.0.1:5000/')
    d.upload()
