
# VOLTTRON - ECHO

Volttron-Amazon Echo uses Alexa voice commands to turn on/off heat, fan, cooling devices on the demo board. End to end connection between Amazon Echo and Volttron’s demo board is established by writing Alexa Skills to change device state in the cloud (Amazon-Iot), and also Volttron agent aws_shadow.  The Toggle Demoboard Alexa skill makes changes to the device shadow state , located in AWS-IoT, and aws_shadow listens for changes in the desired device shadow state. When a delta is heard, the aws_shadow is triggers the actuator method to turn on/off devices on the demoboard.  
  

###########################################################################################################

# Explanation of AWS_Shadow Agent
# aws_shadow.py, basic_shadow_updater.py
Aws_Shadow agent listens for deltas from the device shadow located in the cloud, Amazon-Iot, and updates the setpoints for the physical devices on the demo board.  

Amazon provides basic examples for how to update and change the device shadow in their IoT service. The Volttron agent, aws-shadow adopts much of Amazon’s basic example code and is tweaked to run as a Volttron agent. ``aws_shadow.py`` is in charge of listening for changes in device shadow state and triggering the actuator to turn on or off devices on the demo board.  The second example code by Amazon, ``basicShadowUpdater.py``, demonstrates how to change the desired state of the device shadow. 

In this example we will use ``basicShadowUpdater.py`` to reset and clear the device shadow state to zero. ``basicShadowUpdater.py`` performs a shadow update in a loop to continuously modify the desired state of the shadow by changing the value of the integer attribute. In this code, the integer attribute is set to zero. 

``aws_shadow.py`` subscribes to the delta topic of the same shadow and receives delta messages when there is a difference between the desired and reported states.

As the desired state is being updated by basicShadowUpdater, a series of delta messages corresponding to the shadow update requests are received by the aws_shadow agent. After the basicShadowUpdater begins sending shadow update requests, you should be able to see corresponding delta messages in the aws_shadow output.

Run ``basicShadowUpdater.py`` for the first cycle to set the shadow device to zeros for all heat/fan/cool device. Then ctl-c to stop.

1) Enter in the command line ‘Volttron-ctl status’, check to see that the actuator and master driver agents are first running before running aws_shadow agent.

2) Run AGENT_CONFIG=config python -m aws_shadow.aws_shadow

3) Run python basicShadowUpdater.py -e **************.iot.us-west-2.amazonaws.com -r aws-iot-rootCA.crt -w

4) The final step is to use Alexa Demo Skills to change the shadow device’s desired state, so that the aws_shadow agent can register the change and trigger the actuator to turn on/off devices on the demo board.

Resources:

https://github.com/aws/aws-iot-device-sdk-python/tree/master/samples


# Explanation of Alexa Demo Skills
# alexa_demo_skills.js
Alexa demo skill is written for device shadow Bot.

You can edit alexa_demo_skills.js to update alexa skills. Login to aws.amazon.com to save code in 
AWS lambda, alexa_demoboard lambda function. (be sure region is set to US-East, Alexa is not yet 
available in US-West-2)
	
login to developer.amazon.com  alexa_demo_IntentScheme.js.  Edit this file to update alexa skills 
interaction model. Save code in the interaction model segment of in the developer website.

To activate Amazon Alexa, say “Alexa Toggle Demoboard”

Use echo commands to change setpoints on device shadow : 
	SetHeatOnIntent heat two
	SetHeatOffIntent heat one
	SetHeatAutoIntent heat zero
Use echo commands to change get setpoints from device shadow :
GetHeatSetpointIntent what is the heat set point
	GetHeatSetpointIntent what's the heat set point

For voice simulation, sign into developer.amazon.com, enter simulation through Toggle Demo Board skill

https://developer.amazon.com

Resources:

https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/developing-an-alexa-skill-as-a-lambda-function

https://aws.amazon.com/blogs/aws/aws-iot-cloud-services-for-connected-devices/

https://developer.amazon.com/public/community/post/Tx3828JHC7O9GZ9/Using-Alexa-Skills-Kit-and-AWS-IoT-to-Voice-Control-Connected-Devices


################################################################################################################

# VOLTTRON - AMAZON IOT
Amazon Iot Device Shadow can be updated with Volttron Central data using Aws_Shadow agent and Aws_Shadow_Updater.

################################################################################################################

# Sending Volttron data to Amazon-Iot
# aws_shadow_updater.py, aws_shadow.py
This agent demonstrates the use of updating shadow with Volttron Central data. It has two scripts, ``aws_shadow_updater.py`` and ``aws_shadow.py``. The aws_shadow_updater script is subscribed to Volttron Central through VIP setup. The aws_shadow scripts listens to delta events and updates the shadow in AWS iot cloud. 

``aws_shadow_updater.py`` subscribes to VC on_match for the defined prefix, ie 'devices/PNNL/BUILDING1' and puts messages in a queue.  perform a shadow update in a loop to
continuously modify the desired state of the shadow by changing the
value of the integer attribute.

``aws_shadow.py`` subscribes to VC, and the delta topic of the same shadow and receives delta messages when there is a difference between the desired and reported states.
Because only the desired state is being updated by basicShadowUpdater, a series of delta messages that correspond to the shadow update requests should be received in aws_shadow.py.

# Volttron Central publishing and subscribing to Amazon-Iot
# aws_publisher.py
This agent demonstrates a simple MQTT publish using AWS IoT and VIP subscribing to Volttron Central. 
It first subscribes to a topic and registers a callback to print new messages and then publishes to the 
same topic. New messages are printed upon receipt, indicating the callback function has been called.
