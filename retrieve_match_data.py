from leaderboard_puuids_retriever import LeaderboardPUUIDsRetriever
from local_api import LockfileHandler
import requests
import json

class RetrieveMatchData:
    def __init__(self):
        self.version_data = "release-12.06-shipping-19-4440219"
        self.match_data = []
        self.modified_header = {}

    def retrieve_matches(self):
        handler = LeaderboardPUUIDsRetriever()
        handler.retrieve_puuids()

        if not handler.puuids:
            print("No players were returned from the leaderboard.")
            return

        local_api_handler = LockfileHandler()
        local_api_handler.lockfile_data_function()

        self.modified_header = dict(local_api_handler.match_id_header)
        self.modified_header["X-Riot-ClientVersion"] = self.version_data
        player_puuid = handler.puuids[0]

        print(f"Headers configured. Retrieving matches for player {player_puuid}...")
        self._retrieve_matches_for_player(player_puuid)

    def _retrieve_matches_for_player(self, puuid):
        history_url = f"https://pd.eu.a.pvp.net/match-history/v1/history/{puuid}?startIndex=0&endIndex=20&queue=competitive"
        history_response = requests.get(history_url, headers=self.modified_header)

        if history_response.status_code != 200:
            print(f"Failed to fetch match history. Status code: {history_response.status_code}")
            return

        history_data = history_response.json()
        match_ids = []

        for match in history_data.get("History", []):
            match_id = match.get("MatchID")
            if match_id and match_id not in match_ids:
                match_ids.append(match_id)

        print(f"Fetching details for {len(match_ids)} matches...")
        self.match_data = []

        for match_id in match_ids:
            match_url = f"https://pd.eu.a.pvp.net/match-details/v1/matches/{match_id}"
            match_response = requests.get(match_url, headers=self.modified_header)

            if match_response.status_code == 200:
                self.match_data.append(match_response.json())
            else:
                print(f"Skipping match {match_id}. Status code: {match_response.status_code}")

        print("Saving data to match_data.json...")
        with open("match_data.json", "w", encoding="utf-8") as f:
            json.dump(self.match_data, f, indent=2)
        print("Done.")
