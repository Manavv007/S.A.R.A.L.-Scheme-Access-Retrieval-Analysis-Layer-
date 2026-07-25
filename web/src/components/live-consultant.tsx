"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AudioLines, Loader2, Mic, PhoneOff, Send, Volume2 } from "lucide-react";
import { useLocale } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { Locale, localeToBackendLanguage } from "@/i18n/config";
import { formProfileToVoiceSlots } from "@/lib/profile-context";
import type { Profile } from "@/lib/types";
import { cn } from "@/lib/utils";

type Status = "idle" | "listening" | "thinking" | "speaking";
type Turn = { role: "user" | "assistant"; content: string };

interface ConverseResponse {
  reply: string;
  profile: Record<string, unknown>;
  phase: string;
  done?: boolean;
  schemes?: { scheme_name: string; eligibility_status: string }[];
  error?: string;
}

const PHASE_LABEL: Record<string, string> = {
  greet: "Starting…",
  collect: "Getting to know you",
  qa: "Ask me anything",
};

export function LiveConsultant({
  seedProfile = null,
}: {
  /** Form profile after "Run analysis"; null → officer asks demographics. */
  seedProfile?: Profile | null;
}) {
  const locale = useLocale() as Locale;
  const language = localeToBackendLanguage[locale];

  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status>("idle");
  const [phase, setPhase] = useState("greet");
  const [profile, setProfile] = useState<Record<string, unknown>>({});
  const [turns, setTurns] = useState<Turn[]>([]);
  const [schemes, setSchemes] = useState<ConverseResponse["schemes"]>([]);
  const [textInput, setTextInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const turnsRef = useRef<Turn[]>([]);
  const phaseRef = useRef(phase);
  const profileRef = useRef(profile);

  // Keep refs in sync so async callbacks read the latest state.
  useEffect(() => void (turnsRef.current = turns), [turns]);
  useEffect(() => void (phaseRef.current = phase), [phase]);
  useEffect(() => void (profileRef.current = profile), [profile]);
  // Portal target is only available after client mount (avoids SSR mismatch).
  useEffect(() => setMounted(true), []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, status]);

  // ── Play a reply via server TTS (falls back silently on failure) ──
  const speak = useCallback(
    async (text: string) => {
      if (!text) return;
      try {
        setStatus("speaking");
        const res = await fetch("/api/voice/tts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, language }),
        });
        if (!res.ok) throw new Error("tts failed");
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;
        await new Promise<void>((resolve) => {
          audio.onended = () => resolve();
          audio.onerror = () => resolve();
          audio.play().catch(() => resolve());
        });
        URL.revokeObjectURL(url);
      } catch {
        /* ignore playback errors; transcript still shows the reply */
      } finally {
        setStatus("idle");
      }
    },
    [language],
  );

  // ── Send a user message (from STT or typed) to the dialogue engine ──
  const converse = useCallback(
    async (message: string) => {
      setStatus("thinking");
      setError(null);
      try {
        const res = await fetch("/api/voice/converse", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message,
            profile: profileRef.current,
            history: turnsRef.current,
            phase: phaseRef.current,
            language,
          }),
        });
        const data: ConverseResponse = await res.json();
        if (data.error) throw new Error(data.error);

        setProfile(data.profile || {});
        setPhase(data.phase || "collect");
        if (data.schemes?.length) setSchemes(data.schemes);
        setTurns((prev) => [...prev, { role: "assistant", content: data.reply }]);
        await speak(data.reply);
      } catch (e) {
        setStatus("idle");
        setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
      }
    },
    [language, speak],
  );

  // ── Recording → STT ──
  const sendAudio = useCallback(
    async (blob: Blob) => {
      setStatus("thinking");
      try {
        const form = new FormData();
        form.append("file", blob, "answer.webm");
        form.append("language", language);
        const res = await fetch("/api/voice/stt", { method: "POST", body: form });
        const data = await res.json();
        const text = (data.text || "").trim();
        if (!text) {
          setStatus("idle");
          setError("I couldn't hear that clearly. Please try again.");
          return;
        }
        setTurns((prev) => [...prev, { role: "user", content: text }]);
        await converse(text);
      } catch {
        setStatus("idle");
        setError("Transcription failed. You can type your answer instead.");
      }
    },
    [language, converse],
  );

  const stopTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  const startListening = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stopTracks();
        if (blob.size > 0) void sendAudio(blob);
        else setStatus("idle");
      };
      recorderRef.current = recorder;
      recorder.start();
      setStatus("listening");
    } catch {
      setError("Microphone access is needed for voice. You can type instead.");
      setStatus("idle");
    }
  }, [sendAudio, stopTracks]);

  const stopListening = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
  }, []);

  const onOrbClick = useCallback(() => {
    if (status === "idle") void startListening();
    else if (status === "listening") stopListening();
    else if (status === "speaking") {
      audioRef.current?.pause();
      setStatus("idle");
    }
  }, [status, startListening, stopListening]);

  const submitText = useCallback(() => {
    const msg = textInput.trim();
    if (!msg || status === "thinking") return;
    setTextInput("");
    setTurns((prev) => [...prev, { role: "user", content: msg }]);
    void converse(msg);
  }, [textInput, status, converse]);

  // ── Open / close lifecycle ──
  const openLive = useCallback(async () => {
    setOpen(true);
    setStatus("thinking");
    setPhase("greet");
    const seeded = formProfileToVoiceSlots(seedProfile);
    setProfile(seeded);
    setTurns([]);
    setSchemes([]);
    setError(null);
    try {
      const res = await fetch("/api/voice/converse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "",
          profile: seeded,
          history: [],
          phase: "greet",
          language,
        }),
      });
      const data: ConverseResponse = await res.json();
      setProfile(data.profile || seeded);
      setPhase(data.phase || "collect");
      if (data.schemes?.length) setSchemes(data.schemes);
      setTurns([{ role: "assistant", content: data.reply }]);
      await speak(data.reply);
    } catch {
      setStatus("idle");
      setError("Could not start the conversation. Is the backend running?");
    }
  }, [language, speak, seedProfile]);

  const closeLive = useCallback(() => {
    audioRef.current?.pause();
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    stopTracks();
    setOpen(false);
    setStatus("idle");
  }, [stopTracks]);

  useEffect(() => () => stopTracks(), [stopTracks]);

  const orbLabel =
    status === "listening" ? "Listening… tap to send"
      : status === "thinking" ? "Thinking…"
        : status === "speaking" ? "Speaking… tap to skip"
          : "Tap to speak";

  return (
    <>
      {/* Launcher — compact icon button (placed inside the chat window) */}
      <button
        type="button"
        onClick={openLive}
        aria-label="Live voice chat"
        title="Live voice chat"
        className="grid h-7 w-7 place-items-center rounded-lg border border-secondary-container/30 bg-primary-fixed text-primary-container transition-colors hover:border-secondary-container hover:text-secondary"
      >
        <AudioLines className="h-4 w-4" />
      </button>

      {/* Portal escapes the chat window's transform stacking context so
          position:fixed covers the real viewport instead of the widget. */}
      {mounted &&
        createPortal(
          <AnimatePresence>
            {open && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] flex items-center justify-center bg-[#191c1d]/45 p-4 backdrop-blur-md"
              >
                <motion.div
                  initial={{ scale: 0.94, y: 20 }}
                  animate={{ scale: 1, y: 0 }}
                  exit={{ scale: 0.94, y: 20 }}
                  className="glass flex max-h-[calc(100dvh-2rem)] w-full max-w-lg flex-col overflow-hidden rounded-xl2 p-5 h-[min(86vh,calc(100dvh-2rem))] shadow-ambient-xl"
                >
                  {/* Header */}
                  <div className="flex shrink-0 items-center justify-between">
                    <div>
                      <div className="text-sm font-bold text-on-surface">Talk to an Officer</div>
                      <div className="text-[11px] text-secondary">
                        {PHASE_LABEL[phase] || "Live"} · {language}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={closeLive}
                      aria-label="End conversation"
                      className="grid h-9 w-9 place-items-center rounded-full border border-error/20 bg-error-container/40 text-error transition-colors hover:bg-error-container"
                    >
                      <PhoneOff className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Transcript */}
                  <div ref={scrollRef} className="mt-4 min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
                    {turns.map((t, i) => (
                      <div
                        key={i}
                        className={cn("flex", t.role === "user" && "justify-end")}
                      >
                        <div
                          className={cn(
                            "max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed",
                            t.role === "user"
                              ? "bg-primary-container text-on-primary"
                              : "bg-surface-container-low text-on-surface",
                          )}
                        >
                          {t.content}
                        </div>
                      </div>
                    ))}

                    {schemes && schemes.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {schemes.map((s, i) => (
                          <span
                            key={`${s.scheme_name}-${i}`}
                            className={cn(
                              "rounded-full border px-2.5 py-1 text-[11px]",
                              (s.eligibility_status || "").toLowerCase().includes("near")
                                ? "border-amber-400/40 bg-amber-50 text-amber-800"
                                : "border-primary-fixed bg-primary-fixed/50 text-on-primary-fixed-variant",
                            )}
                          >
                            {s.scheme_name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {error && (
                    <p className="mt-2 shrink-0 text-center text-xs text-error">{error}</p>
                  )}

                  {/* Orb */}
                  <div className="mt-4 flex shrink-0 flex-col items-center gap-2">
                    <motion.button
                      type="button"
                      onClick={onOrbClick}
                      disabled={status === "thinking"}
                      whileTap={{ scale: 0.94 }}
                      aria-label={orbLabel}
                      className={cn(
                        "grid h-20 w-20 place-items-center rounded-full text-on-primary shadow-ambient-lg transition-colors disabled:opacity-70",
                        status === "listening"
                          ? "animate-pulse-glow bg-secondary-container"
                          : status === "speaking"
                            ? "bg-secondary"
                            : "bg-primary-container",
                      )}
                    >
                      {status === "thinking" ? (
                        <Loader2 className="h-7 w-7 animate-spin" />
                      ) : status === "speaking" ? (
                        <Volume2 className="h-7 w-7" />
                      ) : (
                        <Mic className="h-7 w-7" />
                      )}
                    </motion.button>
                    <span className="text-xs text-on-surface-variant">{orbLabel}</span>
                  </div>

                  {/* Type-instead fallback */}
                  <div className="mt-3 flex shrink-0 items-center gap-2">
                    <input
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && submitText()}
                      placeholder="…or type your answer"
                      className="h-10 flex-1 rounded-lg border border-[#E0E0E0] bg-white px-4 text-sm text-on-surface placeholder:text-outline-variant focus:border-secondary-container focus:outline-none focus:ring-2 focus:ring-secondary-container/20"
                    />
                    <button
                      type="button"
                      onClick={submitText}
                      disabled={!textInput.trim() || status === "thinking"}
                      aria-label="Send"
                      className="grid h-10 w-10 place-items-center rounded-lg bg-primary-container text-on-primary transition-all hover:-translate-y-0.5 disabled:opacity-50"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>,
          document.body,
        )}
    </>
  );
}
