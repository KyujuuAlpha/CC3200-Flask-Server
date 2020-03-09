from __future__ import absolute_import
from __future__ import print_function
import argparse
from awscrt import auth, io, mqtt, http
from awsiot import iotshadow
from awsiot import mqtt_connection_builder
from concurrent.futures import Future
import sys
import threading
import traceback

mqtt_connection = None
shadow_client = None

mqtt_connection = None
shadow_client = None
thing_name = "CC3200_Thing"
endpoint = "a1euv4eww1wx8z-ats.iot.us-west-2.amazonaws.com"
client_id = "Web-Client-1.0"
signing_region = "us-west-2"
cert = "cert/client.pem"
key = "cert/private.pem"
root_ca = "cert/ca.pem"

SHADOW_VALUE_DEFAULT = "val"

class LockedData(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.shadow_property = None
        self.shadow_value = None

disconnect_called = False
locked_data = []

# Function for gracefully quitting this sample
def exit(msg_or_exception):
    global locked_data
    global disconnect_called

    if isinstance(msg_or_exception, Exception):
        print("Exiting sample due to exception.")
        traceback.print_exception(msg_or_exception.__class__, msg_or_exception, sys.exc_info()[2])
    else:
        print("Exiting sample:", msg_or_exception)

    for x in locked_data:
        with x.lock:
            if not disconnect_called:
                print("Disconnecting...")
                disconnect_called = True
                future = mqtt_connection.disconnect()
                future.add_done_callback(on_disconnected)

def on_disconnected(disconnect_future):
    # type: (Future) -> None
    print("Disconnected.")

def on_get_shadow_accepted(response):
    global locked_data
    try:
        print("Finished getting initial shadow state.")

        for x in locked_data:
            with x.lock:
                if x.shadow_value is not None:
                    print("  Ignoring initial query because a delta event has already been received.")
                    continue

            if response.state:
                if response.state.delta:
                    value = response.state.delta.get(x.shadow_property)
                    if value:
                        print("  Shadow contains delta value '{}'.".format(value))
                        change_shadow_value(x.shadow_property, value)
                        continue

                if response.state.reported:
                    value = response.state.reported.get(x.shadow_property)
                    if value:
                        print("  Shadow contains reported value '{}'.".format(value))
                        set_local_value_due_to_initial_query(x.shadow_property, response.state.reported[x.shadow_property])
                        continue

            print("  Shadow document lacks '{}' property. Setting defaults...".format(x.shadow_property))
            change_shadow_value(x.shadow_property, SHADOW_VALUE_DEFAULT)
        return

    except Exception as e:
        exit(e)

def on_get_shadow_rejected(error):
    # type: (iotshadow.ErrorResponse) -> None
    if error.code == 404:
        print("Thing has no shadow document. Creating with defaults...")    
        for x in locked_data:
            change_shadow_value(x.shadow_property, SHADOW_VALUE_DEFAULT)
    else:
        exit("Get request was rejected. code:{} message:'{}'".format(
            error.code, error.message))

def on_shadow_delta_updated(delta):
    global locked_data
    try:
        print("Received shadow delta event.")
        for x in locked_data:
            if delta.state and (x.shadow_property in delta.state):
                value = delta.state[x.shadow_property]
                if value is None:
                    print("  Delta reports that '{}' was deleted. Resetting defaults...".format(x.shadow_property))
                    change_shadow_value(x.shadow_property, SHADOW_VALUE_DEFAULT)
                    return
                else:
                    print("  Delta reports that desired value is '{}'. Changing local value...".format(value))
                    change_shadow_value(x.shadow_property, value)
            else:
                print("  Delta did not report a change in '{}'".format(x.shadow_property))

    except Exception as e:
        exit(e)

def on_publish_update_shadow(future):
    #type: (Future) -> None
    try:
        future.result()
        print("Update request published.")
    except Exception as e:
        print("Failed to publish update request.")
        exit(e)

def on_update_shadow_accepted(response):
    # type: (iotshadow.UpdateShadowResponse) -> None
    for x in locked_data:
        try:
            print("Finished updating reported shadow value to '{}'.".format(response.state.reported[x.shadow_property])) # type: ignore
        except:
            print("Following shadow property does not need to be updated: '{}'.".format(x.shadow_property))

def on_update_shadow_rejected(error):
    # type: (iotshadow.ErrorResponse) -> None
    exit("Update request was rejected. code:{} message:'{}'".format(
        error.code, error.message))

def set_local_value_due_to_initial_query(shadow_property, reported_value):
    global locked_data
    for x in locked_data:
        if x.shadow_property == shadow_property: 
            with x.lock:
                x.shadow_value = reported_value

def change_shadow_value(shadow_property, value):
    global locked_data
    global mqtt_connection
    global shadow_client

    found_data = None
    for x in locked_data:
        if x.shadow_property == shadow_property: 
            found_data = x
            break
    if found_data != None:
        print("Following shadow property is subscribed: '{}'.".format(shadow_property))

        with found_data.lock:
            if found_data.shadow_value == value:
                print("Local value is already '{}'.".format(value))
                return

            print("Changed local shadow value to '{}'.".format(value))
            found_data.shadow_value = value

    print("Updating reported remote shadow value to '{}'.".format(value))
    request = iotshadow.UpdateShadowRequest(
        thing_name=thing_name,
        state=iotshadow.ShadowState(
            reported={ shadow_property: value },
            desired={ shadow_property: value },
        )
    )
    future = shadow_client.publish_update_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
    future.add_done_callback(on_publish_update_shadow)

def subscribe_shadow_property(shadow_property):
    global locked_data
    new_property = LockedData()
    new_property.shadow_property = shadow_property
    locked_data.append(new_property)

def get_subscribed_value(shadow_property):
    global locked_data
    for x in locked_data:
        if x.shadow_property == shadow_property:
            return x.shadow_value
    return None

def connect():
    global mqtt_connection
    global shadow_client
    # Process input args
    # args = parser.parse_args()
    io.init_logging(getattr(io.LogLevel, io.LogLevel.Error.name), 'stderr')

    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    # Subscribe to Shadow Properties to preserve local values
    subscribe_shadow_property("enemy_dir")
    subscribe_shadow_property("player_dir")

    # MQT connection
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=cert,
        pri_key_filepath=key,
        client_bootstrap=client_bootstrap,
        ca_filepath=root_ca,
        client_id=client_id,
        clean_session=False,
        keep_alive_secs=6)

    print("Connecting to {} with client ID '{}'...".format(
        endpoint, client_id))

    connected_future = mqtt_connection.connect()

    shadow_client = iotshadow.IotShadowClient(mqtt_connection)

    # Wait for connection to be fully established.
    # Note that it's not necessary to wait, commands issued to the
    # mqtt_connection before its fully connected will simply be queued.
    # But this sample waits here so it's obvious when a connection
    # fails or succeeds.
    connected_future.result()
    print("Connected!")

    try:
        print("Subscribing to Delta events...")
        delta_subscribed_future, _ = shadow_client.subscribe_to_shadow_delta_updated_events(
            request=iotshadow.ShadowDeltaUpdatedSubscriptionRequest(thing_name),
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=on_shadow_delta_updated)

        # Wait for subscription to succeed
        delta_subscribed_future.result()
        
        print("Subscribing to Update responses...")
        update_accepted_subscribed_future, _ = shadow_client.subscribe_to_update_shadow_accepted(
            request=iotshadow.UpdateShadowSubscriptionRequest(thing_name),
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=on_update_shadow_accepted)

        update_rejected_subscribed_future, _ = shadow_client.subscribe_to_update_shadow_rejected(
            request=iotshadow.UpdateShadowSubscriptionRequest(thing_name),
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=on_update_shadow_rejected)

        # Wait for subscriptions to succeed
        update_accepted_subscribed_future.result()
        update_rejected_subscribed_future.result()
        
        print("Subscribing to Get responses...")
        get_accepted_subscribed_future, _ = shadow_client.subscribe_to_get_shadow_accepted(
            request=iotshadow.GetShadowSubscriptionRequest(thing_name),
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=on_get_shadow_accepted)

        get_rejected_subscribed_future, _ = shadow_client.subscribe_to_get_shadow_rejected(
            request=iotshadow.GetShadowSubscriptionRequest(thing_name),
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=on_get_shadow_rejected)

        # Wait for subscriptions to succeed
        get_accepted_subscribed_future.result()
        get_rejected_subscribed_future.result()

        print("Requesting current shadow state...")
        publish_get_future = shadow_client.publish_get_shadow(
            request=iotshadow.GetShadowRequest(thing_name),
            qos=mqtt.QoS.AT_LEAST_ONCE)

        # Ensure that publish succeeds
        publish_get_future.result()

    except Exception as e:
        exit(e)
