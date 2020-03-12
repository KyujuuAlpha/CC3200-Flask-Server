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

# Enemy queues
b1_q = ""
b2_q = ""
b3_q = ""
b4_q = ""

def queueMovement(selectedBaddie, move):
    global b1_q
    global b2_q
    global b3_q
    global b4_q
    if selectedBaddie == 1:
        b1_q += move
    elif selectedBaddie == 2:
        b2_q += move
    elif selectedBaddie == 3:
        b3_q += move
    elif selectedBaddie == 4:
        b4_q += move
    updateServerQueues()

def updateServerQueues():
    global b1_q
    global b2_q
    global b3_q
    global b4_q
    queue = ""
    if getSubscribedPropertyVal("b1_q") == "ready" and len(b1_q) > 0:
        if len(b1_q) > 8:
            queue = b1_q[:8]
            b1_q = b1_q[8:]
        else:
            queue = b1_q
            b1_q = ""
        changeShadowValue("b1_q", queue)
    if getSubscribedPropertyVal("b2_q") == "ready" and len(b2_q) > 0:
        if len(b2_q) > 8:
            queue = b2_q[:8]
            b2_q = b2_q[8:]
        else:
            queue = b2_q
            b2_q = ""
        changeShadowValue("b2_q", queue)
    if getSubscribedPropertyVal("b3_q") == "ready" and len(b3_q) > 0:
        if len(b3_q) > 8:
            queue = b3_q[:8]
            b3_q = b3_q[8:]
        else:
            queue = b3_q
            b3_q = ""
        changeShadowValue("b3_q", queue)
    if getSubscribedPropertyVal("b4_q") == "ready" and len(b4_q) > 0:
        if len(b4_q) > 8:
            queue = b4_q[:8]
            b4_q = b4_q[8:]
        else:
            queue = b4_q
            b4_q = ""
        changeShadowValue("b4_q", queue)

def changeShadowValue(shadowProperty, val):
    global shadowProperties
    global mqttC
    global shadow

    # print("updating value")

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
    # print("delta event")
    for x in shadowProperties:
        if d.state and (x.name in d.state):
            value = d.state.get(x.name)
            if value is None:
                # something was deleted
                changeShadowValue(x.name, "val")
            else:
                # something changed!
                changeShadowValue(x.name, value)

def shadowUpdateAcceptedEvent(r):
    try:
        value = r.state.reported["b1_q"]
        updateServerQueues()
    except Exception as e:
        try:
            value = r.state.reported["b2_q"]
            updateServerQueues()
        except Exception as e:
            try:
                value = r.state.reported["b3_q"]
                updateServerQueues()
            except Exception as e:
                try:
                    value = r.state.reported["b4_q"]
                    updateServerQueues()
                except Exception as e:
                    return

def connect():
    global mqttC
    global shadow

    # don't fully comprehend what these are, but they were in the example. though i can see that they relate
    # to io stuff
    eventLoopGroup = io.EventLoopGroup(1)
    hostResolver = io.DefaultHostResolver(eventLoopGroup)
    clientBootstrap = io.ClientBootstrap(eventLoopGroup, hostResolver)

    # Subscribe to Shadow Properties to preserve local values
    subscribeToProperties("pac_loc", "b1_loc", "b2_loc", "b3_loc", "b4_loc", "b1_q", "b2_q", "b3_q", "b4_q")

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
    # Update Accepted
    shadow.subscribe_to_update_shadow_accepted(iotshadow.UpdateShadowSubscriptionRequest(thingName), 
                                                    mqtt.QoS.AT_LEAST_ONCE, shadowUpdateAcceptedEvent)
    # Get Response
    shadow.subscribe_to_get_shadow_accepted(iotshadow.GetShadowSubscriptionRequest(thingName),
                                                    mqtt.QoS.AT_LEAST_ONCE, shadowGetEvent)[0].result()

    # Get shadow's current state request
    shadow.publish_get_shadow(iotshadow.GetShadowRequest(thingName), mqtt.QoS.AT_LEAST_ONCE).result()