# Based on the sample given to us from the AWS Python MQTT Library
# Rewritten based on the needs of multiple shadow properties and for the sake
# of relearning Python :)

from awscrt import io, mqtt
from awsiot import iotshadow, mqtt_connection_builder

# Classes used
class ShadowProperty:
    def __init__(self, name = None, val = None):
        self.name = name
        self.val = val

# Parameters for the MQTT connection
thingName = "CC3200_Thing"
endpoint = "a1euv4eww1wx8z-ats.iot.us-west-2.amazonaws.com"
clientID = "Web-Client-1.0"
signingRegion = "us-west-2"
cert = "cert/client.pem"
key = "cert/private.pem"
rootCA = "cert/ca.pem"

# Some global variable regarding the connection
shadowProperties = []
mqttC = None
shadow = None

def changeShadowValue(shadowProperty, val):
    global shadowProperties
    global mqttC
    global shadow

    print("updating value")

    # first check if it exists
    foundShadow = None
    for x in shadowProperties:
        if x.name == shadowProperty: 
            foundShadow = x
            break

    # if it does, update the local value
    if foundShadow != None:
        if foundShadow.val == val:
            return
        foundShadow.val = val

    # update what is on the server
    request = iotshadow.UpdateShadowRequest(
        thing_name=thingName,
        state=iotshadow.ShadowState(
            reported={ shadowProperty: val },
            desired={ shadowProperty: val },
        )
    )
    response = shadow.publish_update_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
    response.add_done_callback(updateDoneCallBack)

def updateDoneCallBack(f):
    f.result()

def subscribeToProperties(*shadowPropertyArgs):
    global shadowProperties
    for x in shadowPropertyArgs:
        newProperty = ShadowProperty(x, None)
        shadowProperties.append(newProperty)

def getSubscribedPropertyVal(shadowProperty):
    global shadowProperties
    for x in shadowProperties:
        if x.name == shadowProperty:
            return x.val
    return None

def setSubscribedPropertyVal(shadowProperty, val):
    global shadowProperties
    for x in shadowProperties:
        if x.name == shadowProperty:
            x.val = val
            return True
    return False

def shadowGetEvent(r):
    global shadowProperties
    print("initial get")
    for x in shadowProperties:
        if r.state:
            if r.state.delta:
                # exists in delta
                value = r.state.delta.get(x.name)
                if value:
                    changeShadowValue(x.name, value)
                    continue
            if r.state.reported:
                # exists in reported
                value = r.state.reported.get(x.name)
                if value:
                    setSubscribedPropertyVal(x.name, value)
                    continue
        # exists in neither
        changeShadowValue(x.name, "val")

def shadowDeltaUpdateEvent(d):
    global shadowProperties
    print("delta event")
    for x in shadowProperties:
        if d.state and (x.name in d.state):
            value = d.state.get(x.name)
            if value is None:
                # something was deleted
                changeShadowValue(x.name, "val")
            else:
                if value != "#":
                    # something changed!
                    changeShadowValue(x.name, value)

def connect():
    global mqttC
    global shadow

    # don't fully comprehend what these are, but they were in the example. though i can see that they relate
    # to io stuff
    eventLoopGroup = io.EventLoopGroup(1)
    hostResolver = io.DefaultHostResolver(eventLoopGroup)
    clientBootstrap = io.ClientBootstrap(eventLoopGroup, hostResolver)

    # Subscribe to Shadow Properties to preserve local values
    subscribeToProperties("pac_loc", "b1_loc", "b2_loc", "b3_loc", "b4_loc", "bad_ctrl", "bad_dir")

    # MQT connection
    mqttC = mqtt_connection_builder.mtls_from_path(cert, key,
                                                   ca_filepath=rootCA, endpoint=endpoint, client_id=clientID,
                                                   client_bootstrap=clientBootstrap, clean_session=False, keep_alive_secs=6)

    # Attempt to connect to the server
    connection = mqttC.connect()
    shadow = iotshadow.IotShadowClient(mqttC)

    # Wait for connection
    connection.result()
   
    # Subscribe to  different shadow events
    # Shadow Delta Event
    shadow.subscribe_to_shadow_delta_updated_events(iotshadow.ShadowDeltaUpdatedSubscriptionRequest(thingName),
                                                    mqtt.QoS.AT_LEAST_ONCE, shadowDeltaUpdateEvent)[0].result()
    # Get Response
    shadow.subscribe_to_get_shadow_accepted(iotshadow.GetShadowSubscriptionRequest(thingName),
                                                    mqtt.QoS.AT_LEAST_ONCE, shadowGetEvent)[0].result()

    # Get shadow's current state request
    shadow.publish_get_shadow(iotshadow.GetShadowRequest(thingName), mqtt.QoS.AT_LEAST_ONCE).result()