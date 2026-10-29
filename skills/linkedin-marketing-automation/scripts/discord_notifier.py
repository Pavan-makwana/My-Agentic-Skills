"""Discord Rich Embed Webhook Notifier for LinkedIn Automation Review Co-Pilot."""

import os
import json
import requests
from pathlib import Path


class DiscordNotifier:
    """Delivers scheduled post previews, graphic cards, and validation audits to Discord."""

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    def send_preview(
        self,
        topic: str,
        pillar: str,
        copy: str,
        hook: str,
        image_path: Path | str,
        scheduled_time: str = "8:30 PM IST",
        target_focus: str = "B2B SaaS"
    ) -> bool:
        """Sends a rich preview of the scheduled LinkedIn post with image attachment to Discord."""
        if not self.webhook_url:
            print("[Discord] DISCORD_WEBHOOK_URL is not configured. Skipping Discord preview.")
            return False

        path = Path(image_path)
        if not path.exists():
            print(f"[Discord] Image file {path} not found.")
            return False

        # Truncate copy if it exceeds Discord embed description limit (4096 chars)
        display_copy = copy if len(copy) <= 3800 else copy[:3800] + "\n\n...[truncated]"

        payload = {
            "content": (
                f"**🔔 [Preview & Gating] Upcoming LinkedIn Post Scheduled for {scheduled_time}**\n"
                "Please review the copy and visual card below before automated publication."
            ),
            "embeds": [
                {
                    "title": f"📋 {topic}",
                    "description": f"**Opening Hook:**\n> *\"{hook}\"*\n\n**Full LinkedIn Copy:**\n```\n{display_copy}\n```",
                    "color": 3719160, # Electric Cyan
                    "fields": [
                        {"name": "🎯 Focus", "value": target_focus, "inline": True},
                        {"name": "🏛️ Content Pillar", "value": pillar, "inline": True},
                        {"name": "⏰ Scheduled Time", "value": scheduled_time, "inline": True}
                    ],
                    "image": {
                        "url": "attachment://linkedin_preview.png"
                    },
                    "footer": {
                        "text": "Antigravity Agentic Marketing Automation System"
                    }
                }
            ]
        }

        try:
            with open(path, "rb") as f:
                files = {
                    "file": ("linkedin_preview.png", f, "image/png"),
                    "payload_json": (None, json.dumps(payload))
                }
                resp = requests.post(self.webhook_url, files=files, timeout=25)

            if resp.status_code in (200, 204):
                print("[Discord] Successfully delivered post preview with image to Discord!")
                return True
            else:
                print(f"[Discord] Discord webhook failed with status {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            print(f"[Discord] Failed to send Discord webhook: {e}")
            return False
