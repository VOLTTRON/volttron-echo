######################################################################################################### 

#volttron-echo
Amazon Echo–Volttron
Use Alexa voice commands to turn on/off heat/fan/cool devices on the demo board. 
End to end connection between Amazon Echo and Volttron’s demo board is established by using 
the custom made Alexa Skill – Toggle Demoboard skill with Volttron agent aws_shadow.  
The Toggle Demoboard skill makes changes to the device shadow state , located in AWS-IoT, 
and aws_shadow listens for the deltas. When a delta is heard, the aws_shadow is triggers the 
actuator method to turn on/off devices on the demoboard.  

###########################################################################################################

# AWS_Shadow agent
# aws_shadow.py
Aws_Shadow agent listens for deltas from the device shadow in the cloud and updates the setpoints 
for the physical devices on the demo board.  

This example demonstrates the use of basic shadow operations (update/delta). It has two scripts, 
``basicShadowUpdater.py`` and ``aws_shadow.py``. The agent shows how an shadow update
request triggers delta events.

``basicShadowUpdater.py`` performs a shadow update in a loop to continuously modify the desired state 
of the shadow by changing the value of the integer attribute.

``aws_shadow.py`` subscribes to the delta topic of the same shadow and receives delta messages when 
there is a difference between the desired and reported states.

Because only the desired state is being updated by basicShadowUpdater, a series of delta messages that 
correspond to the shadow update requests should be received in aws_shadow.

After the basicShadowUpdater starts sending shadow update requests, you should be able to see corresponding 
delta messages in the aws_shadow output.

Use the first cycle to set the shadow device to zeros for all heat/fan/cool device. Then ctl-c to stop.

Volttron-ctl status, see that the actuator and master driver agents are running.

# Alexa Demo Skills
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

################################################################################################################

# Amazon-Iot Device Shadow - Volttron
Amazon Iot Device Shadow can be updated with Volttron Central data using Aws_Shadow agent and Aws_Shadow_Updater.

################################################################################################################

# Using AwsShadowUpdater for sending Volttron data to Iot
# aws_shadow_updater.py, aws_shadow.py, basicShadowUpdater.py, 
This agent demonstrates the use of updating shadow with Volttron Central data. It has two scripts, ``aws_shadow_updater.py`` and ``aws_shadow.py``. The aws_shadow_updater script is subscribed to Volttron Central through VIP setup. The aws_shadow scripts listens to delta events and updates the shadow in AWS iot cloud. 

``aws_shadow_updater.py`` subscribes to VC on_match for the defined prefix, ie 'devices/PNNL/BUILDING1' and puts messages in a queue.  perform a shadow update in a loop to
continuously modify the desired state of the shadow by changing the
value of the integer attribute.

``aws_shadow.py`` subscribes to VC, and the delta topic of the same shadow and receives delta messages when there is a difference between the desired and reported states.
Because only the desired state is being updated by basicShadowUpdater, a series of delta messages that correspond to the shadow update requests should be received in aws_shadow.py.

# Iot-Volttron pubsub
# aws_publisher.py
This agent demonstrates a simple MQTT publish using AWS IoT and VIP subscribing to Volttron Central. 
It first subscribes to a topic and registers a callback to print new messages and then publishes to the 
same topic. New messages are printed upon receipt, indicating the callback function has been called.
