import json
import os

def global_setup():
    with open('./config.json') as config_file:
        cfg = json.load(config_file)

    os.environ['E2E_APP_URL'] = cfg['E2E_APP_URL']
    os.environ['E2E_USER'] = cfg['E2E_USER']
    os.environ['E2E_PASSWORD'] = cfg['E2E_PASSWORD']
    os.environ['E2E_UNIQUE_CONTEXT'] = cfg['E2E_UNIQUE_CONTEXT']

if __name__ == "__main__":
    global_setup()
