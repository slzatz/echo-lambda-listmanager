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
        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}

    print json.dumps(response) 

    return {"version":appVersion,"response":response}

def launch_request(session, request):
    output_speech = "Welcome to List Manager. You can add a new item."
    response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}
    return response

def intent_request(session, request):

    intent = request['intent']['name']
    print "intent_request: {}".format(intent)

    if intent ==  "AddItem":

        try:
            context = request['intent']['slots']['mycontext']['value']
        except KeyError:
            context = None

        title = request['intent']['slots']['title']['value']
        #client = boto3.client('ses')
        #The below should not be an email to cloudmailin, it should be a direct post to the server (dummy)
        #response = client.send_email(Source='slzatz@gmail.com', Destination={'ToAddresses':['6697b86bca34dcd126cb@cloudmailin.net']}, Message={'Subject':{'Data':item+mods}, 'Body':{'Text':{'Data':'Hi'}}})
        #r = requests.post("http://httpbin.org/post", data = {"key":"value"})
        #r = requests.post("http://54...:5000/incoming", data={"headers[Subject]":"This is a test of posting", 'plain':"hello"})
        #r = requests.post("http://54...:5000/incoming", data={"headers[Subject]":item+mods, 'plain':"This was created via Amazon Echo"})
        data={'title':title, 'note':"This was created via Amazon Echo"}
        if context:
            data.update({'context':context}) 
        r = requests.post(c.ec_uri+":5000/incoming_from_echo", data=data})
        output_speech = "I added item {} to context".format(title, context if context else "No Context")
        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    else:
        output_speech = "I couldn't tell which type of intent request that was.  Try again."
        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}
        return response
