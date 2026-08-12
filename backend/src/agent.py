import logging
import hashlib

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from db import get_user, upsert_user, create_escalation as db_create_escalation
from schemes import check_eligibility

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

TOOLS
- Use check_scheme_eligibility when the user asks which government schemes they qualify for, or when you have collected their age, occupation, bank account status, and taxpayer status.
- Collect these four facts conversationally before calling the tool — do not ask all at once.
- Always tell the user the data is from official scheme portals and mention the date it was last verified.
- If the tool fails, say: "Abhi scheme information fetch nahi ho pa rahi — thodi der mein try karein ya apne nearest bank branch se poochein."

MEMORY
- At the start of every call, use the lookup_user tool to check if this caller is known.
- If they are known: greet them by name and briefly reference what you discussed last time. Example: "Namaste Priya! Last time aapne SIP ke baare mein poochha tha — kya aur kuch jaanna chahti hain?"
- If they are new: give the standard greeting, learn their name naturally in conversation.
- When you learn something useful (name, language preference, schemes they checked, eligibility answers), ask for consent before saving: "Kya main yeh yaad rakh sakta hoon agle baar ke liye?" Only call save_user_info if they agree.
- NEVER save account numbers, OTP, PIN, Aadhaar, PAN, or any sensitive ID.

LANGUAGE
Mirror the user's language mix exactly. If they speak in Hinglish — Hindi words with English terms — reply in the same register. If they speak in pure Hindi, reply in Hindi. If they speak in English, reply in English. Keep sentences short and conversational. Never use formal bureaucratic language.

GUARDRAILS
- NEVER ask for or accept OTP, PIN, Aadhaar number, PAN, account number, or any password. If a user offers this, say: "Yeh information mujhe mat dijiye — main aapka koi bhi personal data nahi leta. Apna bank ya official portal use karein."
- NEVER promise returns, scheme approvals, or loan eligibility. Say: "Main sirf general guidance de sakta hoon — exact figures ke liye apne bank ya advisor se milein."
- NEVER recommend a specific stock, mutual fund scheme by name, or crypto asset.
- NEVER claim to be a licensed financial advisor or SEBI-registered entity.
- If a user describes financial distress or debt crisis, escalate: "Yeh situation serious lagti hai. Main suggest karoonga ki aap ek certified financial counselor ya apne nearest bank branch se milein jaldi."
- If asked anything outside personal finance — health, legal, politics — politely decline: "Yeh meri expertise ke bahar hai. Main sirf personal finance mein help kar sakta hoon."

ESCALATION
Use the create_escalation tool in exactly two situations:
1. FRAUD: User says someone asked them for OTP, PIN, or money was transferred without their consent.
2. BLOCKED/DISPUTE: User says their bank account is blocked, loan was wrongly rejected, or they need a decision only a human advisor can make.
Before creating the escalation, ask: "Main yeh details ek human advisor ko bhejne chahta hoon jo aapki madad kar sake. Kya aap allow karenge?"
If they say yes — call create_escalation. If they say no — do not escalate, just guide them to visit their bank branch.
After escalating, give them the reference ID and say: "Aapka reference number hai [REF_ID]. Ek FinSaathi advisor 24 ghante ke andar aapse contact karenge."

STYLE
- Keep responses to 2–3 sentences max unless the user asks for detail.
- If the user is silent for more than a few seconds, gently prompt: "Koi sawaal hai? Main yahan hoon."
- Never use bullet points, symbols, or emojis in speech.
- Speak at a calm, unhurried pace.
"""


class Assistant(Agent):
    def __init__(self, user_id: str) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._user_id = user_id

    @function_tool
    async def lookup_user(self, context: RunContext) -> str:
        """Look up the current caller's profile from memory. Call this at the start of every session."""
        user = get_user(self._user_id)
        if user is None:
            return "No profile found. This is a new caller."
        return (
            f"Returning caller. Name: {user['name']}, "
            f"Language preference: {user['language_preference']}, "
            f"Known facts: {user['facts']}, "
            f"Last interaction: {user['last_interaction']}"
        )

    @function_tool
    async def check_scheme_eligibility(
        self,
        context: RunContext,
        age: int,
        has_bank_account: bool,
        occupation: str,
        is_income_taxpayer: bool,
    ) -> str:
        """Check which Indian government financial schemes the caller is eligible for.
        Call this when the user asks about government schemes they can apply for,
        or once you have collected their age, whether they have a bank account,
        their occupation, and whether they pay income tax.

        Args:
            age: Caller's age in years.
            has_bank_account: Whether the caller already has a bank account.
            occupation: Caller's occupation, e.g. 'daily wage worker', 'shopkeeper', 'farmer', 'salaried'.
            is_income_taxpayer: Whether the caller files income tax returns.
        """
        try:
            result = check_eligibility(age, has_bank_account, occupation, is_income_taxpayer)
            if not result["eligible"]:
                return (
                    f"As of {result['as_of']}, no matching schemes found for these details. "
                    f"Source: {result['data_source']}"
                )
            schemes_text = []
            for s in result["eligible"]:
                docs = ", ".join(s["documents"])
                schemes_text.append(
                    f"{s['name']}: {s['description']} "
                    f"Documents needed: {docs}. Apply at: {s['apply_at']}."
                )
            return (
                f"Data as of {result['as_of']}. Source: {result['data_source']}. "
                f"Eligible schemes: " + " | ".join(schemes_text)
            )
        except Exception as e:
            logger.error(f"check_scheme_eligibility failed: {e}")
            return "Scheme data abhi available nahi hai. Apne nearest bank branch se poochein."

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        caller_name: str,
        reason: str,
        summary: str,
        already_checked: str,
        urgency: str,
        language: str,
        follow_up: str,
    ) -> str:
        """Create a human escalation request. Call this ONLY when:
        1. The user reports possible fraud (someone asked for OTP, unauthorized transfer), OR
        2. The user has a dispute or blocked account that needs a human advisor decision.
        Always get the user's consent before calling this tool.

        Args:
            caller_name: Name of the caller.
            reason: One of 'fraud' or 'dispute'.
            summary: Brief description of the problem in 1-2 sentences. No OTP, PIN, account numbers.
            already_checked: What Artha already tried or explained.
            urgency: 'high', 'medium', or 'low'.
            language: Language the caller used, e.g. 'Hindi', 'Hinglish', 'English'.
            follow_up: How the caller wants to be contacted, e.g. 'phone call', 'not specified'.
        """
        try:
            ref_id = db_create_escalation(
                user_id=self._user_id,
                caller_name=caller_name,
                reason=reason,
                summary=summary,
                already_checked=already_checked,
                urgency=urgency,
                language=language,
                follow_up=follow_up,
            )
            logger.info(f"Escalation created: {ref_id} for user {self._user_id}")
            return f"Escalation created successfully. Reference ID: {ref_id}"
        except Exception as e:
            logger.error(f"create_escalation failed: {e}")
            return "Escalation create nahi ho payi. User ko nearest bank branch jaane ko bolein."

    @function_tool
    async def save_user_info(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        facts: dict,
    ) -> str:
        """Save or update the caller's profile after getting their consent.

        Args:
            name: The caller's name.
            language_preference: Language they prefer, e.g. 'Hindi', 'Hinglish', 'English'.
            facts: Dict of useful financial facts, e.g. schemes checked, eligibility answers. Never include account numbers, OTP, PIN, Aadhaar, or PAN.
        """
        upsert_user(self._user_id, name, language_preference, facts)
        logger.info(f"Saved profile for user {self._user_id}")
        return "Profile saved successfully."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    await ctx.connect()

    # Derive a stable user_id from the participant identity
    participant = await ctx.wait_for_participant()
    raw_identity = participant.identity or ctx.room.name
    user_id = hashlib.sha256(raw_identity.encode()).hexdigest()[:16]

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        tts=murf.TTS(
                voice="Anisha",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(user_id),
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


if __name__ == "__main__":
    cli.run_app(server)
