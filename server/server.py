from MonitorServer.Server import MServer
from MonitorServer.helpers import validate_signature
from flask import Flask, request, abort

app = Flask(__name__)


@app.route('/v1/register/client', methods=['POST'])
def register_client():
    ms = MServer(client_ip=request.remote_addr)
    if not all(k in request.form.keys() for k in('hostname','hostname_signature','public_signing_key')):
        abort(406)

    hostname = request.form['hostname']
    hostname_signature = request.form['hostname_signature']
    public_signing_key = request.form['public_signing_key']

    print(public_signing_key)
    if validate_signature(hostname, hostname_signature, public_signing_key) == False:
        ms.log_message('Invalid signature')
        abort(422)
    
    return ms.get_new_api_key(hostname,hostname_signature,public_signing_key)

@app.route('/v1/deliver/measurement', methods=['POST'])
def deliver_measurement():
    ms = MServer(client_ip=request.remote_addr)
    if not all(k in request.form.keys() for k in('api_key','measurement','measurement_signature')):
        abort(406)

    api_key = request.form['api_key']
    measurement = request.form['measurement']
    measurement_signature = request.form['measurement_signature']
    
    parent_id, public_signing_key = ms.get_parent_id_and_psk(api_key)
    if parent_id is None:
        ms.log_message('Invalid api key')
        abort(498)

    if validate_signature(measurement, measurement_signature, public_signing_key) == False:
        ms.log_message('Invalid signature')
        abort(422)
    
    ms.deliver_measurement(measurement, parent_id)
    return ''

if __name__ == '__main__':
  app.run(debug=True,port=5000,host='0.0.0.0')
