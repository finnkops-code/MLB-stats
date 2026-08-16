"""
MLB Speler-statistieken Scraper — hitting + pitching van alle spelers, één JSON.

Gebruikt de officiële MLB Stats API (statsapi.mlb.com), dezelfde bron als
mlb.com/stats zelf. Geen browser-scraping nodig: de statistieken komen
gepagineerd binnen (playerPool=all) en worden hier tot één volledige lijst
samengevoegd, per groep (hitting/pitching).
"""
import json
import urllib.request
import datetime as dt
from datetime import timezone

STATS_API = (
    "https://statsapi.mlb.com/api/v1/stats"
    "?stats=season&group={groep}&sportId=1&season={seizoen}"
    "&playerPool=all&limit={limiet}&offset={offset}"
)
JSON_FILE = "mlb_stats.json"
PAGINA_GROOTTE = 100


def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def logo_url(team_id):
    if not team_id:
        return None
    return f"https://www.mlbstatic.com/team-logos/{team_id}.svg"


def fetch_alle_splits(groep, seizoen):
    """Haalt alle spelers voor een stat-groep (hitting/pitching) op, gepagineerd."""
    alle_splits = []
    offset = 0
    totaal = None
    while totaal is None or offset < totaal:
        url = STATS_API.format(groep=groep, seizoen=seizoen, limiet=PAGINA_GROOTTE, offset=offset)
        data = fetch_json(url)
        stats_blokken = data.get("stats", [])
        if not stats_blokken:
            break
        blok = stats_blokken[0]
        if totaal is None:
            totaal = blok.get("totalSplits", 0)
            print(f"  {groep}: {totaal} spelers in totaal")
        splits = blok.get("splits", [])
        if not splits:
            break
        alle_splits.extend(splits)
        offset += PAGINA_GROOTTE
    return alle_splits


def bouw_hitting_rij(split):
    speler = split.get("player", {})
    team = split.get("team", {})
    stat = split.get("stat", {})
    team_id = team.get("id")
    return {
        "speler_id":  speler.get("id"),
        "speler":     speler.get("fullName", "-"),
        "team_id":    team_id,
        "team":       team.get("name", "-"),
        "team_logo":  logo_url(team_id),
        "g":          stat.get("gamesPlayed"),
        "ab":         stat.get("atBats"),
        "r":          stat.get("runs"),
        "h":          stat.get("hits"),
        "doubles":    stat.get("doubles"),
        "triples":    stat.get("triples"),
        "hr":         stat.get("homeRuns"),
        "rbi":        stat.get("rbi"),
        "bb":         stat.get("baseOnBalls"),
        "so":         stat.get("strikeOuts"),
        "sb":         stat.get("stolenBases"),
        "avg":        stat.get("avg"),
        "obp":        stat.get("obp"),
        "slg":        stat.get("slg"),
        "ops":        stat.get("ops"),
    }


def bouw_pitching_rij(split):
    speler = split.get("player", {})
    team = split.get("team", {})
    stat = split.get("stat", {})
    team_id = team.get("id")
    return {
        "speler_id": speler.get("id"),
        "speler":    speler.get("fullName", "-"),
        "team_id":   team_id,
        "team":      team.get("name", "-"),
        "team_logo": logo_url(team_id),
        "w":         stat.get("wins"),
        "l":         stat.get("losses"),
        "era":       stat.get("era"),
        "g":         stat.get("gamesPitched"),
        "gs":        stat.get("gamesStarted"),
        "sv":        stat.get("saves"),
        "ip":        stat.get("inningsPitched"),
        "h":         stat.get("hits"),
        "r":         stat.get("runs"),
        "er":        stat.get("earnedRuns"),
        "hr":        stat.get("homeRuns"),
        "bb":        stat.get("baseOnBalls"),
        "so":        stat.get("strikeOuts"),
        "whip":      stat.get("whip"),
    }


def main():
    seizoen = dt.datetime.now(timezone.utc).year
    print(f"Seizoen: {seizoen}")

    print("\nHitting-statistieken ophalen...")
    hitting_splits = fetch_alle_splits("hitting", seizoen)
    hitting = [bouw_hitting_rij(s) for s in hitting_splits]
    hitting.sort(key=lambda r: (r["team"] or "", r["speler"] or ""))
    print(f"→ {len(hitting)} hitters")

    print("\nPitching-statistieken ophalen...")
    pitching_splits = fetch_alle_splits("pitching", seizoen)
    pitching = [bouw_pitching_rij(s) for s in pitching_splits]
    pitching.sort(key=lambda r: (r["team"] or "", r["speler"] or ""))
    print(f"→ {len(pitching)} pitchers")

    output = {
        "bijgewerkt": dt.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seizoen":    seizoen,
        "hitting":    hitting,
        "pitching":   pitching,
    }
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n{JSON_FILE}: {len(hitting)} hitters, {len(pitching)} pitchers")


if __name__ == "__main__":
    main()
