"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bot, Maximize2, MessageCircle, Minimize2, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChatPanel } from "./chat-panel";
import { LiveConsultant } from "./live-consultant";
import type { Profile } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Floating AI consultant. Collapsed it is a clickable circle anchored to the
 * bottom-right. Clicking opens a compact chat window; the expand button grows
 * it into a large window. Closing returns it to the circle.
 */
export function ChatConsultant({ profile }: { profile: Profile | null }) {
  const t = useTranslations("chat");
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const iconBtn =
    "grid h-7 w-7 place-items-center rounded-lg border border-white/10 bg-white/[0.04] text-white/60 transition-colors hover:text-white hover:border-white/20";

  return (
    <div className="fixed bottom-6 right-6 z-40 flex flex-col items-end gap-3">
      <AnimatePresence>
        {open && (
          <motion.div
            key="window"
            initial={{ opacity: 0, scale: 0.85, y: 24 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 24 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
            style={{ transformOrigin: "bottom right" }}
            className={cn(
              "overflow-hidden transition-[width,height] duration-300 ease-out",
              expanded
                ? "h-[min(80vh,calc(100dvh-6.5rem))] w-[min(720px,92vw)]"
                : "h-[min(560px,72vh,calc(100dvh-6.5rem))] w-[min(400px,92vw)]",
            )}
          >
            <ChatPanel
              profile={profile}
              fill
              actions={
                <div className="flex items-center gap-1.5">
                  <LiveConsultant seedProfile={profile} />
                  <button
                    type="button"
                    onClick={() => setExpanded((e) => !e)}
                    aria-label={expanded ? "Collapse" : "Expand"}
                    title={expanded ? "Collapse" : "Expand"}
                    className={iconBtn}
                  >
                    {expanded ? (
                      <Minimize2 className="h-3.5 w-3.5" />
                    ) : (
                      <Maximize2 className="h-3.5 w-3.5" />
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setOpen(false);
                      setExpanded(false);
                    }}
                    aria-label="Close"
                    title="Close"
                    className={iconBtn}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              }
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toggle circle */}
      <motion.button
        type="button"
        onClick={() => setOpen((o) => !o)}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.9 }}
        aria-label={open ? "Close consultant" : t("heading")}
        title={t("heading")}
        className="relative grid h-14 w-14 place-items-center rounded-full bg-gradient-to-br from-violet-500 to-emerald-500 text-white shadow-[0_10px_40px_-8px_rgba(139,92,246,0.7)]"
      >
        {!open && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-violet-400/40" />
        )}
        <AnimatePresence mode="wait" initial={false}>
          {open ? (
            <motion.span
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="relative"
            >
              <X className="h-6 w-6" />
            </motion.span>
          ) : (
            <motion.span
              key="open"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="relative"
            >
              <MessageCircle className="h-6 w-6" />
              <Bot className="absolute -right-1 -top-1 h-3 w-3" />
            </motion.span>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
