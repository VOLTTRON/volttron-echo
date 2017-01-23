# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2015, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#

# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# r favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

# }}}

from __future__ import absolute_import, print_function

from datetime import datetime
import logging
import random
import sys
import gevent

import pymysql
import json

import datetime
import string
import re

# subscriber agent
from volttron.platform.vip.agent import Agent, Core, PubSub, compat
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod
from volttron.platform.messaging.health import (STATUS_BAD,
                                                STATUS_GOOD, Status)

# AWS IOT
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import getopt

# global varaibles for iot certificates --------
useWebsocket = True
host = "**************.iot.us-west-2.amazonaws.com"
rootCAPath = "aws-iot-rootCA.crt"
certificatePath = ""
privateKeyPath = ""

#---------------------------------------------------
utils.setup_logging()
_log = logging.getLogger(__name__)
__version__ = '3.0'
FORWARD_TIMEOUT_KEY = 'FORWARD_TIMEOUT_KEY'


# subscribe callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

# Configure logging
def configure_logging():
    logger = None
    if sys.version_info[0] == 3:
        logger = logging.getLogger("core")  # Python 3
    else:
        logger = logging.getLogger("AWSIoTPythonSDK.core")  # Python 2
    logger.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

'''
Structuring the agent this way allows us to grab config file settings 
for use in subscriptions instead of hardcoding them.
'''


# this is a publishing agent. listener agent will subscribe.
def subscriber_agent(config_path, **kwargs):
    config = utils.load_config(config_path) 

    # VC vip is currently being used
    destination_vip = config.get('destination-vip') 
    _log.debug("destination vip: {}".format(destination_vip)) 

    configure_logging()

    class AwsSender(Agent):
        '''
        This agent demonstrates usage of the 3.0 pubsub service as well as 
        interfacting with the historian. This agent is mostly self-contained, 
        but requires the histoiran be running to demonstrate the query feature.
        '''

        def __init__(self, **kwargs):
            super(AwsSender, self).__init__(**kwargs)

        @Core.receiver('onsetup')
        def setup(self, sender, **kwargs):
            # Demonstrate accessing a value from the config file
            self._agent_id = config['agentid'] 
            self.aws_root_ca = config['aws_root_ca'] 
            self._target_platform = '' 
            self.historian_setup() 

            # Establish connection
            self.connect_iot()

        # @Core.receiver('onstart')
        def historian_setup(self, **kwargs): 
            try:
                _log.debug(
                    "Setting up to forward to {}".format(destination_vip))
                event = gevent.event.Event()
                agent = Agent(address=destination_vip)
                agent.core.onstart.connect(lambda *a, **kw: event.set(),
                                           event)
                gevent.spawn(agent.core.run)
                event.wait(timeout=10)

                self._target_platform = agent
            except gevent.Timeout:
                _log.debug(
                    "Timeout in setting the agent}")
                self.vip.health.set_status(
                    STATUS_BAD, "Timeout in setup of agent")
                status = Status.from_json(self.vip.health.get_status())
                self.vip.health.send_alert(FORWARD_TIMEOUT_KEY,
                                           status)
            agent.vip.pubsub.subscribe(peer='pubsub', prefix='devices/PNNL/BUILDING1/', callback=self.on_match) 



        def on_match(self, peer, sender, bus, topic, headers, message):
            '''
            Subscribes to the platform message bus on the actuator, record,
            datalogger, and device topics to capture data.
            '''

            _log.debug('GOT DATA FOR: {}'.format(topic)) 
            _log.debug('MESSAGES:{}'.format(message))

            self.publish_to_iot(peer, sender, bus, topic, headers, message)


        def connect_iot(self):
            # Init AWSIoTMQTTClient
            self.myAWSIoTMQTTClient = None
            if useWebsocket:
                self.myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub", useWebsocket=True)
                self.myAWSIoTMQTTClient.configureEndpoint(host, 443)
                _log.debug("ROOT CA: {}".format(self.aws_root_ca))
                self.myAWSIoTMQTTClient.configureCredentials(self.aws_root_ca)
            else:
                self.myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub")
                self.myAWSIoTMQTTClient.configureEndpoint(host, 8883)
                self.myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

            # AWSIoTMQTTClient connection configuration
            self.myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
            self.myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
            self.myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
            self.myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
            self.myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

            # Connect and subscribe to AWS IoT
            self.myAWSIoTMQTTClient.connect()
            self.myAWSIoTMQTTClient.subscribe("devices/PNNL/BUILDING1/", 1, customCallback)  # topic
            time.sleep(2)


        def publish_to_iot(self, peer, sender, bus, topic, headers, message):

            # Set data collection
            results_parametername = list()
            results_parametervalue = []
            topicNameList = []

            try:
                # Format Message
                for element in message[0]:
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    topicname = topic
                    print(topicname)
                    setpoint = element
                    setpoint_value = message[0][element]
                    results_parametervalue.append(setpoint_value)
                    print(setpoint)
                    chars_to_remove = ['(', ')', '(', '\n', '!', '?', '/', ' ', '-']
                    topicname_modified = topic.translate(None, ''.join(chars_to_remove))
                    print(topicname_modified)
                    setpoint_modified = setpoint.translate(None, ''.join(chars_to_remove))
                    msg_txt = '%s' % setpoint_modified
                    results_parametername.append(msg_txt)
                    msg_json = "{\"TopicName\": \"%s\",\"SetPointName\": \"%s\",\"SetPointValue\": %r}"
                    msg_json_formatted = msg_json % (topicname, msg_txt, setpoint_value)
                    print(msg_json_formatted)

                    # Send message to IOT
                    self.myAWSIoTMQTTClient.publish("devices/PNNL/BUILDING1/", "New Message " + str(msg_json_formatted), 1)

            except KeyboardInterrupt:
                print("Sample stopped")

    return AwsSender(**kwargs)


def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(subscriber_agent)
    except Exception as e:
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass

    print("\n Python Version : %s" % sys.version)
    print("Starting the IoT for Volttron")
