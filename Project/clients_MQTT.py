import time
import paho.mqtt.client as mqtt
import config_constants as const

class Client:
    def __init__(self, broker, publisher_topics_list, subscribers_topic_to_func_dict):
        timestamp_id = str(int(time.time() * 1000))
        self.main_add = mqtt.Client(client_id=f'main_add_{timestamp_id}')
        self.main_check_request = mqtt.Client(client_id=f'main_check_request_{timestamp_id}')
        self.main_check_response = mqtt.Client(client_id=f'main_check_response_{timestamp_id}')
        self.token_check_request = mqtt.Client(client_id=f'token_check_request_{timestamp_id}')
        self.token_check_response = mqtt.Client(client_id=f'token_check_response_{timestamp_id}')
        self.broker = broker
        self.publisher_topics = publisher_topics_list
        self.subscribers_topic_to_func = subscribers_topic_to_func_dict
        self.topic_to_client_dict = {
            const.MAIN_TOPIC_ADD : self.main_add,
            const.MAIN_TOPIC_CHECK_REQUEST : self.token_check_request,
            const.MAIN_TOPIC_CHECK_RESPONSE : self.main_check_response,
            const.TOKEN_CHECK_REQUEST : self.token_check_request,
            const.TOKEN_CHECK_RESPONSE : self.token_check_response
        }

    def connect_publishers(self):
        for topic in self.publisher_topics:
            self.topic_to_client_dict[topic].connect(self.broker)

    def disconnect_publishers(self):
        for topic in self.publisher_topics:
            self.topic_to_client_dict[topic].disconnect()

    def connect_subscribers(self):
        for topic, func in self.subscribers_topic_to_func.items():
            self.topic_to_client_dict[topic].connect(self.broker)
            self.topic_to_client_dict[topic].on_message = func
            self.topic_to_client_dict[topic].loop_start()
            self.topic_to_client_dict[topic].subscribe(topic)

    def disconnect_subscribers(self):
        for topic in self.subscribers_topic_to_func:
            self.topic_to_client_dict[topic].loop_stop()
            self.topic_to_client_dict[topic].disconnect()
    
    def publish(self, topic, message):
        self.topic_to_client_dict[topic].publish(message)