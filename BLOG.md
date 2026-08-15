# How I Built Artha — A Hinglish Voice Agent for Financial Inclusion in India

## The Problem

Most Indians who need financial guidance — about SIPs, government schemes, insurance, or loans — can't easily access it. Bank branches are crowded. Apps are in English. Advisors are expensive.

Voice is different. You don't need to read or type. You just talk.

I built **Artha**, a voice AI agent from FinSaathi that helps everyday Indians understand personal finance in Hindi, Hinglish, or English — whichever they're comfortable with.

---

## What Artha Can Do

- Answer questions about SIPs, FDs, insurance, UPI, and government schemes
- Check eligibility for 6 major schemes: PM Jan Dhan, PMSBY, PMJJBY, Atal Pension Yojana, PM Mudra Shishu and Kishor
- Remember returning users and continue from last time
- Escalate fraud or disputes to a human advisor with a reference ID
- Hand off to Lakshmi, a specialist agent for Mudra loan queries
- Track call outcomes on a live analytics dashboard
- Refuse to accept OTP, PIN, Aadhaar, or account numbers — hard guardrails, not suggestions

---

## The Stack

```
User speaks → Deepgram STT → Gemini LLM → Murf Falcon TTS → LiveKit → User hears
```

- **Murf Falcon** — Text-to-speech. 55ms model latency, natural Indian English voice, no hardcoded locale so it adapts to Hindi and Hinglish automatically
- **Deepgram nova-3** — Speech-to-text with `language="multi"` for Hindi/Hinglish detection
- **Gemini 1.5 Flash Lite** — LLM for reasoning and conversation
- **LiveKit Agents** — Real-time audio transport and agent orchestration
- **SQLite** — Memory, escalations, and call analytics
- **Next.js** — Frontend with finance-themed UI showing all 5 agent states

---

## How to Run It

**Prerequisites:** Python 3.10+, Node.js 18+, uv, pnpm

```bash
git clone https://github.com/AkshayJKulkarni/murf-livekit-starter
cd murf-livekit-starter
```

Create `backend/.env.local`:
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
MURF_API_KEY=your_murf_key
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_API_KEY=your_gemini_key
```

Create `frontend/.env.local`:
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
AGENT_NAME=my-agent
```

Install and run:
```bash
cd backend && uv sync
.\start_app.ps1   # Windows
```

Open http://localhost:3000, click **Artha se baat karein**, and speak.

---

## Features I Built

### 1. Personality and Guardrails (Day 2)

The system prompt is structured in sections: IDENTITY, OBJECTIVES, KNOWLEDGE, LANGUAGE, GUARDRAILS, STYLE. The guardrails are hard rules:

```
NEVER ask for or accept OTP, PIN, Aadhaar number, PAN, or account number.
If a user offers this: "Yeh information mujhe mat dijiye — main aapka koi bhi 
personal data nahi leta."
```

The key insight: guardrails in the prompt work only if they're specific. "Be safe" does nothing. "Never accept OTP" works.

### 2. Multilingual Support

The original config had `locale="en-IN"` hardcoded in Murf TTS — this caused a foreign accent on Hindi responses. The fix:

```python
# Wrong
tts=murf.TTS(voice="Anisha", locale="en-IN")

# Right
tts=murf.TTS(voice="Anisha", style="Conversation")
stt=deepgram.STT(model="nova-3", language="multi")
```

Remove the locale. Let Murf detect it from the text. Set Deepgram to `multi` for Hindi detection.

### 3. Memory (Day 4)

SQLite with a `users` table. Two function tools — `lookup_user` called at session start, `save_user_info` called only after user gives consent. Consent before saving is a hard rule for Financial Services.

### 4. Scheme Eligibility Tool (Day 5)

A hand-built dataset of 6 government schemes with eligibility rules, documents, and where to apply. The tool description is what tells the LLM when to call it. If the tool fires at the wrong time or never fires — the description is the bug.

### 5. Human Escalation (Day 7)

Two triggers: fraud reports and account disputes. Consent-first flow — agent asks permission, creates escalation with reference ID, human advisor sees it on a live dashboard at `http://localhost:8080`.

### 6. Agent Handoff (Day 9)

Artha hands off to Lakshmi (Mudra Loan specialist) mid-conversation by returning an `Agent` instance from a function tool. The user doesn't reconnect — the conversation continues in the same session.

---

## The Hard Parts

**1. Invalid token on first run**
`AGENT_NAME` was blank in `frontend/.env.local`. Without it, LiveKit doesn't dispatch the agent to the room. Fix: set `AGENT_NAME=my-agent`.

**2. Foreign accent on Hindi**
Hardcoded `locale="en-IN"` caused unnatural Hindi responses. Fix: remove locale, let Murf auto-detect from text.

**3. Agent not responding after code changes**
Process initialization took 90+ seconds on first start. Browser connected before agent was ready. Fix: wait for `process initialized` in backend logs before connecting.

**4. Google API key format**
New Google AI Studio projects generate keys starting with `AQ.` instead of `AIza`. Both work.

---

## Architecture

```
Browser → LiveKit Cloud → Backend Agent
                              ↓
                    Deepgram STT (multi-language)
                              ↓
                    Gemini LLM + Function Tools
                    ├── lookup_user / save_user_info (SQLite)
                    ├── check_scheme_eligibility (local dataset)
                    ├── create_escalation (SQLite + dashboard)
                    ├── log_call_outcome (analytics)
                    └── transfer_to_mudra_specialist (agent handoff)
                              ↓
                    Murf Falcon TTS (Anisha voice)
                              ↓
                         LiveKit Cloud → Browser
```

---

## What I Learned

1. **Voice UX is different from chat UX.** No bullet points. No markdown. Short sentences. The agent must sound like a person, not a document.

2. **The tool description is the most important line of code.** The LLM decides when to call a tool based on that description alone.

3. **Consent-first is not just ethics — it's trust.** Asking before saving anything changes the tone of the entire conversation.

4. **Multilingual is a configuration problem, not a model problem.** The models can handle Hindi. You just have to stop hardcoding English.

---

## Links

- GitHub: https://github.com/AkshayJKulkarni/murf-livekit-starter
- Murf Falcon TTS: https://murf.ai/api/docs/text-to-speech/streaming
- LiveKit Agents: https://docs.livekit.io/agents
- Deepgram: https://developers.deepgram.com

---

*Built during 10 Days of Voice Agents — VoiceForBharat Edition, powered by Murf Falcon.*
