'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

function RupeeIcon() {
  return (
    <svg
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mb-4 size-16 text-emerald-600 dark:text-emerald-400"
    >
      <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="3" />
      <text
        x="32"
        y="44"
        textAnchor="middle"
        fontSize="28"
        fontWeight="bold"
        fill="currentColor"
        fontFamily="sans-serif"
      >
        ₹
      </text>
    </svg>
  );
}

function MicBlockedBanner() {
  return (
    <div className="mx-auto mt-4 max-w-sm rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-center text-sm text-red-700 dark:border-red-700 dark:bg-red-950 dark:text-red-300">
      <p className="font-semibold">Microphone access blocked</p>
      <p className="mt-1 text-xs">
        Browser settings mein microphone allow karein, phir page reload karein.
      </p>
    </div>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [micBlocked, setMicBlocked] = useState(false);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    navigator.permissions
      .query({ name: 'microphone' as PermissionName })
      .then((result) => {
        if (result.state === 'denied') setMicBlocked(true);
        result.onchange = () => setMicBlocked(result.state === 'denied');
      })
      .catch(() => {});
  }, []);

  async function handleStart() {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setConnecting(true);
      onStartCall();
    } catch {
      setMicBlocked(true);
    }
  }

  return (
    <div ref={ref}>
      <section className="bg-background flex flex-col items-center justify-center text-center px-4">
        <RupeeIcon />

        <h1 className="text-foreground text-2xl font-bold tracking-tight">Artha</h1>
        <p className="text-muted-foreground mt-1 text-sm">by FinSaathi</p>

        <p className="text-foreground mt-4 max-w-xs text-sm leading-6">
          Apne savings, SIP, insurance aur government schemes ke baare mein Hindi ya English mein poochein.
        </p>

        {micBlocked && <MicBlockedBanner />}

        <Button
          size="lg"
          onClick={handleStart}
          disabled={connecting || micBlocked}
          className="mt-6 w-64 rounded-full bg-emerald-600 font-mono text-xs font-bold tracking-wider uppercase text-white hover:bg-emerald-700 disabled:opacity-60 dark:bg-emerald-500 dark:hover:bg-emerald-600"
        >
          {connecting ? 'Connecting...' : startButtonText}
        </Button>

        <p className="text-muted-foreground mt-3 text-xs">
          SEBI-registered advisor nahi hoon · Sirf general guidance
        </p>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center">
        <p className="text-muted-foreground max-w-prose pt-1 text-xs leading-5 font-normal text-pretty">
          Powered by{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://murf.ai/api/docs/text-to-speech/streaming"
            className="underline"
          >
            Murf Falcon TTS
          </a>
        </p>
      </div>
    </div>
  );
};
