'''
List manager is an echo skill to add an item to mylistmanager
'''
import json
import requests
import config as c

appVersion = '0.1'

def lambda_handler(event, context):
    session = event['session']
    request = event['request']
    requestType = request['type']
	
    if requestType == "LaunchRequest":
        response = launch_request(session, request)
    elif requestType == "IntentRequest":
        response = intent_request(session, request)
    else:
        output_speech = "I couldn't tell which type of request that was.  Try again."
        response= {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}}

    response['version'] = appVersion
    print json.dumps(response) 

    return response

def launch_request(session, request):
    output_speech = "Welcome to List Manager. You can add a new item."
    response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}
    return response

def intent_request(session, request):

    intent = request['intent']['name']
    print "intent_request: {}".format(intent)

    if intent ==  "AddItem":

        title = request['intent']['slots']['mytitle']['value']
        data={'title':title, 'note':"This was created via Amazon Echo"}
        output_speech = "I added item {}.  What is the context?".format(title)
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}, "sessionAttributes":{'title':title}}
        return response

    elif intent ==  "SetContext":

        context = request['intent']['slots']['mycontext']['value']
        title = session['attributes']['title']
        data={'title':title, 'context':context, 'note':"This was created via Amazon Echo"}
        r = requests.post(c.ec_uri+":5000/incoming_from_echo", json=data)
        output_speech = "The item will be place in context {}. Do you want it to be starred?".format(context)
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}, "sessionAttributes"{'title':title, 'context':context}}
        return response

    elif intent == "AMAZON.YesIntent":

        star = True
        # ? should use dict.copy()
        title = session['attributes']['title']
        context = session['attributes']['context']
        data={'title':title, 'context':context, 'star':True}
        r = requests.post(c.ec_uri+":5000/incoming_from_echo", json=data)
        output_speech = "The item will be starred".format(context)
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}}
        return response

    elif intent == "AMAZON.NoIntent":

        star = False
        title = session['attributes']['title']
        context = session['attributes']['context']
        data={'title':title, 'context':context, 'star':False}
        r = requests.post(c.ec_uri+":5000/incoming_from_echo", json=data)
        output_speech = "The item will not be starred".format(context)
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}}
        return response

    else:
        output_speech = "I couldn't tell which type of intent request that was.  Try again."
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}}
        return response
