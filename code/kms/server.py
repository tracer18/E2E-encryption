#!flask/bin/python
from flask import Flask, request, abort, jsonify, make_response
from flask_httpauth import HTTPBasicAuth
import paho.mqtt.client as mqtt
import threading
import click
import time

CLIENT_ID               = "kms-muii"

topicsPublishNewKeys    = {}
secretRegisteredDevices = {}

app                     = Flask( __name__ )
auth                    = HTTPBasicAuth()
 
class FlaskThread( threading.Thread ):

    @auth.get_password
    def get_password( username ):
        # Ref: https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask
        # TODO-MAYBE: Token Authentication method (?) https://realpython.com/python-random/#osurandom-about-as-random-as-it-gets
        if username == "platform":

            return "platform-MUII"
        return None
       
    @app.route( '/register-device', methods=['POST'] )
    @auth.login_required
    def register( ):
        # TODO: Create a file to include registeredDevices
        if not request.json or not 'id' in request.json: abort( 400 )

        topicsPublishNewKeys[request.json["id"]] = request.json['key_topic']
        return jsonify( {"key_topics": topicsPublishNewKeys} ), 201
        
    @auth.error_handler
    def unauthorized( ):
        return make_response( jsonify( {'error': 'Unauthorized access'} ), 401 )

    @app.errorhandler( 404 )
    def not_found( error ):
        return make_response( jsonify( {'error': 'Not found'} ), 404 )
     
    def run( self ):
        app.run()
    
    @app.route( '/new-key', methods=['GET'] )
    def sendKey():   
        #TODO: Use the function to generate the new key
        API_KEY="Esto es una nueva clave"
        request_message = {'key':API_KEY}
        return request_message,201 

def on_connect( client, userdata, flags, rc ):

  print( "KMS is ready to work." )
  print( "Connected with result code " + str( rc ) )
  # TODO: Read all devices already connected.

def start_flask():
    # Starting flask thread. RESTful service.
    flaskThread = FlaskThread()
    flaskThread.daemon = True # Need to be a daemon to close it with Ctrl+C
    flaskThread.start()

@click.group()
def cli():
    pass

@click.command()
@click.option( '-s', '--server', 'server', required=True, type=str, show_default=True, default='broker.shiftr.io', help="The MQTT Server to send keys." )
@click.option( '-P', '--port', 'port', required=True, type=int, show_default=True, default=1883, help="Port of theMQTT Server to send keys." )
@click.option( '-u', '--user', 'user', required=True, type=str, help="The user to connect to the MQTT Serve." )
@click.option( '-p', '--password', 'password', required=True, type=str, prompt=True, hide_input=True, help="The password for the user to connect to the MQTT Serve. If you do not include this option, a prompt will appear to you introduce the password." )
def connect( server, port, user, password ):
    """
        Start KMS. It will start the RESTful at port 5000 and start the Key Rotation process.
    """
    start_flask() 
    # Connect to MQTT Server.    
    client = mqtt.Client( client_id=CLIENT_ID )
    client.on_connect = on_connect
    client.username_pw_set( user, password )
    client.connect( server, port, 60 )
    client.loop_start()
    while True:    
        # TODO: Reset keys after a while for each device
        for device, topic in topicsPublishNewKeys.items(): 
            # TODO: For each device, change its key depending on the algorithm requested by the device.
            print( device, '->', topic )
            client.publish( topic, "HEY, I'M A KEY", 0 )
        time.sleep( 10 )

if __name__ == '__main__':
  # This main process only include the `connect` command.
  # If you need help to run this command, check: `python server.py connect --help`
  cli.add_command( connect )
  cli()
   