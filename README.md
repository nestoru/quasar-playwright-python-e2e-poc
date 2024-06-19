# Portal E2E (portal-e2e)
The Portal E2E project tests the portal-ui project and through it all endpoints of the portal-api project.
```
portal-e2e/
├── README.md
├── config.json
├── global_setup.py
├── reporter.py
├── resources
│   └── e2e.png
└── tests
    └── test_authentication_and_authorization.py
```

- config.json is not committed to git but its structure is below
```
{
    "E2E_APP_URL": "http://localhost:9000",
    "E2E_USER": "<admin user here>",
    "E2E_PASSWORD": "<password here>",
    "E2E_UNIQUE_CONTEXT": "<initials here>",
    "E2E_LOG_FILE": "/tmp/e2e-log.txt"
}
```
- global-setup.py extracts config.json definitions and create environment variables with them
- reporter.py is a custom reporter that compiles in a json file in the test-results directory the result of the run, screenshot if fails, video if fails etc.
- resources/ is a directory to add any assets a test needs like it is the case of files to upload.
- tests/ is a directory that contains the tests which should be named starting with the scenario name and with ".spec.ts" as extension.
 
# Preconditions
```
pip install playwright pytest
playwright install
```

# Run tests
```
pytest
```

# share content of the project
```
tree --gitignore
find ./ -type f -name "*" -not -path '*__pycache__*' -not -path '*test-results*' -not -path '*resources*' -not -path '*.git*' -not -path '*.gitignore*' -exec sh -c 'echo "File: {}"; cat {}' \;
```
