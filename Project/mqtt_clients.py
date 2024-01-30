# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=import-error
# pylint: disable=line-too-long

import time
from logging import Logger
import config_constants as const
import paho.mqtt.client as mqtt
from terminal_colors import TerminalColors

# class Client:
#     def __init__(self, broker, publisher_topics_list, subscribers_topic_to_func_dict, variables):
#         self.main_add = mqtt.Client(client_id='main_add')
#         self.main_check_request = mqtt.Client(client_id='main_check_request')
#         self.main_check_response = mqtt.Client(client_id='main_check_response')
#         self.token_check_request = mqtt.Client(client_id='main_token_check_request')
#         self.token_check_response = mqtt.Client(client_id='main_token_check_response', userdata={'variables': variables})
#         self.broker = broker
#         self.publisher_topics = publisher_topics_list
#         self.subscribers_topic_to_func = subscribers_topic_to_func_dict
#         self.topic_to_client_dict = {
#             const.MAIN_TOPIC_ADD : self.main_add,
#             const.MAIN_TOPIC_CHECK_REQUEST : self.main_check_request,
#             const.MAIN_TOPIC_CHECK_RESPONSE : self.main_check_response,
#             const.MAIN_TOKEN_CHECK_REQUEST : self.token_check_request,
#             const.MAIN_TOKEN_CHECK_RESPONSE : self.token_check_response
#         }

#     def connect_publishers(self):
#         for topic in self.publisher_topics:
#             self.topic_to_client_dict[topic].connect(self.broker)

#     def disconnect_publishers(self):
#         for topic in self.publisher_topics:
#             self.topic_to_client_dict[topic].disconnect()

#     def connect_subscribers(self):
#         for topic, func in self.subscribers_topic_to_func.items():
#             self.topic_to_client_dict[topic].connect(self.broker)
#             self.topic_to_client_dict[topic].on_message = func
#             self.topic_to_client_dict[topic].loop_start()
#             self.topic_to_client_dict[topic].subscribe(f'{topic}')

#     def disconnect_subscribers(self):
#         for topic in self.subscribers_topic_to_func:
#             self.topic_to_client_dict[topic].loop_stop()
#             self.topic_to_client_dict[topic].disconnect()

#     def publish(self, topic, message):
#         self.topic_to_client_dict[topic].publish(topic, message)

# class SecretClient:
#     def __init__(self, client_id, broker, publisher_topics_list, subscribers_topic_to_func_dict, variables):
#         self.id = client_id
#         self.secret_add = mqtt.Client(client_id=f'secret_add_{id}')
#         self.secret_check_request = mqtt.Client(client_id=f'secret_check_request_{id}')
#         self.secret_check_response = mqtt.Client(client_id=f'secret_check_response_{id}')
#         self.token_check_request = mqtt.Client(client_id=f'secret_token_check_request_{id}')
#         self.token_check_response = mqtt.Client(client_id=f'secret_token_check_response_{id}', userdata={'variables': variables})
#         self.broker = broker
#         self.publisher_topics = publisher_topics_list
#         self.subscribers_topic_to_func = subscribers_topic_to_func_dict
#         self.topic_to_client_dict = {
#             const.SECRET_TOPIC_ADD : self.secret_add,
#             const.SECRET_TOPIC_CHECK_REQUEST : self.secret_check_request,
#             const.SECRET_TOPIC_CHECK_RESPONSE : self.secret_check_response,
#             const.SECRET_TOKEN_CHECK_REQUEST : self.token_check_request,
#             const.SECRET_TOKEN_CHECK_RESPONSE : self.token_check_response
#         }

#     def connect_publishers(self):
#         for topic in self.publisher_topics:
#             self.topic_to_client_dict[topic].connect(self.broker)

#     def disconnect_publishers(self):
#         for topic in self.publisher_topics:
#             self.topic_to_client_dict[topic].disconnect()

#     def connect_subscribers(self):
#         for topic, func in self.subscribers_topic_to_func.items():
#             self.topic_to_client_dict[topic].connect(self.broker)
#             self.topic_to_client_dict[topic].on_message = func
#             self.topic_to_client_dict[topic].loop_start()
#             self.topic_to_client_dict[topic].subscribe(f'{topic}/{self.id}')

#     def disconnect_subscribers(self):
#         for topic in self.subscribers_topic_to_func:
#             self.topic_to_client_dict[topic].loop_stop()
#             self.topic_to_client_dict[topic].disconnect()

#     def publish(self, topic, message):
#         self.topic_to_client_dict[topic].publish(f'{topic}/{self.id}', f'{self.id}&{message}')
class Client:
    def __init__(self, client_id, is_main, broker, publisher_topics_list, subscribers_topic_to_func_dict, variables, logger: Logger):
        timestamp = time.time() * 1000
        self.id = client_id
        self.is_main = is_main
        self.logger = logger
        self.client_add = mqtt.Client(client_id=f'client_add_{id}_{timestamp}')
        self.client_check_request = mqtt.Client(client_id=f'client_check_request_{id}_{timestamp}')
        self.client_check_response = mqtt.Client(client_id=f'client_check_response_{id}_{timestamp}')
        self.token_check_request = mqtt.Client(client_id=f'client_token_check_request_{id}_{timestamp}')
        self.token_check_response = mqtt.Client(client_id=f'client_token_check_response_{id}_{timestamp}', userdata={'variables': variables})
        self.broker = broker
        self.publisher_topics = publisher_topics_list
        self.subscribers_topic_to_func = subscribers_topic_to_func_dict
        self.topic_to_client_dict = {
            const.MAIN_TOPIC_ADD : self.client_add,
            const.SECRET_TOPIC_ADD : self.client_add,
            const.MAIN_TOPIC_CHECK_REQUEST : self.client_check_request,
            const.SECRET_TOPIC_CHECK_REQUEST : self.client_check_request,
            const.MAIN_TOPIC_CHECK_RESPONSE : self.client_check_response,
            const.SECRET_TOPIC_CHECK_RESPONSE : self.client_check_response,
            const.MAIN_TOKEN_CHECK_REQUEST : self.token_check_request,
            const.SECRET_TOKEN_CHECK_REQUEST : self.token_check_request,
            const.MAIN_TOKEN_CHECK_RESPONSE : self.token_check_response,
            const.SECRET_TOKEN_CHECK_RESPONSE : self.token_check_response
        }

    def connect_publishers(self):
        for topic in self.publisher_topics:
            self.topic_to_client_dict[topic].connect(self.broker)
            self.logger.debug('%s[Client id - %i]%s Connected client: %s to the broker: %s%s', TerminalColors.BLUE, self.id, TerminalColors.YELLOW, self.topic_to_client_dict[topic].client_id, self.broker, TerminalColors.RESET)

    def disconnect_publishers(self):
        for topic in self.publisher_topics:
            self.topic_to_client_dict[topic].disconnect()
            self.logger.debug('%s[Client id - %i]%s Disconnected client: %s from the broker: %s%s', TerminalColors.BLUE, self.id, TerminalColors.YELLOW, self.topic_to_client_dict[topic].client_id, self.broker, TerminalColors.RESET)

    def connect_subscribers(self):
        for topic, func in self.subscribers_topic_to_func.items():
            self.topic_to_client_dict[topic].connect(self.broker)
            self.topic_to_client_dict[topic].on_message = func
            self.topic_to_client_dict[topic].loop_start()
            self.topic_to_client_dict[topic].subscribe(f'{topic}/{self.id}')
            self.logger.debug('%s[Client id - %i]%s Subscribed topic: %s%s', TerminalColors.BLUE, self.id, TerminalColors.YELLOW, f'{topic}/{self.id}', TerminalColors.RESET)

    def disconnect_subscribers(self):
        for topic in self.subscribers_topic_to_func:
            self.topic_to_client_dict[topic].loop_stop()
            self.topic_to_client_dict[topic].disconnect()
            self.logger.debug('%s[Client id - %i]%s Unsubscribed topic: %s%s', TerminalColors.BLUE, self.id, TerminalColors.YELLOW, f'{topic}/{self.id}', TerminalColors.RESET)

    def publish(self, topic, message):
        if self.is_main:
            self.topic_to_client_dict[topic].publish(f'{topic}/{self.id}', message)
            self.logger.debug('%s[Client id - %i]%s Published to the topic: %s, message: %s%s', TerminalColors.BLUE, self.id, TerminalColors.YELLOW, f'{topic}/{self.id}', message, TerminalColors.RESET)
        else:
            self.topic_to_client_dict[topic].publish(f'{topic}/{self.id}', f'{self.id}&{message}')
            self.logger.debug('%s[Client id - %i]%s Published to the topic: %s, message: %s%s', TerminalColors.BLUE, self.id, TerminalColors.YELLOW, f'{topic}/{self.id}', f'{self.id}&{message}', TerminalColors.RESET)
