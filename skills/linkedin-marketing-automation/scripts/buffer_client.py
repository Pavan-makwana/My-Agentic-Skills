"""Buffer GraphQL API Client for LinkedIn Company Page Marketing Automation.

Certified Partner Middleware for LinkedIn Company Pages.
"""

import os
import json
import requests
from pathlib import Path


class BufferPublishingError(Exception):
    """Raised when Buffer API encounters a failure."""
    pass


class BufferClient:
    """Official GraphQL API client for Buffer to publish directly to LinkedIn Company Pages."""

    ENDPOINT = "https://api.buffer.com"

    def __init__(self, api_key: str = None, channel_id: str = None):
        self.api_key = api_key or os.getenv("BUFFER_API_KEY", "").strip()
        self.channel_id = channel_id or os.getenv("BUFFER_CHANNEL_ID", "").strip()
        if not self.api_key:
            raise ValueError("Buffer API key is not configured. Set BUFFER_API_KEY in environment.")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _execute(self, query: str, variables: dict = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            resp = requests.post(self.ENDPOINT, headers=self._headers(), json=payload, timeout=30)
            if resp.status_code != 200:
                raise BufferPublishingError(f"HTTP Error {resp.status_code}: {resp.text}")

            data = resp.json()
            if "errors" in data and data["errors"]:
                raise BufferPublishingError(f"GraphQL Error: {json.dumps(data['errors'])}")

            return data.get("data", {})
        except requests.RequestException as e:
            raise BufferPublishingError(f"Network error communicating with Buffer API: {e}")

    def get_channels(self) -> list[dict]:
        """Fetches all connected channels across organizations."""
        account_query = """
        query {
          account {
            organizations {
              id
              name
            }
          }
        }
        """
        data = self._execute(account_query)
        orgs = data.get("account", {}).get("organizations", [])
        if not orgs:
            return []

        channels_query = """
        query GetChannels($input: ChannelsInput!) {
          channels(input: $input) {
            id
            name
            service
          }
        }
        """
        all_channels = []
        for org in orgs:
            org_id = org.get("id")
            res = self._execute(channels_query, {"input": {"organizationId": org_id}})
            for ch in res.get("channels", []):
                ch["organization_id"] = org_id
                all_channels.append(ch)
        return all_channels

    def create_draft(self, text: str, asset_url: str = None, first_comment: str = None, channel_id: str = None) -> dict:
        """Saves a post as a Draft in Buffer for review before live publishing."""
        return self._create_post(
            text=text,
            mode="addToQueue",
            save_to_draft=True,
            asset_url=asset_url,
            first_comment=first_comment,
            channel_id=channel_id
        )

    def publish_now(self, text: str, asset_url: str = None, first_comment: str = None, channel_id: str = None) -> dict:
        """Immediately publishes the post live to the connected LinkedIn channel."""
        return self._create_post(
            text=text,
            mode="shareNow",
            save_to_draft=False,
            asset_url=asset_url,
            first_comment=first_comment,
            channel_id=channel_id
        )

    def schedule_post(self, text: str, due_at: str = None, asset_url: str = None, first_comment: str = None, channel_id: str = None) -> dict:
        """Adds post to Buffer queue or schedules for a specific ISO-8601 UTC timestamp."""
        mode = "customScheduled" if due_at else "addToQueue"
        return self._create_post(
            text=text,
            mode=mode,
            save_to_draft=False,
            due_at=due_at,
            asset_url=asset_url,
            first_comment=first_comment,
            channel_id=channel_id
        )

    def delete_post(self, post_id: str) -> dict:
        """Deletes a post or draft from Buffer."""
        mutation = """
        mutation DeletePost($input: DeletePostInput!) {
          deletePost(input: $input) {
            ... on DeletePostSuccess {
              id
            }
            ... on VoidMutationError {
              message
            }
          }
        }
        """
        return self._execute(mutation, {"input": {"id": post_id}})

    def _create_post(
        self,
        text: str,
        mode: str,
        save_to_draft: bool,
        due_at: str = None,
        asset_url: str = None,
        first_comment: str = None,
        channel_id: str = None
    ) -> dict:
        target_channel = channel_id or self.channel_id
        if not target_channel:
            raise BufferPublishingError("No target Buffer channel_id provided.")

        mutation = """
        mutation CreatePost($input: CreatePostInput!) {
          createPost(input: $input) {
            ... on PostActionSuccess {
              post {
                id
                text
                status
                dueAt
              }
            }
            ... on MutationError {
              message
            }
          }
        }
        """

        post_input = {
            "channelId": target_channel,
            "text": text,
            "schedulingType": "automatic",
            "mode": mode,
            "saveToDraft": save_to_draft,
            "needsApproval": False
        }

        if due_at:
            post_input["dueAt"] = due_at

        if asset_url:
            post_input["assets"] = [
                {
                    "image": {
                        "url": asset_url
                    }
                }
            ]

        if first_comment:
            post_input["metadata"] = {
                "linkedin": {
                    "firstComment": first_comment
                }
            }

        data = self._execute(mutation, {"input": post_input})
        result = data.get("createPost", {})

        if "message" in result:
            raise BufferPublishingError(f"Buffer Mutation Error: {result['message']}")

        post_info = result.get("post", {})
        return {
            "success": True,
            "post_id": post_info.get("id"),
            "status": post_info.get("status"),
            "due_at": post_info.get("dueAt"),
            "channel_id": target_channel
        }
