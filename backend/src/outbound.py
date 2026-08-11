"""
outbound.py — Trigger an outbound call to a user via Twilio + LiveKit SIP.

Usage:
    uv run python src/outbound.py --to +91XXXXXXXXXX --name "Rahul" --scheme "Atal Pension Yojana" --deadline "31 March 2026"

How it works:
1. Creates a LiveKit room for the call
2. Dispatches the outbound_agent to that room
3. Uses Twilio to dial the user's phone number via LiveKit SIP trunk
"""

import argparse
import asyncio
import os
import uuid

from dotenv import load_dotenv
from livekit import api
from twilio.rest import Client as TwilioClient

load_dotenv(".env.local")

LIVEKIT_URL = os.environ["LIVEKIT_URL"]
LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = os.environ["TWILIO_PHONE_NUMBER"]
LIVEKIT_SIP_TRUNK_ID = os.environ["LIVEKIT_SIP_TRUNK_ID"]


async def create_room_and_dispatch(room_name: str, user_name: str, scheme: str, deadline: str) -> str:
    """Create a LiveKit room and dispatch the outbound agent to it."""
    lk = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)

    # Create the room
    await lk.room.create_room(api.CreateRoomRequest(name=room_name))

    # Dispatch the outbound agent with call metadata
    await lk.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="outbound-agent",
            room=room_name,
            metadata=f"{user_name}|{scheme}|{deadline}",
        )
    )

    await lk.aclose()
    return room_name


async def dial_via_sip(room_name: str, to_number: str):
    """Create a SIP participant in the room to dial the user's phone."""
    lk = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)

    await lk.sip.create_sip_outbound_trunk(
        api.CreateSIPOutboundTrunkRequest(
            trunk=api.SIPOutboundTrunkInfo(
                name="twilio-outbound",
                address="pstn.twilio.com",
                numbers=[TWILIO_PHONE_NUMBER],
                auth_username=TWILIO_ACCOUNT_SID,
                auth_password=TWILIO_AUTH_TOKEN,
            )
        )
    ) if not LIVEKIT_SIP_TRUNK_ID else None

    await lk.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            sip_trunk_id=LIVEKIT_SIP_TRUNK_ID,
            sip_call_to=to_number,
            room_name=room_name,
            participant_identity="phone_user",
            participant_name="Caller",
            play_ringtone=True,
        )
    )

    await lk.aclose()


async def make_outbound_call(to_number: str, user_name: str, scheme: str, deadline: str):
    room_name = f"outbound_{uuid.uuid4().hex[:8]}"
    print(f"Creating room: {room_name}")

    await create_room_and_dispatch(room_name, user_name, scheme, deadline)
    print(f"Agent dispatched to room: {room_name}")

    await dial_via_sip(room_name, to_number)
    print(f"Dialing {to_number}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True, help="Phone number to call, e.g. +91XXXXXXXXXX")
    parser.add_argument("--name", required=True, help="User's name")
    parser.add_argument("--scheme", required=True, help="Scheme name to remind about")
    parser.add_argument("--deadline", required=True, help="Deadline date, e.g. '31 March 2026'")
    args = parser.parse_args()

    asyncio.run(make_outbound_call(args.to, args.name, args.scheme, args.deadline))
