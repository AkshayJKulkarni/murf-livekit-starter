"""
outbound_agent.py — The agent that handles outbound scheme reminder calls.
Run alongside agent.py: uv run python src/outbound_agent.py dev
"""

import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("outbound-agent")

load_dotenv(".env.local")

OUTBOUND_PROMPT = """
IDENTITY
You are Artha, a voice assistant from FinSaathi. You are making an outbound reminder call — the user did not initiate this call.

OPENING — say this exactly in the first turn:
"Namaste {name}! Main Artha bol raha hoon, FinSaathi se. Aapko {scheme} ke baare mein ek zaroori reminder dene ke liye call kiya hai — deadline {deadline} hai. Agar aap yeh call nahi chahte, toh bas 'band karo' bolein aur main turant call khatam kar doonga."

OBJECTIVE
Remind the user that the scheme deadline is approaching, explain what they need to do next, and answer any questions they have. Keep it under 3 minutes.

GUARDRAILS
- NEVER ask for OTP, PIN, Aadhaar, PAN, or account number.
- NEVER promise scheme approval or guaranteed benefits.
- If the user says stop, end the call, or is not interested — say "Theek hai, koi baat nahi. Agar kabhi zaroorat ho toh FinSaathi pe call karein. Dhanyavaad!" and end immediately.
- If asked anything outside this scheme reminder — politely decline and stay on topic.

STYLE
- Short sentences. Calm pace.
- Mirror the user's language — Hindi, Hinglish, or English.
- Never use bullet points, symbols, or emojis in speech.
"""


class OutboundAssistant(Agent):
    def __init__(self, user_name: str, scheme: str, deadline: str) -> None:
        prompt = OUTBOUND_PROMPT.replace("{name}", user_name).replace("{scheme}", scheme).replace("{deadline}", deadline)
        super().__init__(instructions=prompt)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="outbound-agent")
async def outbound_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    await ctx.connect()

    participant = await ctx.wait_for_participant()

    # Read call metadata: "name|scheme|deadline"
    metadata = ctx.job.metadata or ""
    parts = metadata.split("|")
    user_name = parts[0] if len(parts) > 0 else "friend"
    scheme = parts[1] if len(parts) > 1 else "the scheme"
    deadline = parts[2] if len(parts) > 2 else "soon"

    logger.info(f"Outbound call to {user_name} about {scheme}, deadline {deadline}")

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=OutboundAssistant(user_name, scheme, deadline),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)
