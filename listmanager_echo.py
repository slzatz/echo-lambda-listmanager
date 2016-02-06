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

    elif intent ==  "SetContextOrFolder":
        
        attributes = session['attributes']
        if attributes.get('context'):
            folder = request['intent']['slots']['mycontextorfolder'].get('value', "No Folder")
            d = {'title':attributes.get('title', 'No title'), 'context':attributes['context'], 'folder':folder}
            output_speech = "The item will be placed in folder {}. Do you want it to be starred?".format(folder)
        else:
            context = request['intent']['slots']['mycontextorfolder'].get('value', "No Context")
            d = {'title':attributes.get('title', 'No title'), 'context':context}
            output_speech = "The item will be placed in context {}. What folder do you want to place it in?".format(context)

        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}, 'sessionAttributes':d}
        return response

    elif intent == "AMAZON.YesIntent":
        # ? should use dict.copy()
        title = session['attributes']['title']
        context_title = session['attributes']['context']
        folder_title = session['attributes']['folder']
        #data={'title':title, 'context':context, 'folder':folder, 'star':True}
        #r = requests.post(c.ec_uri+":5000/incoming_from_echo", json=data)
        task = Task(priority=3, title=title, star=True)
        folder = remote_session.query(Folder).filter_by(title=folder_title.lower()).first()
        if folder:
            task.folder = folder
        else:
            folder_title = 'No Folder'
        context = remote_session.query(Context).filter_by(title=context_title.lower()).first()
        if context:
            task.context = context
        else:
            context_title = 'No Context'
        task.startdate = datetime.today().date() 
        task.note = "Created from Echo on {}".format(task.startdate)
        remote_session.add(task)
        remote_session.commit()

        r = requests.get(c.ec_uri+':5000/sync')
        print r.text

        output_speech = "The new item {} will be created for context {} and folder {} and it will be starred".format(title, context_title, folder_title)
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}}
        return response

    elif intent == "AMAZON.NoIntent":
        title = session['attributes']['title']
        context_title = session['attributes']['context']
        folder_title = session['attributes']['folder']
        #data={'title':title, 'context':context, 'folder':folder, 'star':True}
        #r = requests.post(c.ec_uri+":5000/incoming_from_echo", json=data)
        task = Task(priority=3, title=title, star=False)
        folder = remote_session.query(Folder).filter_by(title=folder_title.lower()).first()
        if folder:
            task.folder = folder
        else:
            folder_title = 'No Folder'
        context = remote_session.query(Context).filter_by(title=context_title.lower()).first()
        if context:
            task.context = context
        else:
            context_title = 'No Context'
        task.startdate = datetime.today().date() 
        task.note = "Created from Echo on {}".format(task.startdate)
        remote_session.add(task)
        remote_session.commit()

        r = requests.get(c.ec_uri+':5000/sync')
        print r.text

        output_speech = "The new item {} will be created for context {} and folder {} and it will not be starred".format(title, context_title, folder_title)
        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}}
        return response

    elif intent == "RetrieveFolderItems":
        folder_title = request['intent']['slots']['myfolder'].get('value', '')
        folder_title = folder_title.lower()
        q = remote_session.query(Task).join(Folder).filter(and_(Folder.title==folder_title, Task.completed==None, Task.deleted==False, datetime.now()-Task.modified<timedelta(days=30)))
        count = q.count()
        tasks = q.limit(10).all()

        if count:
            output_speech = "The total number of tasks is {}. ".format(count)
            now = datetime.now()
            for n,task in enumerate(tasks, start=1):
                output_speech+="{}, {}. Created {} days ago.{}".format(n, task.title, (now-task.created).days, ' It is starred. ' if task.star else ' ')
        else:
            output_speech = "I did not find anything."

        response = {'response':{'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}}
        return response

    elif intent == "RetrieveContextItems":
        context_title = request['intent']['slots']['mycontext'].get('value', '')
        context_title = context_title.lower()
        count = remote_session.query(Task).join(Context).filter(and_(Context.title==context_title, Task.completed==None, Task.deleted==False, datetime.now()-Task.modified<timedelta(days=30))).count()
        tasks = remote_session.query(Task).join(Context).filter(and_(Context.title==context_title, Task.completed==None, Task.deleted==False, datetime.now()-Task.modified<timedelta(days=30))).limit(10).all()

        if count:
            output_speech = "The total number of tasks is {}. ".format(count)
            now = datetime.now()
            for n,task in enumerate(tasks, start=1):
                output_speech+="{}, {}. Created {} days ago. It is {} starred. ".format(n, task.title, (now-task.created).days, '' if task.star else 'not')

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
        queryterm = queryterm.replace(' ', '')
        #Initially thought the queryterm could be queryterms and hence the below
        #s = 'title:' + ' AND title:'.join(queryterm.split())
        #s = s + ' note:' + ' AND note:'.join(queryterm.split())
        s = 'title:{} note:{} tag:{}'.format(*(3*(queryterm,)))
        print s
        #fq = ['star:true', 'completed:false']
        fq = ['completed:false']
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
