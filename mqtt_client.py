import logging
import paho.mqtt.client as mqtt

from bot import get_mqtt_message
import consts


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def on_connect(client, userdata, flags, reason_code, properties):
    logging.info(f"Connected with result code {reason_code}")
    client.subscribe("+/+/+")

def on_message(client, userdata, msg):
    get_mqtt_message(msg)

def start_mqtt_client():
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(consts.ADRESS, 1883, 60)
    mqttc.loop_start()