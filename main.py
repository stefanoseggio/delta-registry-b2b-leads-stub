#!/usr/bin/env python3
"""
actor-18-b2b-lead-magnet-stub

Free, local, one-off puller for OpenStreetMap business listings via the
public Overpass API. Same endpoint and Overpass QL query pattern used by
the "osmOverpass" discovery mode of the paid, hosted actor
stefano_seggio/actor-18-b2b-lead-magnet (https://apify.com/stefano_seggio/actor-18-b2b-lead-magnet).

This script only does discovery: it asks Overpass for businesses inside a
bounding box that have a name and a website (or other contact:* tag), and
saves a small local JSON sample of the raw results.

It does NOT crawl each business's own website, check DNS/MX records, or
run any LLM buying-intent scoring - those enrichment steps only happen in
the paid actor. It also does not schedule itself, track which leads were
already seen in a previous run, retry a failed request, or run on a
recurring basis. See README.md, "What this doesn't do".

Usage:
    python main.py
    python main.py "south,west,north,east"   # your own bounding box
"""

import json
import sys
from datetime import datetime, timezone

import requests

# Same public Overpass API mirror used by this actor's OSM discovery mode.
# Production volume should use a self-hosted Overpass instance - the public
# overpass-api.de mirror is fair-use only.
OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"

# Same Overpass QL template as the actor's OSM discovery mode: any node or
# way carrying a "name" tag AND a "website" tag (shops, offices, craft
# businesses), within a bounding box. "(bbox)" is a literal placeholder
# substituted with the real "south,west,north,east" string before sending.
OVERPASS_QUERY_TEMPLATE = """[out:json][timeout:25];
(
  node["shop"]["name"]["website"](bbox);
  node["office"]["name"]["website"](bbox);
  way["craft"]["name"]["website"](bbox);
);
out center;"""

# Example bounding box covering central Southampton, UK ("south,west,
# north,east" in decimal degrees). Pass your own bbox as the first
# command-line argument - a smaller box returns faster on the public mirror.
DEFAULT_BBOX = "50.90,-1.42,50.92,-1.38"

MAX_RECORDS = 20
OUTPUT_FILE = "sample_leads.json"

# overpass-api.de rejects requests/urllib's default "python-requests/x.x"
# User-Agent with an HTTP 406. Sending a plain, honest, identifying
# User-Agent (not a spoofed browser fingerprint) is enough to pass - and is
# the courteous, documented way to use the public Overpass mirror.
USER_AGENT = "b2b-lead-magnet-stub/1.0 (free sample script; contact: stefanoseggio28@gmail.com)"


def build_query(bbox: str) -> str:
    """Substitute the bounding box into the Overpass QL template."""
    return OVERPASS_QUERY_TEMPLATE.replace("(bbox)", "(" + bbox + ")")


def fetch_elements(bbox: str):
    """POST the query to Overpass and return the raw 'elements' list.

    No retry logic on purpose: a failed request just prints an error and
    the script stops. Retry/backoff is a paid-actor feature.
    """
    query = build_query(bbox)
    try:
        response = requests.post(
            OVERPASS_ENDPOINT,
            data=query.encode("utf-8"),
            headers={"Content-Type": "text/plain", "User-Agent": USER_AGENT},
            timeout=30,
        )
    except requests.exceptions.RequestException as exc:
        print(f"ERROR: request to Overpass API failed: {exc}")
        return []

    if not response.ok:
        print(f"ERROR: Overpass API returned HTTP {response.status_code}: {response.text[:200]}")
        return []

    try:
        payload = response.json()
    except ValueError as exc:
        print(f"ERROR: could not parse Overpass API response as JSON: {exc}")
        return []

    return payload.get("elements", [])


def to_lead_records(elements):
    """Turn raw Overpass elements into a small sample of lead records.

    Field names match this actor's real dataset schema
    (.actor/dataset_schema.json) for the subset this stub actually
    produces: record_id, entity_identifier_native, discoverySource,
    recipient_or_defendant_name, website, category_or_type, jurisdiction,
    scraped_at. Fields the paid actor fills in during enrichment
    (emailsFound, emailPlausible, intentScore, etc.) are not included here
    because this script never computes them.
    """
    records = []
    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"

    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        website = tags.get("website") or tags.get("contact:website")
        has_contact_tag = any(key.startswith("contact:") for key in tags)
        if not website and not has_contact_tag:
            continue

        osm_id = f"{element.get('type')}/{element.get('id')}"
        records.append({
            "record_id": f"osm:{osm_id}",
            "entity_identifier_native": osm_id,
            "recipient_or_defendant_name": name,
            "website": website,
            "discoverySource": "osm",
            "category_or_type": "business_listing_osm",
            "jurisdiction": "OSM",
            "scraped_at": scraped_at,
        })
        if len(records) >= MAX_RECORDS:
            break

    return records


def main():
    bbox = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BBOX
    print(f"Querying Overpass API ({OVERPASS_ENDPOINT}) for businesses in bbox: {bbox}")

    elements = fetch_elements(bbox)
    if not elements:
        print("No elements retrieved (request failed, or zero matches in this bbox). Exiting.")
        return

    records = to_lead_records(elements)
    print(f"Parsed {len(records)} candidate business(es) (sample capped at {MAX_RECORDS}).")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Saved sample to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
