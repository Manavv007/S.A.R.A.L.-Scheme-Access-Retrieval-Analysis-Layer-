"use client";

import { motion } from "framer-motion";
import { Bot, Send, User } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";

import { Button } from "./ui/button";
import type { ChatMessage, Profile } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ChatPanel({ profile }: { profile: Profile | null }) {
  const t = useTranslations("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

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
    <div className="glass flex h-[520px] flex-col rounded-xl2 p-5">
      <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-white">
        <Bot className="h-4 w-4 text-violet-400" />
        {t("heading")}
      </div>
      <p className="mb-4 text-xs text-white/45">{t("subheading")}</p>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn("flex gap-2.5", m.role === "user" && "flex-row-reverse")}
          >
            <div
              className={cn(
                "grid h-7 w-7 flex-shrink-0 place-items-center rounded-lg border border-white/10",
                m.role === "user" ? "bg-emerald-400/15" : "bg-violet-400/15",
              )}
            >
              {m.role === "user" ? (
                <User className="h-3.5 w-3.5 text-emerald-300" />
              ) : (
                <Bot className="h-3.5 w-3.5 text-violet-300" />
              )}
            </div>
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed",
                m.role === "user"
                  ? "bg-emerald-400/10 text-white"
                  : "bg-white/[0.04] text-white/80",
              )}
            >
              {m.content || (
                <span className="text-white/40">{t("thinking")}</span>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-4 flex items-center gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={t("placeholder")}
          className="h-11 flex-1 rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white placeholder:text-white/30 focus:border-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-400/15"
        />
        <Button onClick={send} disabled={streaming || !input.trim()} className="h-11 px-4">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
