import mapping
import config

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def listLabel(creds: Credentials):
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().labels().list(userId="me").execute()
    config.g_Labels = results.get("labels", [])

    if not config.g_Labels:
        print("No labels found.")
        return
    #print(labels)

    d = {}
    for i in mapping.mapping:
        d[i['label']] = i['domain']

    for i in config.g_Labels:
        domain = i['name']
        if (d.get(domain)):
            i['domain'] = d[domain]
