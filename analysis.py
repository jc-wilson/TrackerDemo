import json

with open("puuid_data.json") as a:
    puuid = json.load(a)

puuid = puuid[0]

with open("match_data.json") as b:
    matches = json.load(b)

with open("weapon_uuids.json") as c:
    weapon_uuids = json.load(c)

def normalise_weapon_uuids(uuid):
    for weapon in weapon_uuids["data"]:
        if weapon["uuid"] == uuid:
            return weapon["displayName"]
    return None

ttr = {
    0: "Unranked",
    3: "Iron 1",
    4: "Iron 2",
    5: "Iron 3",
    6: "Bronze 1",
    7: "Bronze 2",
    8: "Bronze 3",
    9: "Silver 1",
    10: "Silver 2",
    11: "Silver 3",
    12: "Gold 1",
    13: "Gold 2",
    14: "Gold 3",
    15: "Platinum 1",
    16: "Platinum 2",
    17: "Platinum 3",
    18: "Diamond 1",
    19: "Diamond 2",
    20: "Diamond 3",
    21: "Ascendant 1",
    22: "Ascendant 2",
    23: "Ascendant 3",
    24: "Immortal 1",
    25: "Immortal 2",
    26: "Immortal 3",
    27: "Radiant"
}

def safe_division(numerator, denominator, decimals=1, default=0):
    if denominator == 0:
        return default
    return round(int(numerator) / int(denominator), decimals)

player_info = {
    "name": None,
    "tag": None,
    "rank": None,
    "level": None
}

for player in matches[0]["players"]:
    if player["subject"] == puuid:
        player_info["name"] = player["gameName"]
        player_info["tag"] = player["tagLine"]
        player_info["rank"] = ttr[player["competitiveTier"]]
        player_info["level"] = player["accountLevel"]

won_stats_raw = {
    "games": 0,
    "playtimeMillis": 0,
    "rounds": 0,
    "kills": 0,
    "deaths": 0,
    "assists": 0,
    "ACS": 0,
    "ADR": 0,
    "legshots": 0,
    "bodyshots": 0,
    "headshots": 0,
    "legshots_received": 0,
    "bodyshots_received": 0,
    "headshots_received": 0,
    "first_bloods": 0,
    "first_deaths": 0,
    "KAST": 0
}
lost_stats_raw = {
    "games": 0,
    "playtimeMillis": 0,
    "rounds": 0,
    "kills": 0,
    "deaths": 0,
    "assists": 0,
    "ACS": 0,
    "ADR": 0,
    "legshots": 0,
    "bodyshots": 0,
    "headshots": 0,
    "legshots_received": 0,
    "bodyshots_received": 0,
    "headshots_received": 0,
    "first_bloods": 0,
    "first_deaths": 0,
    "KAST": 0
}
stats_raw = {
    "games": 0,
    "playtimeMillis": 0,
    "rounds": 0,
    "kills": 0,
    "deaths": 0,
    "assists": 0,
    "ACS": 0,
    "ADR": 0,
    "legshots": 0,
    "bodyshots": 0,
    "headshots": 0,
    "legshots_received": 0,
    "bodyshots_received": 0,
    "headshots_received": 0,
    "first_bloods": 0,
    "first_deaths": 0,
    "KAST": 0
}

won_rounds_stats_raw = {
    "rounds": 0,
    "kills": 0,
    "deaths": 0,
    "assists": 0,
    "ACS": 0,
    "ADR": 0,
    "legshots": 0,
    "bodyshots": 0,
    "headshots": 0,
    "legshots_received": 0,
    "bodyshots_received": 0,
    "headshots_received": 0,
    "first_bloods": 0,
    "first_deaths": 0,
    "KAST": 0
}
lost_rounds_stats_raw = {
    "rounds": 0,
    "kills": 0,
    "deaths": 0,
    "assists": 0,
    "ACS": 0,
    "ADR": 0,
    "legshots": 0,
    "bodyshots": 0,
    "headshots": 0,
    "legshots_received": 0,
    "bodyshots_received": 0,
    "headshots_received": 0,
    "first_bloods": 0,
    "first_deaths": 0,
    "KAST": 0
}

won_stats = {}
lost_stats = {}
stats = {}
won_rounds_stats = {}
lost_rounds_stats = {}

for match in matches:
    teammates = []
    for player in match["players"]:
        if player["subject"] == puuid:
            team = player["teamId"]
    for player in match["players"]:
        if player["teamId"] == team:
            teammates.append(player["subject"])
    for teams in match["teams"]:
        if teams["teamId"] == team:
            won = teams["won"]

    target_stats = won_stats_raw if won else lost_stats_raw
    for player in match["players"]:
        if player["subject"] == puuid:
            target_stats["games"] += 1
            target_stats["playtimeMillis"] += player["stats"]["playtimeMillis"]
            target_stats["rounds"] += player["stats"]["roundsPlayed"]
            target_stats["kills"] += player["stats"]["kills"]
            target_stats["deaths"] += player["stats"]["deaths"]
            target_stats["assists"] += player["stats"]["assists"]
            target_stats["ACS"] += player["stats"]["score"]
            for round1 in player["roundDamage"]:
                if round1["damage"] == 999:
                    continue
                if round1["receiver"] in teammates:
                    continue
                target_stats["ADR"] += round1["damage"]
    for round1 in match["roundResults"]:
        if round1["roundResult"] == "Surrendered":
            continue
        else:
            if round1["firstBloodPlayer"] == puuid:
                target_stats["first_bloods"] += 1

            for player in round1["playerStats"]:
                if player["subject"] == round1["firstBloodPlayer"]:
                    if player["kills"][0]["victim"] == puuid:
                        target_stats["first_deaths"] += 1
                if player["subject"] == puuid:
                    if player["damage"]:
                        for damage in player["damage"]:
                            target_stats["legshots"] += damage["legshots"]
                            target_stats["bodyshots"] += damage["bodyshots"]
                            target_stats["headshots"] += damage["headshots"]
                else:
                    if player["damage"]:
                        for damage in player["damage"]:
                            if damage["receiver"] == puuid:
                                target_stats["legshots_received"] += damage["legshots"]
                                target_stats["bodyshots_received"] += damage["bodyshots"]
                                target_stats["headshots_received"] += damage["headshots"]

    for round1 in match["roundResults"]:
        if round1["roundResult"] == "Surrendered":
            continue
        else:
            kast_points = 0
            user_deaths = 0
            death_list = []

            target_round_stats = won_rounds_stats_raw if round1["winningTeam"] == team else lost_rounds_stats_raw
            target_round_stats["rounds"] += 1
            if round1["firstBloodPlayer"] == puuid:
                target_round_stats["first_bloods"] += 1
            for player in round1["playerStats"]:
                if player["subject"] == round1["firstBloodPlayer"]:
                    if player["kills"][0]["victim"] == puuid:
                        target_round_stats["first_deaths"] += 1
                if player["subject"] == puuid:
                    if player["kills"]:
                        target_round_stats["kills"] += len(player["kills"])
                        kast_points += 1
                    if player["damage"]:
                        for damage in player["damage"]:
                            if damage["damage"] == 999:
                                continue
                            if damage["receiver"] in teammates:
                                continue
                            target_round_stats["ADR"] += damage["damage"]
                            target_round_stats["legshots"] += damage["legshots"]
                            target_round_stats["bodyshots"] += damage["bodyshots"]
                            target_round_stats["headshots"] += damage["headshots"]
                    if player["score"]:
                        target_round_stats["ACS"] += player["score"]
                if player["kills"]:
                    for kill in player["kills"]:
                        if kill["victim"] == puuid:
                            target_round_stats["deaths"] += 1
                            user_deaths += 1
                            death_list.append({
                                "death_time": kill["gameTime"],
                                "killer": kill["killer"]
                            })
                        if puuid in kill["assistants"]:
                            target_round_stats["assists"] += 1
                            kast_points += 1
                if player["damage"]:
                    for damage in player["damage"]:
                        if damage["receiver"] == puuid:
                            target_round_stats["legshots_received"] += damage["legshots"]
                            target_round_stats["bodyshots_received"] += damage["bodyshots"]
                            target_round_stats["headshots_received"] += damage["headshots"]
            if not user_deaths:
                kast_points += 1
            else:
                for player in round1["playerStats"]:
                    if player["kills"]:
                        for kill in player["kills"]:
                            for death in death_list:
                                if kill["victim"] == death["killer"] and 0 < kill["gameTime"] - death["death_time"] < 5000:
                                    kast_points += 1
            if kast_points:
                target_round_stats["KAST"] += 1
                target_stats["KAST"] += 1

for stat in stats_raw.keys():
    stats_raw[stat] = (int(won_stats_raw[stat]) + int(lost_stats_raw[stat]))

print(won_rounds_stats_raw)
print(lost_rounds_stats_raw)

won_stats["Games Played"] = won_stats_raw["games"]
lost_stats["Games Played"] = lost_stats_raw["games"]
stats["Games Played"] = stats_raw["games"]

won_stats["Playtime"] = f"{safe_division(int(won_stats_raw['playtimeMillis']), 1000 * 60 * 60, 1)}h"
lost_stats["Playtime"] = f"{safe_division(int(lost_stats_raw['playtimeMillis']), 1000 * 60 * 60, 1)}h"
stats["Playtime"] = f"{safe_division(int(stats_raw['playtimeMillis']), 1000 * 60 * 60, 1)}h"

won_stats["ADR"] = safe_division(int(won_stats_raw["ADR"]), int(won_stats_raw["rounds"]), 1)
lost_stats["ADR"] = safe_division(int(lost_stats_raw["ADR"]), int(lost_stats_raw["rounds"]), 1)
stats["ADR"] = safe_division(int(stats_raw["ADR"]), int(stats_raw["rounds"]), 1)

won_stats["ACS"] = safe_division(int(won_stats_raw["ACS"]), int(won_stats_raw["rounds"]), 1)
lost_stats["ACS"] = safe_division(int(lost_stats_raw["ACS"]), int(lost_stats_raw["rounds"]), 1)
stats["ACS"] = safe_division(int(stats_raw["ACS"]), int(stats_raw["rounds"]), 1)

won_stats["K/D"] = safe_division(int(won_stats_raw["kills"]), int(won_stats_raw["deaths"]), 2)
lost_stats["K/D"] = safe_division(int(lost_stats_raw["kills"]), int(lost_stats_raw["deaths"]), 2)
stats["K/D"] = safe_division(int(stats_raw["kills"]), int(stats_raw["deaths"]), 2)

won_stats["K/R"] = safe_division(int(won_stats_raw["kills"]), int(won_stats_raw["rounds"]), 2)
lost_stats["K/R"] = safe_division(int(lost_stats_raw["kills"]), int(lost_stats_raw["rounds"]), 2)
stats["K/R"] = safe_division(int(stats_raw["kills"]), int(stats_raw["rounds"]), 2)

won_stats["Entry Success Rate %"] = safe_division(
    int(won_stats_raw["first_bloods"]) * 100,
    int(won_stats_raw["first_bloods"]) + int(won_stats_raw["first_deaths"]),
    1,
)
lost_stats["Entry Success Rate %"] = safe_division(
    int(lost_stats_raw["first_bloods"]) * 100,
    int(lost_stats_raw["first_bloods"]) + int(lost_stats_raw["first_deaths"]),
    1,
)
stats["Entry Success Rate %"] = safe_division(
    int(stats_raw["first_bloods"]) * 100,
    int(stats_raw["first_bloods"]) + int(stats_raw["first_deaths"]),
    1,
)

won_stats["Entry Attempt Rate %"] = safe_division(
    (int(won_stats_raw["first_bloods"]) + int(won_stats_raw["first_deaths"])) * 100,
    int(won_stats_raw["rounds"]),
    1
)

lost_stats["Entry Attempt Rate %"] = safe_division(
    (int(lost_stats_raw["first_bloods"]) + int(lost_stats_raw["first_deaths"])) * 100,
    int(lost_stats_raw["rounds"]),
    1
)

stats["Entry Attempt Rate %"] = safe_division(
    (int(stats_raw["first_bloods"]) + int(stats_raw["first_deaths"])) * 100,
    int(stats_raw["rounds"]),
    1
)

won_stats["HS %"] = safe_division(
    int(won_stats_raw["headshots"]) * 100,
    int(won_stats_raw["legshots"]) + int(won_stats_raw["bodyshots"]) + int(won_stats_raw["headshots"]),
    1,
)
lost_stats["HS %"] = safe_division(
    int(lost_stats_raw["headshots"]) * 100,
    int(lost_stats_raw["legshots"]) + int(lost_stats_raw["bodyshots"]) + int(lost_stats_raw["headshots"]),
    1,
)
stats["HS %"] = safe_division(
    int(stats_raw["headshots"]) * 100,
    int(stats_raw["legshots"]) + int(stats_raw["bodyshots"]) + int(stats_raw["headshots"]),
    1,
)

won_stats["HS % Received"] = safe_division(
    int(won_stats_raw["headshots_received"]) * 100,
    int(won_stats_raw["legshots_received"]) + int(won_stats_raw["bodyshots_received"]) + int(won_stats_raw["headshots_received"]),
    1,
)
lost_stats["HS % Received"] = safe_division(
    int(lost_stats_raw["headshots_received"]) * 100,
    int(lost_stats_raw["legshots_received"]) + int(lost_stats_raw["bodyshots_received"]) + int(lost_stats_raw["headshots_received"]),
    1,
)
stats["HS % Received"] = safe_division(
    int(stats_raw["headshots_received"]) * 100,
    int(stats_raw["legshots_received"]) + int(stats_raw["bodyshots_received"]) + int(stats_raw["headshots_received"]),
    1,
)

won_stats["KAST %"] = safe_division(
    int(won_stats_raw["KAST"]) * 100,
    int(won_stats_raw["rounds"]),
    1
)

lost_stats["KAST %"] = safe_division(
    int(lost_stats_raw["KAST"]) * 100,
    int(lost_stats_raw["rounds"]),
    1
)

stats["KAST %"] = safe_division(
    int(stats_raw["KAST"]) * 100,
    int(stats_raw["rounds"]),
    1
)

won_rounds_stats["ADR"] = safe_division(int(won_rounds_stats_raw["ADR"]), int(won_rounds_stats_raw["rounds"]), 1)
lost_rounds_stats["ADR"] = safe_division(int(lost_rounds_stats_raw["ADR"]), int(lost_rounds_stats_raw["rounds"]), 1)

won_rounds_stats["ACS"] = safe_division(int(won_rounds_stats_raw["ACS"]), int(won_rounds_stats_raw["rounds"]), 1)
lost_rounds_stats["ACS"] = safe_division(int(lost_rounds_stats_raw["ACS"]), int(lost_rounds_stats_raw["rounds"]), 1)

won_rounds_stats["K/D"] = safe_division(int(won_rounds_stats_raw["kills"]), int(won_rounds_stats_raw["deaths"]), 2)
lost_rounds_stats["K/D"] = safe_division(int(lost_rounds_stats_raw["kills"]), int(lost_rounds_stats_raw["deaths"]), 2)

won_rounds_stats["K/R"] = safe_division(int(won_rounds_stats_raw["kills"]), int(won_rounds_stats_raw["rounds"]), 2)
lost_rounds_stats["K/R"] = safe_division(int(lost_rounds_stats_raw["kills"]), int(lost_rounds_stats_raw["rounds"]), 2)

won_rounds_stats["Entry Success Rate %"] = safe_division(
    int(won_rounds_stats_raw["first_bloods"]) * 100,
    int(won_rounds_stats_raw["first_bloods"]) + int(won_rounds_stats_raw["first_deaths"]),
    1,
)
lost_rounds_stats["Entry Success Rate %"] = safe_division(
    int(lost_rounds_stats_raw["first_bloods"]) * 100,
    int(lost_rounds_stats_raw["first_bloods"]) + int(lost_rounds_stats_raw["first_deaths"]),
    1,
)

won_rounds_stats["Entry Attempt Rate %"] = safe_division(
    (int(won_rounds_stats_raw["first_bloods"]) + int(won_rounds_stats_raw["first_deaths"])) * 100,
    int(won_rounds_stats_raw["rounds"]),
    1
)

lost_rounds_stats["Entry Attempt Rate %"] = safe_division(
    (int(lost_rounds_stats_raw["first_bloods"]) + int(lost_rounds_stats_raw["first_deaths"])) * 100,
    int(lost_rounds_stats_raw["rounds"]),
    1
)

won_rounds_stats["HS %"] = safe_division(
    int(won_rounds_stats_raw["headshots"]) * 100,
    int(won_rounds_stats_raw["legshots"]) + int(won_rounds_stats_raw["bodyshots"]) + int(won_rounds_stats_raw["headshots"]),
    1,
)
lost_rounds_stats["HS %"] = safe_division(
    int(lost_rounds_stats_raw["headshots"]) * 100,
    int(lost_rounds_stats_raw["legshots"]) + int(lost_rounds_stats_raw["bodyshots"]) + int(lost_rounds_stats_raw["headshots"]),
    1,
)

won_rounds_stats["HS % Received"] = safe_division(
    int(won_rounds_stats_raw["headshots_received"]) * 100,
    int(won_rounds_stats_raw["legshots_received"]) + int(won_rounds_stats_raw["bodyshots_received"]) + int(won_rounds_stats_raw["headshots_received"]),
    1,
)
lost_rounds_stats["HS % Received"] = safe_division(
    int(lost_rounds_stats_raw["headshots_received"]) * 100,
    int(lost_rounds_stats_raw["legshots_received"]) + int(lost_rounds_stats_raw["bodyshots_received"]) + int(lost_rounds_stats_raw["headshots_received"]),
    1,
)

won_rounds_stats["KAST %"] = safe_division(
    int(won_rounds_stats_raw["KAST"]) * 100,
    int(won_rounds_stats_raw["rounds"]),
    1
)

lost_rounds_stats["KAST %"] = safe_division(
    int(lost_rounds_stats_raw["KAST"]) * 100,
    int(lost_rounds_stats_raw["rounds"]),
    1
)


print(f"player info: {player_info}")
print(f"Stats in all games: {stats}")
print(f"Stats in games won: {won_stats}")
print(f"Stats in games lost: {lost_stats}")
print(f"Stats in rounds won: {won_rounds_stats}")
print(f"Stats in rounds lost: {lost_rounds_stats}")
