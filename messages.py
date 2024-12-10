import time
import mapping
import config

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

import re

import asyncio
import aiohttp

def mapDomain(df):
    for mail in df:
        domain = mail.get('domain')
        if (domain is not None):
            for m in config.g_Labels:
                if (m.get('domain') and m.get('domain').count(domain) > 0):
                    mail['LabeltoAdd'] = m['id']
                    break

    return df

def extractDomain(df):
    for mail in df:
        if (mail.get('Sender')):
            m = re.search(r'.+<.+@(.+..+)>', mail['Sender'])
            if (m is not None):
                mail['domain'] = m.group(1)
            else:
                m = re.search(r'.+@(.+..+)', mail['Sender'])
                if (m is not None):
                    mail['domain'] = m.group(1)
    return df
'''
def getMessages(creds: Credentials):
    df = []

    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=200).execute()
    messages = results.get("messages", [])
    token = results.get("nextPageToken", [])

    if not messages:
      print("No messages found.")
      return


    for m in messages:
        rMessages = service.users().messages().get(userId="me", format="metadata", id=m["id"]).execute()
        #print(rMessages["snippet"])
        data = {}
        a = list(filter(lambda x:x["name"]=="From",rMessages["payload"]["headers"]))
        data['id'] = m['id']
        data['Sender'] = a[0]["value"]
        data['Label'] = rMessages["labelIds"]

        # for i in rMessages["payload"]["headers"]:
        #     if (i["name"] == "From"):
        #         data['id'] = m['id']
        #         data['Sender'] = i["value"]
        #         data['Label'] = rMessages["labelIds"]
        #         break
        #     #elif (i["name"] == "Subject"):
        #         #data['Subject'] = i["value"]
        #         #data['Label'] = rMessages["labelIds"]
        df.append(data)
        
    return df
'''

async def readMessage(m, service):
    rMessages = service.users().messages().get(userId="me", format="metadata", id=m["id"]).execute()

    data = {}
    a = list(filter(lambda x:x["name"]=="From",rMessages["payload"]["headers"]))
    if (len(a) > 0):
        data['id'] = m['id']
        data['Sender'] = a[0]["value"]
        data['Label'] = rMessages["labelIds"]

    return data

async def getMessages2(creds: Credentials):
    df = []

    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=200,  q="", labelIds=["INBOX"]).execute() #q="is:read",
    messages = results.get("messages", [])
    pageToken = results.get("nextPageToken", [])

    if not messages:
      print("No messages found.")
      return

    async with aiohttp.ClientSession() as session:
        tasks = []
        for m in messages:
            tasks.append(asyncio.ensure_future(readMessage(m, service)))

        resps = await asyncio.gather(*tasks)
        #decode response
        for resp in resps:
            if (len(resp) > 0):
                df.append(resp)

    return df

def addLabels(df):
    for mail in df:
        oldLabels = mail['Label']
        addLabel = mail.get('LabeltoAdd')
        #if (pd.isnull(oldLabels)):
        #    continue
        if (addLabel is None):
            continue
        if (oldLabels.count(addLabel) == 0):
            mail['ToBeUpdated'] = True

    return df

def updateMessage(df, creds : Credentials):

    service = build("gmail", "v1", credentials=creds)
    for mail in df:
        if (mail.get('ToBeUpdated')):
            if (mail.get('ToBeUpdated') == True):
                u = {}
                u['addLabelIds'] = mail['LabeltoAdd']
                u['removeLabelIds'] = 'INBOX'
                results = service.users().messages().modify(userId="me", id=mail["id"],body=u).execute()
                messages = results.get("messages", [])
                print(f'Mail with {mail["Sender"]} modified')
        else:
            print(f'Mail with {mail["Sender"]} not modified')
    

async def listMessages(creds: Credentials):

    #get messages
    df =  await getMessages2(creds)

    #get sender
    df = extractDomain(df)
    #get new label
    df = mapDomain(df)
    
    #add the label if need be
    df = addLabels(df)

    #then change message
    updateMessage(df, creds)

