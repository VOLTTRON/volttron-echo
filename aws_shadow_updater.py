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
# Citation
# base historian
# https://github.com/kmonson/volttron/blob/develop/volttron/platform/agent/base_historian.py

# subscriber agent
from __future__ import absolute_import, print_function

from datetime import datetime
import logging
import random
import sys
import gevent

from volttron.platform.async import AsyncCall
from volttron.platform.vip.agent import Agent, Core, PubSub, compat
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod
from volttron.platform.messaging.health import (STATUS_BAD,
                                                STATUS_GOOD, Status)

# base_historian
from Queue import Queue, Empty
from threading import Thread
from zmq.utils import jsonapi

# AWS basic shadow
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import time
import json

# global varaibles for iot certificates --------
useWebsocket = True
host = "*************.iot.us-west-2.amazonaws.com"
rootCAPath = "aws-iot-rootCA.crt"
certificatePath = ""
privateKeyPath = ""

# ---------------------------------------------------
utils.setup_logging()
_log = logging.getLogger(__name__)
__version__ = '3.0'
FORWARD_TIMEOUT_KEY = 'FORWARD_TIMEOUT_KEY'

'''
Structuring the agent this way allows us to grab config file settings
for use in subscriptions instead of hardcoding them.
'''
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

# this is a publishing agent. listener agent will subscribe.
def subscriber_agent(config_path, **kwargs):
    print(config_path)
    config = utils.load_config(config_path)
    agent_id = config['agentid']  

    # VC vip is currently being used
    destination_vip = config.get('destination-vip')
    _log.debug("destination vip: {}".format(destination_vip))

    class AwsShadowUpdater(Agent):
        '''
        This agent demonstrates usage of the 3.0 pubsub service as well as
        interfacting with the historian. This agent is mostly self-contained,
        but requires the histoiran be format_to_jsonning to demonstrate the query feature.
        '''

        def __init__(self, **kwargs):
            super(AwsShadowUpdater, self).__init__(**kwargs)

            self._event_queue = Queue()
            self._process_thread = Thread(target=self._process_loop) #run agent updater, historian setup
            self._process_thread.daemon = True  # Don't wait on thread to exit.
            self._process_thread.start()

        @Core.receiver('onsetup')
        def setup(self, sender, **kwargs):
            # Demonstrate accessing a value from the config file
            self.aws_root_ca = config['aws_root_ca']
            self._target_platform = ''
            self._agent_id = config['agentid']
            self.historian_setup()  # get volttron central messages on match

        #subscribes to volttron central
        def historian_setup(self, **kwargs):
            try:
                _log.debug(
                    "Setting up to forward to {}".format(destination_vip))  # connect to volttron central
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

            agent.vip.pubsub.subscribe(peer='pubsub', prefix='devices/PNNL/BUILDING1', 
                                      callback=self.on_match)


        def on_match(self, peer, sender, bus, topic, headers, message):
            '''
            Subscribes to the platform message bus on the actuator, record,
            datalogger, and device topics to capture data.
            '''

            _log.debug('GOT DATA FOR: {}'.format(topic))
            _log.debug('MESSAGES:{}'.format(message))

            #push messages to queue
            self._event_queue.put(message) #has all points and meta data. LIST WITH 2 ITEM, 2ND KEY VALUE PAIR OF ALL POINTS TO META DATA

        _log.debug("Finished processing on_match.")

        # infinite loop
        # wait for things to appear in queue, will block until pushed into it. Gevent loop. Thread wakes up.
        def _process_loop(self):
            """
            The process loop is called off of the main thread and will not exit
            unless the main agent is shutdown.
            """
            _log.debug("Starting process loop.")


            def customShadowCallback_Update(payload, responseStatus, token):
                _log.debug("Shadow updated. {}".format(payload)) # format it to string and puts it in


            def customShadowCallback_Delete(payload, responseStatus, token):
                # payloadDict of new setpoint values to be used for actuating device
                _log.debug("Shadow deleted. {}".format(payload))

            def connect_shadow():
                _log.debug("Connecting to shadow.")

                # Init AWSIoTMQTTShadowClient
                myAWSIoTMQTTShadowClient = None
                if useWebsocket:
                    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("aws_shadow_updater", useWebsocket=True)
                    myAWSIoTMQTTShadowClient.configureEndpoint(host, 443)
                    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath)
                else:
                    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("aws_shadow_updater")
                    myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
                    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

                # AWSIoTMQTTShadowClient configuration
                myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
                myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
                myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

                # Connect to AWS IoT
                myAWSIoTMQTTShadowClient.connect()

                # Create a deviceShadow with persistent subscription
                Bot = myAWSIoTMQTTShadowClient.createShadowHandlerWithName("Bot", True)  # Delete shadow JSON doc
                Bot.shadowDelete(customShadowCallback_Delete, 5)

                return Bot

            def publish_to_shadow(Bot, new_to_publish_message):

                _log.debug("Publishing to shadow.")

                #one message in queue
                setpoint = new_to_publish_message

                payload = {
                    "state":
                        {
                            "desired":
                                {
                                    "setpoint_name": setpoint,  # property
                                    #"setpoint_value": setpoint_value

                                }
                        }
                }

                JSONPayload = json.dumps(payload)
                Bot.shadowUpdate(JSONPayload, customShadowCallback_Update,5)

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

                _log.debug("Configured logging.")

            # Establish connection
            # wait for things to appear in queue, block until pushed onto queue
            # calls get, queue object, get returns, thread wakes up, exit loop
            # thread safe with queue
            Bot = connect_shadow()

            configure_logging()

            wait_for_input = True

            while True:

                _log.debug("Reading from/waiting for queue.")
                # blocks waiting on queue
                new_to_publish_message = self._event_queue.get(wait_for_input)

                _log.debug("Exited if-statement new_to_publish_messages")
                publish_to_shadow(Bot, new_to_publish_message)

    return AwsShadowUpdater(**kwargs)


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
