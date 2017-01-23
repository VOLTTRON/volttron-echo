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

from datetime import datetime, timedelta
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
from threading import Thread
from zmq.utils import jsonapi


# AWS basic shadow
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import time
import json

# global varaibles for iot certificates --------
useWebsocket = True
host = "**************.iot.us-west-2.amazonaws.com"
rootCAPath = "aws-iot-rootCA.crt"
certificatePath = ""
privateKeyPath = ""

# global variable for iot ------------------------
# timeout = 241000
# minimum_polling_time = 1
# receive_context = 0
# received_count = 0
# i=0

# global counters
# receive_callbacks = 0
# send_callbacks = 0
# flag=0

#
utils.setup_logging()
_log = logging.getLogger(__name__)
__version__ = '3.0'
FORWARD_TIMEOUT_KEY = 'FORWARD_TIMEOUT_KEY'

'''
Structuring the agent this way allows us to grab config file settings 
for use in subscriptions instead of hardcoding them.
'''

# this is a publishing agent. listener agent will subscribe.
def subscriber_agent(config_path, **kwargs):
    print(config_path)
    config = utils.load_config(config_path)
    agent_id = config['agentid']

    # VC vip is currently being used
    destination_vip = config.get('destination-vip')
    _log.debug("destination vip: {}".format(destination_vip))


    class AwsShadow(Agent):
        '''
        This agent demonstrates usage of the 3.0 pubsub service as well as
        interfacting with the historian. This agent is mostly self-contained,
        but requires the histoiran be running to demonstrate the query feature.
        '''

        def __init__(self, **kwargs):
            super(AwsShadow, self).__init__(**kwargs)
            self.async_call = AsyncCall()
            self._retry_period=300.0
            self._process_thread = Thread(target=self._process_loop) # run agent
            self._process_thread.daemon = True  # Don't wait on thread to exit.
            self._process_thread.start()

        @Core.receiver('onsetup')
        def setup(self, sender, **kwargs):
            # Demonstrate accessing a value from the config file
            self.aws_root_ca = config['aws_root_ca']
            self._target_platform = ''
            self._agent_id = config['agentid']

        def shadow_updated(self, shadow): #for customShadowCallback_Delta.
            _log.debug("Current shadow: " +str(shadow))

        def shadow_actuator(self, shadow): # shadow as argument for actuator
            try:
                start = str(datetime.now()) # request for time to access device
                end = str(datetime.now() + timedelta(minutes=1))

                msg = [
                    ['PNNL/DEMO/M2000', start, end] 
                    ]
                result = self.vip.rpc.call(
                                            'platform.actuator',
                                            'request_new_schedule', #request sent to actuator
                                            agent_id,
                                            "some task",
                                            'HIGH',
                                            msg).get(timeout=10)
                print("schedule result", result['result'])
            except Exception as e:
                print("Could not contact actuator. Is it running?")
                print(e)
                #return

            result = self.vip.rpc.call(
                                            'platform.actuator',
                                            'set_point', # command for set point
                                            agent_id,
                                            'PNNL/DEMO/M2000/HeatOverride', # some_point is the actual point
                                            shadow['state']['HeatOverride']).get(timeout=4) # payload value for 0.0 ie desired heat value from payload
            print("Set result", result)

            result = self.vip.rpc.call(
                'platform.actuator',
                'request_cancel_schedule',  # request sent to actuator
                agent_id,
                "some task").get(timeout=10)
            print("Cancel result", result)

        # all device shadow and iot stuff put in this thread
        def _process_loop(self):
            """
            The process loop is called off of the main thread and will not exit
            unless the main agent is shutdown.
            """
            _log.debug("Starting process loop.")

            # basicShadowListener.py
            def customShadowCallback_Delta(payload, responseStatus, token):
                # payload is a JSON string ready to be parsed using json.loads(...)
                # in both Py2.x and Py3.x

                payloadDict = json.loads(payload)
                _log.debug("payloadDict setpoint_value:{}".format(payloadDict))

                # give thread to asyn_call for gevent to pickup
                # Send a function to the hub to be called there.
                # (self, receiver, func, *args, **kwargs)
                self.async_call.send(None, self.shadow_updated, # None for no reciever
                                     payloadDict)

                # payloadDict of new setpoint values to be used for actuating device
                self.async_call.send(None, self.shadow_actuator,
                                     payloadDict) # does not take an argument, needs to be fixed

            def connect_shadow():
                # Init AWSIoTMQTTShadowClient
                myAWSIoTMQTTShadowClient = None
                if useWebsocket:
                    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("basicShadowDeltaListener", useWebsocket=True)
                    myAWSIoTMQTTShadowClient.configureEndpoint(host, 443)
                    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath)
                else:
                    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("basicShadowDeltaListener")
                    myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
                    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

                # AWSIoTMQTTShadowClient configuration
                myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
                myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
                myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

                # Connect to AWS IoT
                myAWSIoTMQTTShadowClient.connect()

                # Create a deviceShadow with persistent subscription
                Bot = myAWSIoTMQTTShadowClient.createShadowHandlerWithName("Bot", True)

                # Listen on deltas
                Bot.shadowRegisterDeltaCallback(customShadowCallback_Delta)


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

            # Establish connection
            connect_shadow()
            configure_logging()

    return AwsShadow(**kwargs)


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
