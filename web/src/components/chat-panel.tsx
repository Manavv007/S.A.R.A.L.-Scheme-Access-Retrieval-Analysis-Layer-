"use client";

import { motion } from "framer-motion";
import { Bot, Mic, Send, User, Volume2 } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useRef, useState, type ReactNode } from "react";

import { Button } from "./ui/button";
import { Locale, localeToSpeechLang } from "@/i18n/config";
import type { ChatMessage, Profile } from "@/lib/types";
import { profileSummary } from "@/lib/profile-context";
import { useSpeechRecognition, useSpeechSynthesis } from "@/lib/use-speech";
import { cn } from "@/lib/utils";

export function ChatPanel({
  profile,
  fill = false,
  actions,
}: {
  profile: Profile | null;
  fill?: boolean;
  actions?: ReactNode;
}) {
  const t = useTranslations("chat");
  const locale = useLocale() as Locale;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const speechLang = localeToSpeechLang[locale];
  const { speak, supported: ttsOk } = useSpeechSynthesis();
  const { listening, supported: sttOk, start } = useSpeechRecognition((text) =>
    setInput((prev) => (prev ? `${prev} ${text}` : text)),
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send() {
    const query = input.trim();
    if (!query || streaming) return;
    setInput("");

    const history = messages;
    const next: ChatMessage[] = [...history, { role: "user", content: query }];
    setMessages([...next, { role: "assistant", content: "" }]);
    setStreaming(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, profile, history }),
      });

      if (!res.body) throw new Error("No response body");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = {
            role: "assistant",
            content: copy[copy.length - 1].content + chunk,
          };
          return copy;
        });
      }
    } catch {
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = {
          role: "assistant",
          content: "Connection error. Please try again.",
        };
        return copy;
      });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div
      className={cn(
        "glass flex flex-col overflow-hidden rounded-xl2 p-5 shadow-ambient-lg",
        fill ? "h-full min-h-0" : "h-[520px]",
      )}
    >
      <div className="mb-1 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-on-surface">
          <Bot className="h-4 w-4 text-primary-container" />
          {t("heading")}
        </div>
        {actions}
      </div>
      <p className={cn("text-xs text-on-surface-variant", profile ? "mb-2" : "mb-4")}>
        {t("subheading")}
      </p>
      {profileSummary(profile) && (
        <p className="mb-4 rounded-lg border border-primary-fixed bg-primary-fixed/40 px-2.5 py-1.5 text-[11px] text-on-primary-fixed-variant">
          Using your form profile: {profileSummary(profile)}
        </p>
      )}

      <div ref={scrollRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn("flex gap-2.5", m.role === "user" && "flex-row-reverse")}
          >
            <div
              className={cn(
                "grid h-7 w-7 flex-shrink-0 place-items-center rounded-lg border border-[#E0E0E0]",
                m.role === "user" ? "bg-primary-fixed" : "bg-surface-container-low",
              )}
            >
              {m.role === "user" ? (
                <User className="h-3.5 w-3.5 text-primary-container" />
              ) : (
                <Bot className="h-3.5 w-3.5 text-secondary" />
              )}
            </div>
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed",
                m.role === "user"
                  ? "bg-primary-container text-on-primary"
                  : "bg-surface-container-low text-on-surface",
              )}
            >
              {m.content || (
                <span className="text-on-surface-variant">{t("thinking")}</span>
              )}
              {m.role === "assistant" && m.content && ttsOk && (
                <button
                  type="button"
                  onClick={() => speak(m.content, speechLang)}
                  aria-label={t("listen")}
                  className="mt-2 flex items-center gap-1 text-[11px] text-on-surface-variant transition-colors hover:text-primary"
                >
                  <Volume2 className="h-3 w-3" />
                  {t("listen")}
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-4 flex items-center gap-2">
        {sttOk && (
          <button
            type="button"
            onClick={() => start(speechLang)}
            aria-label="Voice input"
            className={cn(
              "grid h-11 w-11 flex-shrink-0 place-items-center rounded-lg border border-[#E0E0E0] bg-white text-on-surface-variant transition-all hover:text-primary",
              listening && "animate-pulse-glow border-secondary-container text-secondary-container",
            )}
          >
            <Mic className="h-4 w-4" />
          </button>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={t("placeholder")}
          className="h-11 flex-1 rounded-lg border border-[#E0E0E0] bg-white px-4 text-sm text-on-surface placeholder:text-outline-variant focus:border-secondary-container focus:outline-none focus:ring-2 focus:ring-secondary-container/20"
        />
        <Button onClick={send} disabled={streaming || !input.trim()} className="h-11 px-4">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
