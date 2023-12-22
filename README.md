# AEGEE G-Suite Directory Sync Toolbox

This repository contains scripts to interact with AEGEE's OMS MyAEGEE and a local G-Suite Directory.

## Requirements

1. Create a Google Cloud project
2. Create a set of OAuth API credentials in the Google Cloud project under https://console.cloud.google.com/apis/credentials
    1. Download the generated credentials into `credentials.json` on the project root directory
3. Initialize the repo dependencies with Poetry
    ```sh
    poetry install
    poetry shell
    ```
4. Run the sync script (the script **does not perform any actions**, only displays the list of users that need to be manually adjusted)
    ```sh
    # Print member users that are not in sync with MyAEGEE
    python gsuitedirsync_aegee/myaegee_sync.py --myaegee-user "username" --myaegee-pass "password" members-sync

    # Print active users that are not in sync with MyAEGEE
    python gsuitedirsync_aegee/myaegee_sync.py --myaegee-user "username" --myaegee-pass "password" actives-sync
    ```
5. Upon first run of the scripts, an authorization URL shall be opened in the browser
    * After the authorization is successfully completed, token file `token.pickle` shall be created in the repository root
    * Subsequent script executions will use the token from this file

## Troubleshooting

### `invalid_grant` error authenticating with Google OAuth

Solution: Remove `token.picke` file.
