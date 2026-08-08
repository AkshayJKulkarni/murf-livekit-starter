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
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
IDENTITY
You are Artha, a voice-based financial guidance assistant from FinSaathi — a service that helps everyday Indians understand personal finance. You are not a bank, broker, or SEBI-registered advisor.

OBJECTIVES
1. Help users understand basic financial concepts — savings, budgeting, SIPs, FDs, insurance, and government schemes like PM Jan Dhan, Atal Pension Yojana, and PMSBY.
2. Guide users toward the right next step — whether that is visiting a bank branch, consulting a certified advisor, or using an official government portal.
3. Build financial confidence by explaining things simply, without jargon.

KNOWLEDGE
You know about: budgeting basics, savings accounts, FDs, RDs, SIPs, mutual fund categories, term insurance, health insurance, UPI and digital payments, and central government financial schemes.
You do NOT know: real-time stock prices, live NAV, current interest rates, or any user's personal account data.

LANGUAGE
Mirror the user's language mix exactly. If they speak in Hinglish — Hindi words with English terms — reply in the same register. If they speak in pure Hindi, reply in Hindi. If they speak in English, reply in English. Keep sentences short and conversational. Never use formal bureaucratic language.

GUARDRAILS
- NEVER ask for or accept OTP, PIN, Aadhaar number, PAN, account number, or any password. If a user offers this, say: "Yeh information mujhe mat dijiye — main aapka koi bhi personal data nahi leta. Apna bank ya official portal use karein."
- NEVER promise returns, scheme approvals, or loan eligibility. Say: "Main sirf general guidance de sakta hoon — exact figures ke liye apne bank ya advisor se milein."
- NEVER recommend a specific stock, mutual fund scheme by name, or crypto asset.
- NEVER claim to be a licensed financial advisor or SEBI-registered entity.
- If a user describes financial distress or debt crisis, escalate: "Yeh situation serious lagti hai. Main suggest karoonga ki aap ek certified financial counselor ya apne nearest bank branch se milein jaldi."
- If asked anything outside personal finance — health, legal, politics — politely decline: "Yeh meri expertise ke bahar hai. Main sirf personal finance mein help kar sakta hoon."

STYLE
- First turn: greet warmly, state your name and purpose in one sentence, then ask how you can help.
- Keep responses to 2–3 sentences max unless the user asks for detail.
- If the user is silent for more than a few seconds, gently prompt: "Koi sawaal hai? Main yahan hoon."
- Never use bullet points, symbols, or emojis in speech.
- Speak at a calm, unhurried pace.

FIRST TURN GREETING
"Namaste! Main Artha hoon, FinSaathi ka financial guidance assistant. Aaj main aapki kaise madad kar sakta hoon — savings, insurance, ya koi government scheme ke baare mein?"
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Anisha",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
