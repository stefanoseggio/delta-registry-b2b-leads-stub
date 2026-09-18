# actor-18-b2b-lead-magnet-stub

This is a free, one-off, local script that pulls a small sample of business listings from OpenStreetMap's public Overpass API - the same endpoint (`https://overpass-api.de/api/interpreter`) and the same Overpass QL query pattern (any `shop`/`office`/`craft` node or way with a `name` tag and a `website` tag, inside a bounding box) used by the OSM discovery mode of the hosted [actor-18-b2b-lead-magnet](https://apify.com/stefano_seggio/actor-18-b2b-lead-magnet) on Apify. Run it once, get up to 20 real business records as local JSON. It does the discovery step only - no website crawling, no email verification, no scheduling - so you can see exactly what OSM-based lead discovery looks like before deciding whether the hosted, enriched version is worth paying for.

## Setup & run

```bash
pip install -r requirements.txt
python main.py
```

By default it queries a bounding box over central Southampton, UK (`50.90,-1.42,50.92,-1.38`). To query your own area, pass a `"south,west,north,east"` bounding box in decimal degrees as the first argument:

```bash
python main.py "50.70,-1.90,50.90,-1.30"
```

Output is written to `sample_leads.json` in the current directory, capped at 20 records.

## Example output

This is real output from an actual run against `overpass-api.de` (trimmed to one record; a full run writes up to 20):

```json
[
  {
    "record_id": "osm:node/694824593",
    "entity_identifier_native": "node/694824593",
    "recipient_or_defendant_name": "Jamie's Computers",
    "website": "https://jamies.org.uk",
    "discoverySource": "osm",
    "category_or_type": "business_listing_osm",
    "jurisdiction": "OSM",
    "scraped_at": "2026-09-10T15:02:58.060Z"
  }
]
```

The field names (`record_id`, `entity_identifier_native`, `recipient_or_defendant_name`, `website`, `discoverySource`, `category_or_type`, `jurisdiction`) match the hosted actor's real `.actor/dataset_schema.json` - this script only ever populates the subset of that schema that raw OSM discovery can honestly fill in.

## What this doesn't do

This is intentionally the simple half of the funnel. Compared to the hosted actor, this stub does **not**:

- **Enrich a lead.** No website crawl, no DNS/MX email-plausibility check, no `emailsFound`, no `emailPlausible`, and no `intentScore` (the hosted actor's optional Claude Haiku 4.5 buying-intent read). This script stops at the raw OSM record.
- **Retry a failed request.** If the Overpass API call fails or times out, this script prints the error and exits. The hosted actor wraps every outbound call in a shared retry helper with exponential backoff (each retry's delay doubles from a 500ms base) on network errors, HTTP 429, and 5xx responses.
- **Track leads across runs.** Every run of this script is independent - run it twice against the same bounding box and you'll get the same businesses again. The hosted actor persists a seen/not-seen record for every lead it has ever discovered in a named key-value store, so a `skipKnownLeads` run only pays for and re-processes businesses it hasn't seen before.
- **Run on a schedule.** This is a script you run by hand. The hosted actor runs on Apify's platform, so it can be put on a recurring schedule (e.g. weekly territory re-scans) without you keeping a machine or cron job running.

For scheduled runs, cross-run lead tracking, and pay-per-event pricing with reliability built in, see the production actor: https://apify.com/stefano_seggio/actor-18-b2b-lead-magnet

This stub is part of the [Delta Registry](https://delta-registry-website.vercel.app) actor fleet.

## License

MIT - see [LICENSE](./LICENSE).
