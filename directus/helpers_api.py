import os, sys, yaml, requests, json, pathlib

file = open(str(pathlib.Path( __file__ ).parent.absolute()) + "/secret.yaml")
secret = yaml.full_load(file)
file.close()
def get_access_token(): 
    query =f"""mutation {{
        auth_login(email: "{secret["email"]}", password: "{secret["password"]}") {{
            access_token
            refresh_token
        }}
    }}"""
    r = requests.post(secret["url"] + 'system', json={'query': query})
    return r.json()['data']['auth_login']['access_token']

def graphql_query(query):
    r = requests.post(secret["url"] + '?access_token=' + get_access_token(), json={'query': query})
    return json.loads(r.text)
