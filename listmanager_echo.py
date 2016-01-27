'''
List manager is an echo skill to add an item to mylistmanager

CreateItem Create {mytitle}
CreateItem Create item {mytitle}
CreateItem Add {mytitle}
CreateItem Add item {mytitle}
SetContext {mycontext}
SetContext The context is {mycontext}
RetrieveContextItems Retrieve context {mycontext}
RetrieveContextItems Retrieve items from context {mycontext}
RetrieveContextItems Retrieve tasks from context {mycontext}
RetrieveContextItems Get context {mycontext}
RetrieveContextItems Get items from context {mycontext}
RetrieveContextItems Get tasks from context {mycontext}
RetrieveFolderItems Retrieve folder {myfolder}
RetrieveFolderItems Retrieve items from folder {myfolder}
RetrieveFolderItems Retrieve tasks from folder {myfolder}
RetrieveFolderItems Get folder {myfolder}
RetrieveFolderItems Get items from folder {myfolder}
RetrieveFolderItems Get tasks from folder {myfolder}
RetrieveAllItems Retrieve all items
RetrieveAllItems Get all items
RetrieveSpecificItems Find {queryterm}
RetrieveSpecificItems Search {queryterm}
RetrieveStarredItems Retrieve starred {mycontext} items
RetrieveStarredItems Get starred {mycontext} items
RetrieveStarredItems Retrieve starred items from {mycontext} 
RetrieveStarredItems Get starred items from {mycontext} 
RetrieveStarredItems Retrieve starred {mycontext} tasks
RetrieveStarredItems Get starred {mycontext} tasks
RetrieveStarredItems Retrieve starred tasks from {mycontext} 
RetrieveStarredItems Get starred tasks from {mycontext}
'''
import json
import requests
import config as c
from lmdb_lambda import *
from datetime import datetime, timedelta
import pysolr

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
    output_speech = "Welcome to List Manager. You can create a new item and more."
    response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}
    return response

def intent_request(session, request):

    intent = request['intent']['name']
    print "intent_request: {}".format(intent)

    if intent ==  "CreateItem":

        title = request['intent']['slots']['mytitle']['value']
        data={'title':title, 'note':"This was created via Amazon Echo"}
        output_speech = "You want to add: {}.  What is the context?".format(title)
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}, 'sessionAttributes':{'title':title}}
        return response

    elif intent ==  "SetContext":

        context = request['intent']['slots']['mycontext']['value']
        title = session['attributes']['title']
        data={'title':title, 'context':context, 'note':"This was created via Amazon Echo"}
        #r = requests.post(c.ec_uri+":5000/incoming_from_echo", json=data)
        output_speech = "The item will be place in context {}. Do you want it to be starred?".format(context)
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}, 'sessionAttributes':{'title':title, 'context':context}}
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

    elif intent == "RetrieveFolderItems":
        folder_title = request['intent']['slots']['myfolder'].get('value', '')
        folder_title = folder_title.lower()
        count = remote_session.query(Task).join(Folder).filter(and_(Folder.title==folder_title, Task.completed==None, Task.deleted==False, datetime.now()-Task.modified<timedelta(days=30))).count()
        tasks = remote_session.query(Task).join(Folder).filter(and_(Folder.title==folder_title, Task.completed==None, Task.deleted==False, datetime.now()-Task.modified<timedelta(days=30))).limit(10).all()

        if count:
            output_speech = "The total number of tasks is {}. ".format(count)
            now = datetime.now()
            for n,task in enumerate(tasks, start=1):
                output_speech+="{}, {}. Modified {} days ago. ".format(n, task.title, (now-task.modified).days)
        else:
            output_speech = "I did not find anything."

        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}}
        return response

    elif intent == "RetrieveContextItems":
        # TO DO: count the tasks and report on the number and then take the first X (probably ~ 10)
        #context_title = request['intent']['slots']['mycontext']['value']
        context_title = request['intent']['slots']['mycontext'].get('value', '')
        context_title = context_title.lower()
        count = remote_session.query(Task).join(Context).filter(and_(Context.title==context_title, Task.completed==None, Task.deleted==False, datetime.now()-Task.modified<timedelta(days=30))).count()
        tasks = remote_session.query(Task).join(Context).filter(and_(Context.title==context_title, Task.completed==None, Task.deleted==False, datetime.now()-Task.modified<timedelta(days=30))).limit(10).all()

        if count:
            output_speech = "The total number of tasks is {}. ".format(count)
            now = datetime.now()
            for n,task in enumerate(tasks, start=1):
                output_speech+="{}, {}. Modified {} days ago. ".format(n, task.title, (now-task.modified).days)

        else:
            output_speech = 'I did not find anything.'

        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}}
        return response

    elif intent == "RetrieveAllItems":
        #tasks = remote_session.query(Task).filter(Task.star==True).all()
        #tasks = remote_session.query(Task).join(Context).filter(and_(Context.title=='work', Task.star==True, Task.completed==None, datetime.now()-Task.modified<timedelta(days=30))).all()
        try:
            f = remote_session.query(Folder).filter_by(title='echo').one()
        except sqla_orm_exc.NoResultFound:
            tasks = []
        else:
            tasks = f.tasks

        if tasks:
            output_speech = ''
            for n,task in enumerate(tasks, start=1):
                output_speech+='{}, {}. '.format(n, task.title)
        else:
            output_speech = 'I did not find anything.'

        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}}
        return response

    elif intent =="RetrieveSpecificItems":
        solr = pysolr.Solr(c.ec_uri+':8983/solr/listmanager/', timeout=10)
        queryterm = request['intent']['slots']['queryterm']['value']
        #Initially thought the queryterm could be queryterms and hence the below
        #s = 'title:' + ' AND title:'.join(queryterm.split())
        #s = s + ' note:' + ' AND note:'.join(queryterm.split())
        s = 'title:{} note:{} tag:{}'.format(*(3*(queryterm,)))
        fq = ['star:true', 'completed:false']
        result = solr.search(s, fq=fq) # rows=1 or **{'rows':1}
        if len(result):
            output_speech = ''
            for n,task in enumerate(result.docs, start=1):
                output_speech+='{}, {}. '.format(n, task['title'])
            end = True
        else:
            output_speech = 'I did not find anything, try again'
            end = False

        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':end}}
        return response

    elif intent =="RetrieveStarredItems":
        context = request['intent']['slots']['mycontext']['value']
        tasks = remote_session.query(Task).join(Context).filter(and_(Context.title==context, Task.star==True, Task.completed==None, datetime.now()-Task.modified<timedelta(days=30))).all()
        output_speech = ''
        for n,task in enumerate(tasks, start=1):
            output_speech+='{}, {}. '.format(n, task.title)

        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}}
        return response

    else:
        output_speech = "I couldn't tell which type of intent request that was.  Try again."
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}}
        return response
