from MonitorServer import MonitorServer
if __name__ == '__main__':
    connection_info = {
        'client_ip': '123.0.0.1',
        'version': '0.04.a'
    }
    
    server = MonitorServer(connection_info)

    server.log_message('tests')