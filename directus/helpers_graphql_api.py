import os
import sys
import json
import requests
import pathlib
from pprint import pprint
import yaml


def get_access_token(secret):
    query = f"""mutation {{
      auth_login(email: "{secret["email"]}", password: "{secret["password"]}") {{
        access_token
        refresh_token
      }}
    }}"""
    r = requests.post(secret["url"] + '/graphql/system', json={'query': query})
    return r.json()['data']['auth_login']['access_token']


def graphql_query(query, secret):
    r = requests.post(secret["url"] + '/graphql/?access_token=' +
                      get_access_token(secret), json={'query': query})
    return json.loads(r.text)
