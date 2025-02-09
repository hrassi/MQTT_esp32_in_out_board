import network
import time
import machine
import _thread
import socket
from umqtt.simple import MQTTClient


# wdt = machine.WDT(timeout=30000) # settings for watchdog to feed max each 30 seconds

thread_flag = True
launch_flag = True

# Configure the LED pins
led25 = machine.Pin(25, machine.Pin.OUT)
led26 = machine.Pin(26, machine.Pin.OUT)
led27 = machine.Pin(27, machine.Pin.OUT)
led2 = machine.Pin(2, machine.Pin.OUT)

led25.value(0)  # Ensure LEDs are off initially
led26.value(0)
led27.value(0)
led2.value(0)

# Configure the button pins
button32 = machine.Pin(32, machine.Pin.IN, machine.Pin.PULL_UP)
button34 = machine.Pin(34, machine.Pin.IN, machine.Pin.PULL_UP)
button35 = machine.Pin(35, machine.Pin.IN, machine.Pin.PULL_UP)

# Wi-Fi credentials
WIFI_SSID = "Rassi Net3"
WIFI_PASSWORD = "Holyshit"

# MQTT configuration
MQTT_BROKER = "96876878686866a4ad55876876b6480.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "sam02"
MQTT_PASSWORD = "********"
MQTT_TOPICS = ["esp1/led25", "esp1/led26", "esp1/led27", "esp1/button32", "esp1/button34", "esp1/button35"]




# Function to connect to Wi-Fi
def connect_to_wifi():
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)  # Deactivate Wi-Fi
    time.sleep(0.5)  # Give it a moment to reset
    wlan.active(True)  # Reactivate Wi-Fi
    time.sleep(0.5)

    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    time.sleep(1)
    start_time = time.time()
    while not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        time.sleep(2)
        if time.time() - start_time > 60:
            print("Failed to connect to Wi-Fi within timeout")
            print("Push reset or power off and on the ESP32 or check Wi-Fi settings")
            print("MACHINE RESET")
            wlan.disconnect()  
            wlan.active(False) 
            time.sleep(60)  # Ensure clean disconnect and retry after 60 sec
            machine.reset() # restart esp : reset  
            while True:
                led2.value(0)
                time.sleep(0.1)
                led2.value(1)
                time.sleep(0.1)
            return

    print('Connected to Wi-Fi, IP:', wlan.ifconfig()[0])
    
    


# Callback function for received messages
def mqtt_message_callback(topic, msg):
    topic_decoded = topic.decode('utf-8')  # Decode topic to differentiate between them
    try:
        message_value = int(msg)  # Directly convert message to an integer (1 or 0)
    except ValueError:
        print(f"Invalid message on topic {topic_decoded}: {msg}")
        return  # Exit if the message is not a valid integer

    print(f"Message received on topic {topic_decoded}: {message_value}")

    if topic_decoded == "esp1/led25":
        led25.value(message_value)
        print(f"LED25 turned {'ON' if message_value == 1 else 'OFF'}")
    elif topic_decoded == "esp1/led26":
        led26.value(message_value)
        print(f"LED26 turned {'ON' if message_value == 1 else 'OFF'}")
    elif topic_decoded == "esp1/led27":
        led27.value(message_value)
        print(f"LED27 turned {'ON' if message_value == 1 else 'OFF'}")



connect_to_wifi()


# Function to check internet connectivity using a socket
def check_server_connectivity():
    global thread_flag
    try:
        # Connect to Google's public DNS server on port 53
        addr = ("8.8.8.8", 53)
        s = socket.socket()
        s.settimeout(2)  # Set a timeout of 2 seconds
        s.connect(addr)
        s.close()
        print("Connected to internet")
        led2.value(1)
        return True
    except Exception as e:
        led2.value(0)
        print("No internet connectivity!", e)
        print("reseting the esp in 5 seconds")
        thread_flag = False
        time.sleep(5)
        machine.reset()
        return False


# function that run in thread to periodically check esp connectivity
def periodic_check():
    global thread_flag
    while thread_flag == True :
        
        print("Periodic check running...")
        # wdt.feed() # Feed the watchdog to prevent reset
        
        if check_server_connectivity() == False :
            # Disconnect Wi-Fi completely
            led2.value(0)
            print("MACHINE RESET")
            wlan.disconnect()  
            wlan.active(False) 
            time.sleep(2)  # Ensure clean disconnect
            machine.reset() # restart esp : reset      
            
        time.sleep(10)






# Main program
def main():
    
    global launch_flag
    print("Connecting to MQTT broker...")
    try:
        client = MQTTClient(
            client_id="esp32_client",
            server=MQTT_BROKER,
            port=MQTT_PORT,
            user=MQTT_USER,
            password=MQTT_PASSWORD,
            keepalive=60,
            ssl=True,
            ssl_params={'server_hostname':'90b4626652fe44619a4ad5567ecb6480.s1.eu.hivemq.cloud'}  # Certificate verification
        )
        
        # Set Last Will and Testament (LWT)
        client.set_last_will("esp1/status", "offline", retain=True, qos=1)
        
        client.set_callback(mqtt_message_callback)
        client.connect()
        client.publish("esp1/status", "online", retain=True)
        print("MQTT connected!")
        
    except Exception as e:
        print(f"MQTT connection failed: {type(e).__name__}, {e}")
        return

    for topic in MQTT_TOPICS[:3]:  # Subscribe to LED topics
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

    button_states = {
        "esp1/button32": button32.value(),
        "esp1/button34": button34.value(),
        "esp1/button35": button35.value()
    }


    # Start new thread to monitor the connectivity of esp32
    print ("launch_flag is now set to  ",launch_flag)
    if launch_flag == True:
        _thread.start_new_thread(periodic_check, ())


    while True:
        try:
            client.check_msg()

            # Add a ping every 30 seconds to ensure connection is kept alive
            if time.time() % 30 == 0:  # Check every 30 seconds
                time.sleep(1)
                client.ping()  # Send ping to the broker
                print("Ping sent to the broker")
            
            # Check for changes in button states
            for button_topic, button_pin in zip(
                ["esp1/button32", "esp1/button34", "esp1/button35"],
                [button32, button34, button35]
            ):
                current_state = button_pin.value()
                if current_state != button_states[button_topic]:
                    button_states[button_topic] = current_state
                    message = "1" if current_state == 0 else "0"  # Active-low logic
                    client.publish(button_topic, message)
                    print(f"Button state changed: {button_topic} is now {'PUSHED' if message == '1' else 'NOT PUSHED'}")
            time.sleep(0.2)  # Small delay to avoid rapid polling

        except KeyboardInterrupt:
            print("Disconnecting...")
            led2.value(0)
            client.disconnect()
            print("Disconnected.")
        except OSError as e:
            global launch_flag
            print(f"Connection lost: {e}")
            led2.value(0)
            
            try:
                client.disconnect()
            except Exception:
                pass  # Ignore errors if already disconnected    
            
            time.sleep(5)
            try:
                client.connect()
                print("Reconnected to mqtt again and again")
                for topic in MQTT_TOPICS[:3]:  # Ensure re-subscription in case of disconnection
                    client.subscribe(topic)
                    print(f"Resubscribed to topic: {topic}")
            except OSError as e:
                print(f"Reconnection again and again failed: {e}")
                time.sleep(5)
            launch_flag = False
            print("Reconnecting... ... ...")
            time.sleep(3)  # Wait before retrying
            continue  # Restart the loop instead of calling `main()`
            # main()  # Restart the main function
 
 
 
if __name__ == "__main__":
    main()

