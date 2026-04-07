import os
import json
import requests
import pathlib
import base64
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LockfileHandler:
    def __init__(self):
        self.access_token = []
        self.entitlement_token = []
        self.puuid = []
        self.client_version = []
        self.match_id_header = {}

    def lockfile_data_function(self):
        # Finds Lockfile
        lockfile_loc = rf"{os.getenv('LOCALAPPDATA')}\Riot Games\Riot Client\Config\lockfile"
        if os.path.exists(Path(rf'{lockfile_loc}')):
            lockfile_path = Path(rf'{lockfile_loc}')

            # Reads Lockfile
            lockfile_read = open(lockfile_path, "r")
            lockfile_data = lockfile_read.read()
            lockfile_read.close()

            # Finds and defines port and password from lockfile
            lockfile_data_colon_loc = [i for i, x in enumerate(lockfile_data) if x == ":"]
            port = lockfile_data[lockfile_data_colon_loc[1] + 1:lockfile_data_colon_loc[2]]
            password = lockfile_data[lockfile_data_colon_loc[2] + 1:lockfile_data_colon_loc[3]]

            # Retrieves user's access and entitlement tokens
            tokens_response = requests.get(
                f"https://127.0.0.1:{port}/entitlements/v1/token",
                auth=("riot", password),
                verify=False
            )

            # Retrives user's client version
            session_response = requests.get(
                f"https://127.0.0.1:{port}/product-session/v1/external-sessions",
                auth=("riot", password),
                verify=False
            )

            entitlements = tokens_response.json()
            self.access_token = entitlements["accessToken"]
            self.entitlement_token = entitlements["token"]
            self.puuid = entitlements["subject"]

            session = session_response.json()
            self.client_version = session["host_app"]["version"]

            self.match_id_header = {
                "X-Riot-ClientPlatform": "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9",
                "X-Riot-ClientVersion": f"{self.client_version}",
                "X-Riot-Entitlements-JWT": f"{self.entitlement_token}",
                "Authorization": f"Bearer {self.access_token}"
            }
        else:
            print("error")
