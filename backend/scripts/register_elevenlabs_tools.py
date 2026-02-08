from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main() -> None:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    base_url = (os.environ.get("AGENT_TOOLS_BASE_URL") or "").rstrip("/")
    if not api_key:
        print("Set ELEVENLABS_API_KEY")
        sys.exit(1)
    if not base_url:
        print("Set AGENT_TOOLS_BASE_URL (e.g. https://abc123.ngrok.io) so ElevenLabs can reach your webhooks")
        sys.exit(1)

    import httpx

    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    tools = [
        {
            "tool_config": {
                "type": "webhook",
                "name": "get_place_rating",
                "description": "Get rating data for a provider or Google Place. Use when the user asks about ratings, reviews, or quality of a dental office. Provide provider_id (from our registry) or place_id (Google Place ID) for live rating from Google Places.",
                "api_schema": {
                    "url": f"{base_url}/api/v1/agent-tools/rating",
                    "method": "POST",
                    "request_body_schema": {
                        "type": "object",
                        "properties": {
                            "provider_id": {"type": "string", "description": "Provider ID from our registry (e.g. dentist-001)"},
                            "place_id": {"type": "string", "description": "Google Place ID for Places API rating"},
                        },
                        "required": [],
                    },
                },
            },
        },
        {
            "tool_config": {
                "type": "webhook",
                "name": "get_travel_distance",
                "description": "Get travel distance and duration to a provider (Google Maps Distance Matrix). Use when the user cares about distance or travel time. Provide provider_id and optionally origin (user address or lat,lng) for real driving distance.",
                "api_schema": {
                    "url": f"{base_url}/api/v1/agent-tools/distance",
                    "method": "POST",
                    "request_body_schema": {
                        "type": "object",
                        "properties": {
                            "provider_id": {"type": "string", "description": "Provider ID"},
                            "origin": {"type": "string", "description": "User origin address or lat,lng for Distance Matrix"},
                        },
                        "required": ["provider_id"],
                    },
                },
            },
        },
        {
            "tool_config": {
                "type": "webhook",
                "name": "get_availability",
                "description": "Get available time slots from Google Calendar. Use when the user asks when they are free or what times are available. Returns list of free slots.",
                "api_schema": {
                    "url": f"{base_url}/api/v1/agent-tools/availability",
                    "method": "POST",
                    "request_body_schema": {
                        "type": "object",
                        "properties": {
                            "time_min_iso": {"type": "string", "description": "Start of window (ISO datetime)"},
                            "time_max_iso": {"type": "string", "description": "End of window (ISO datetime)"},
                            "duration_minutes": {"type": "integer", "description": "Slot duration in minutes", "default": 30},
                        },
                        "required": [],
                    },
                },
            },
        },
        {
            "tool_config": {
                "type": "webhook",
                "name": "get_user_weighting",
                "description": "Get the user's preference weights for ranking: availability vs rating vs distance. Use when you need to rank or compare options (e.g. availability_weight, rating_weight, distance_weight).",
                "api_schema": {
                    "url": f"{base_url}/api/v1/agent-tools/user-weighting",
                    "method": "POST",
                    "request_body_schema": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
        },
    ]

    created = []
    for t in tools:
        try:
            r = httpx.post(
                "https://api.elevenlabs.io/v1/convai/tools",
                headers=headers,
                json=t,
                timeout=15.0,
            )
            if r.status_code == 200:
                data = r.json()
                tool_id = data.get("id", "?")
                created.append((t["tool_config"]["name"], tool_id))
                print(f"Created tool: {t['tool_config']['name']} -> id {tool_id}")
            else:
                print(f"Failed {t['tool_config']['name']}: {r.status_code} {r.text[:200]}")
        except Exception as e:
            print(f"Error {t['tool_config']['name']}: {e}")

    if created:
        print(f"\nRegistered {len(created)} tools. Attach these tools to your agent in the ElevenLabs dashboard (Conversational AI -> your agent -> Tools).")
    else:
        print("No tools were created. Check API key and base URL.")
        sys.exit(1)


if __name__ == "__main__":
    main()
