/**Alexa: change the Shadow state of your
Place the following code at the top of your AWS Lambda function to load the libraries we are going to use, 
replace the endpoint with the ‘REST API Endpoint’ value you copied earlier.
**/


//Environment Configuration

var config = {};

config.IOT_BROKER_ENDPOINT      = "**************.iot.us-west-2.amazonaws.com".toLowerCase();

config.IOT_BROKER_REGION        = "us-west-2";

config.IOT_THING_NAME           = "Bot";

//Loading AWS SDK libraries

var AWS = require('aws-sdk');

AWS.config.region = config.IOT_BROKER_REGION;

//Initializing client for IoT

var iotData = new AWS.IotData({endpoint: config.IOT_BROKER_ENDPOINT});

/**
 * This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
 * The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well as
 * testing instructions are located at http://amzn.to/1LzFrj6
 *
 * For additional samples, visit the Alexa Skills Kit Getting Started guide at
 * http://amzn.to/1LGWsLG
 */

// Route the incoming request based on type (LaunchRequest, IntentRequest,
// etc.) The JSON body of the request is provided in the event parameter.
exports.handler = function (event, context) {
    try {
        console.log("event.session.application.applicationId=" + event.session.application.applicationId);

        /**
         * Uncomment this if statement and populate with your skill's application ID to
         * prevent someone else from configuring a skill that sends requests to this function.
         */
        /*
        if (event.session.application.applicationId !== "amzn1.echo-sdk-ams.app.[unique-value-here]") {
             context.fail("Invalid Application ID");
        }
        */

        if (event.session.new) {
            onSessionStarted({requestId: event.request.requestId}, event.session);
        }

        if (event.request.type === "LaunchRequest") {
            onLaunch(event.request,
                event.session,
                function callback(sessionAttributes, speechletResponse) {
                    context.succeed(buildResponse(sessionAttributes, speechletResponse));
                });
        } else if (event.request.type === "IntentRequest") {
            onIntent(event.request,
                event.session,
                function callback(sessionAttributes, speechletResponse) {
                    context.succeed(buildResponse(sessionAttributes, speechletResponse));
                });
        } else if (event.request.type === "SessionEndedRequest") {
            onSessionEnded(event.request, event.session);
            context.succeed();
        }
    } catch (e) {
        context.fail("Exception: " + e);
    }
};

/**
 * Called when the session starts.
 */
function onSessionStarted(sessionStartedRequest, session) {
    console.log("onSessionStarted requestId=" + sessionStartedRequest.requestId +
        ", sessionId=" + session.sessionId);
}

/**
 * Called when the user launches the skill without specifying what they want.
 */
function onLaunch(launchRequest, session, callback) {
    console.log("onLaunch requestId=" + launchRequest.requestId +
        ", sessionId=" + session.sessionId);

    // Dispatch to your skill's launch.
    getWelcomeResponse(callback);
}

/**
 * Called when the user specifies an intent for this skill.
 */
function onIntent(intentRequest, session, callback) {
    console.log("onIntent requestId=" + intentRequest.requestId +
        ", sessionId=" + session.sessionId);

    var intent = intentRequest.intent,
        intentName = intentRequest.intent.name;

    // Dispatch to your skill's intent handlers
    if ("SetHeatOnIntent" === intentName) {
        SetDeviceHeatOnInSession(intent, session, callback);
    } else if ("SetHeatOffIntent" === intentName) {
        SetDeviceHeatOffInSession(intent, session, callback);
    } else if ("SetHeatAutoIntent" === intentName) {
        SetDeviceHeatAutoInSession(intent, session, callback);
    } else if ("GetHeatSetpointIntent" === intentName) {
        getDeviceHeatSetpointFromSession(intent, session, callback);

    } else if ("SetFanOnIntent" === intentName) {
        SetDeviceFanOnInSession(intent, session, callback);
    } else if ("SetFanOffIntent" === intentName) {
        SetDeviceFanOffInSession(intent, session, callback);
    } else if ("SetFanAutoIntent" === intentName) {
        SetDeviceFanAutoInSession(intent, session, callback);
    } else if ("GetFanSetpointIntent" === intentName) {
        getDeviceFanSetpointFromSession(intent, session, callback);

    } else if ("SetCoolOnIntent" === intentName) {
        SetDeviceCoolOnInSession(intent, session, callback);
    } else if ("SetCoolOffIntent" === intentName) {
        SetDeviceCoolOffInSession(intent, session, callback);
    } else if ("SetCoolAutoIntent" === intentName) {
        SetDeviceCoolAutoInSession(intent, session, callback);
    } else if ("GetCoolSetpointIntent" === intentName) {
        getDeviceCoolSetpointFromSession(intent, session, callback);


    } else if ("AMAZON.HelpIntent" === intentName) {
        getWelcomeResponse(callback);
    } else if ("AMAZON.StopIntent" === intentName || "AMAZON.CancelIntent" === intentName) {
        handleSessionEndRequest(callback);
    } else {
        throw "Invalid intent";
    } 

    //
}


/**
 * Called when the user ends the session.
 * Is not called when the skill returns shouldEndSession=true.
 */
function onSessionEnded(sessionEndedRequest, session) {
    console.log("onSessionEnded requestId=" + sessionEndedRequest.requestId +
        ", sessionId=" + session.sessionId);
    // Add cleanup logic here
}

// --------------- Functions that control the skill's behavior -----------------------

function getWelcomeResponse(callback) {
    // If we wanted to initialize the session to have some attributes we could add those here.
    var sessionAttributes = {};
    var cardTitle = "Welcome";
    var speechOutput = "Welcome to the Alexa Demo Skill. " +
        "Please tell me which device and what setpoint you want to set your device to";
    // If the user either does not reply to the welcome message or says something that is not
    // understood, they will be prompted again with this text.
    var repromptText = "Please tell what to set the device to, " +
        "set the device to one";
    var shouldEndSession = false;

    callback(sessionAttributes,
        buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession));
}

function handleSessionEndRequest(callback) {
    var cardTitle = "Session Ended";
    var speechOutput = "Thank you for trying the Alexa Demo Skill. Have a nice day!";
    // Setting this to true ends the session and exits the skill.
    var shouldEndSession = true;

    callback({}, buildSpeechletResponse(cardTitle, speechOutput, null, shouldEndSession));
}

//heat
function SetDeviceHeatOnInSession (intent, session, callback) {
	var setpoint = 2;
	setDeviceHeatSetpointHelper(intent, session, callback, setpoint);
}

function SetDeviceHeatOffInSession (intent, session, callback) {
	var setpoint = 1;
	setDeviceHeatSetpointHelper(intent, session, callback, setpoint);
}

function SetDeviceHeatAutoInSession (intent, session, callback) {
	var setpoint = 0;
	setDeviceHeatSetpointHelper(intent, session, callback, setpoint);
}

//fan
function SetDeviceFanOnInSession (intent, session, callback) {
    var setpoint = 2;
    setDeviceFanSetpointHelper(intent, session, callback, setpoint);
}

function SetDeviceFanOffInSession (intent, session, callback) {
    var setpoint = 1;
    setDeviceFanSetpointHelper(intent, session, callback, setpoint);
}

function SetDeviceFanAutoInSession (intent, session, callback) {
    var setpoint = 0;
    setDeviceFanSetpointHelper(intent, session, callback, setpoint);
}

//cool
function SetDeviceCoolOnInSession (intent, session, callback) {
    var setpoint = 2;
    setDeviceCoolSetpointHelper(intent, session, callback, setpoint);
}

function SetDeviceCoolOffInSession (intent, session, callback) {
    var setpoint = 2;
    setDeviceCoolSetpointHelper(intent, session, callback, setpoint);
}

function SetDeviceCoolAutoInSession (intent, session, callback) {
    var setpoint = 2;
    setDeviceCoolSetpointHelper(intent, session, callback, setpoint);
}

function getThingShadowSetpoint(point_name){
    var setPoint = 0;
    var params = {
        "thingName" : config.IOT_THING_NAME,
    };
    
    iotData.getThingShadow(params, function(err, data) {
        
          if (err){
            //Handle the error here
            //print("setpoint_from_getThingShadowSetpoint_if : " + setPoint);
            console.log("setpoint_from_getThingShadowSetpoint_if : " + setPoint);
          }
          else {
            var body = JSON.parse(data.payload);
            setPoint = body.state.desired.HeatOverride;//point_name
            //print("setpoint_from_getThingShadowSetpoint_else : " + setPoint);
            console.log("setpoint_from_getThingShadowSetpoint_else : " + setPoint);
          }    

        });
    console.log("setpoint_from_getThingShadowSetpoint : " + setPoint);
    return setPoint;
}



function setDeviceSetpoint(intent, session, callback, payloadObj) {
    var repromptText = null;
    var sessionAttributes = {};
    var shouldEndSession = true;
    var speechOutput = "";

    //Prepare the parameters of the update call
    var paramsUpdate = {
        "thingName" : config.IOT_THING_NAME,
        "payload" : JSON.stringify(payloadObj)
    };

    //Update Device Shadow
    iotData.updateThingShadow(paramsUpdate, function(err, data) {
      if (err){
        //Handle the error here
      }
      else {
        speechOutput = "The device has been set!";
        console.log(data);
        callback(sessionAttributes,buildSpeechletResponse(intent.name, speechOutput, repromptText, shouldEndSession));
      }    

    });

}


function setDeviceHeatSetpointHelper(intent, session, callback, setpoint) {
    point_fan = "SupplyFanOverride";
    point_cool = "CoolOverride2";

    fan_setpoint = getThingShadowSetpoint(point_fan); 
    cool_setpoint = getThingShadowSetpoint(point_cool);
    console.log("setDeviceHeatSetpointHelper setpoint : " + cool_setpoint);


    var payloadObj={ "state":
                          { "desired":
                                   { "HeatOverride":setpoint,
                                     "SupplyFanOverride":fan_setpoint,
                                     "CoolOverride2":cool_setpoint,
                                    }
                          }
                 };

    setDeviceSetpoint(intent, session, callback, payloadObj)
}

function setDeviceFanSetpointHelper(intent, session, callback, setpoint) {
    point_heat = "HeatOverride";
    point_cool = "CoolOverride2";
    heat_setpoint = getThingShadowSetpoint(point_heat); 
    cool_setpoint = getThingShadowSetpoint(point_cool);

    var payloadObj={ "state":
                          { "desired":
                                   { "HeatOverride":heat_setpoint,
                                     "SupplyFanOverride":setpoint,
                                     "CoolOverride2":cool_setpoint,
                                    }
                          }
                 };

    setDeviceSetpoint(intent, session, callback, payloadObj);
}

function setDeviceCoolSetpointHelper(intent, session, callback, setpoint) {
    heat_setpoint = 0; 
    fan_setpoint = 0; 
     


    var payloadObj={ "state":
                          { "desired":
                                   { "HeatOverride":heat_setpoint,
                                     "SupplyFanOverride":fan_setpoint,
                                     "CoolOverride2":setpoint,
                                    }
                          }
                 };

    setDeviceSetpoint(intent, session, callback, payloadObj);
}



function getDeviceHeatSetpointFromSession(intent, session, callback) {

    var repromptText = null;
    var sessionAttributes = {};
    var shouldEndSession = true;
    var speechOutput = "";
    
    var params = {
        "thingName" : config.IOT_THING_NAME,
    };

    iotData.getThingShadow(params, function(err, data) {
    
      if (err){
        //Handle the error here
      }
      else {
        var body = JSON.parse(data.payload);
        var setPoint = body.state.desired.HeatOverride;
        speechOutput = "The setpoint value is " + setPoint + ". Goodbye.";
        console.log(data);
        callback(sessionAttributes,buildSpeechletResponse(intent.name, speechOutput, repromptText, shouldEndSession));
      }    

    });
}

function getDeviceFanSetpointFromSession(intent, session, callback) {

    var repromptText = null;
    var sessionAttributes = {};
    var shouldEndSession = true;
    var speechOutput = "";
    
    var params = {
        "thingName" : config.IOT_THING_NAME,
    };

    iotData.getThingShadow(params, function(err, data) {
    
      if (err){
        //Handle the error here
      }
      else {
        var body = JSON.parse(data.payload);
        var setPoint = body.state.desired.SupplyFanOverride;
        speechOutput = "The setpoint value is " + setPoint + ". Goodbye.";
        console.log(data);
        callback(sessionAttributes,buildSpeechletResponse(intent.name, speechOutput, repromptText, shouldEndSession));
      }    

    });
}

function getDeviceCoolSetpointFromSession(intent, session, callback) {

    var repromptText = null;
    var sessionAttributes = {};
    var shouldEndSession = true;
    var speechOutput = "";
    
    var params = {
        "thingName" : config.IOT_THING_NAME,
    };

    iotData.getThingShadow(params, function(err, data) {
    
      if (err){
        //Handle the error here
      }
      else {
        var body = JSON.parse(data.payload);
        var setPoint = body.state.desired.CoolOverride2;
        speechOutput = "The setpoint value is " + setPoint + ". Goodbye.";
        console.log(data);
        callback(sessionAttributes,buildSpeechletResponse(intent.name, speechOutput, repromptText, shouldEndSession));
      }    

    });
}

// --------------- Helpers that build all of the responses -----------------------

function buildSpeechletResponse(title, output, repromptText, shouldEndSession) {
    return {
        outputSpeech: {
            type: "PlainText",
            text: output
        },
        card: {
            type: "Simple",
            title: "SessionSpeechlet - " + title,
            content: "SessionSpeechlet - " + output
        },
        reprompt: {
            outputSpeech: {
                type: "PlainText",
                text: repromptText
            }
        },
        shouldEndSession: shouldEndSession
    };
}

function buildResponse(sessionAttributes, speechletResponse) {
    return {
        version: "1.0",
        sessionAttributes: sessionAttributes,
        response: speechletResponse
    };
}