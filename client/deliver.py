from MonitorClient.Deliver import Deliver
import json

if __name__ == '__main__':
    d = Deliver('https://api.aroonie.com/')
    d.upload()
