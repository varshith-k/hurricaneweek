"use client";

import { useEffect, useRef, useState } from "react";

import { AutoInsuranceQuiz } from "@/components/AutoInsuranceQuiz";
import { askAssistant, getAssistantIntro } from "@/lib/api";
import type { AskResponse, AssistantIntro, ChatTurn } from "@/lib/types";

interface Message extends ChatTurn {
  id: string;
  meta?: AskResponse;
}

function badgeFor(response: AskResponse): { label: string; tone: "danger" | "accent" | "muted" } | null {
  if (response.kind === "emergency") return { label: "Emergency guidance", tone: "danger" };
  if (response.kind === "greeting") return null;
  if (response.kind === "verified") return { label: "Verified answer", tone: "muted" };
  if (response.kind === "fallback") return { label: "Could not answer", tone: "muted" };
  if (response.ai_meta?.provider === "snowflake-cortex-rag") return { label: "Snowflake Cortex · RAG", tone: "accent" };
  if (response.ai_meta?.provider === "snowflake-cortex") return { label: "Snowflake Cortex", tone: "accent" };
  return { label: "Gemini (backup)", tone: "accent" };
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-3 w-3 shrink-0" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="m5 12 5 5L20 7" />
    </svg>
  );
}

export function ReadinessAssistant() {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<"chat" | "quiz">("chat");
  const [intro, setIntro] = useState<AssistantIntro | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open || intro) return;
    const simulationId = typeof window !== "undefined" ? sessionStorage.getItem("hurricane-week-sim") : null;
    getAssistantIntro(simulationId).then(setIntro).catch(() => setError("Could not load the assistant right now."));
  }, [open, intro]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const send = async (question: string, questionId?: string) => {
    if (!question.trim() && !questionId) return;
    setError(null);
    const userMessage: Message = { id: `${Date.now()}-u`, role: "user", content: question };
    setMessages((current) => [...current, userMessage]);
    setInput("");
    setLoading(true);
    try {
      const simulationId = typeof window !== "undefined" ? sessionStorage.getItem("hurricane-week-sim") : null;
      const history = messages.slice(-4).map(({ role, content }) => ({ role, content }));
      const response = await askAssistant(questionId ? { question_id: questionId } : { question }, simulationId, history);
      setMessages((current) => [...current, { id: `${Date.now()}-a`, role: "assistant", content: response.answer, meta: response }]);
    } catch {
      setError("The assistant is unavailable right now. Try again in a moment.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="fixed bottom-4 left-4 z-40 flex items-center gap-2 rounded-full border border-border bg-surface/90 px-4 py-2 text-sm text-muted shadow-lg backdrop-blur-sm transition hover:border-accent hover:text-text"
      >
        <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M12 2a7 7 0 0 0-7 7c0 3 1.5 4.5 2 6l-1 5 5-1.5c.3.1.7.1 1 .1a7 7 0 0 0 0-14Z" />
        </svg>
        Readiness Assistant
      </button>

      {open ? (
        <div className="fixed inset-x-4 bottom-20 top-16 z-50 mx-auto flex max-w-md flex-col overflow-hidden rounded-3xl border border-border bg-surface shadow-2xl sm:left-4 sm:right-auto sm:top-auto sm:h-[560px]">
          <div className="flex items-center justify-between border-b border-border p-4">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-muted">Readiness Assistant</p>
              <p className="text-sm text-text">{tab === "quiz" ? "How ready is your car for storm season?" : "Ask about hurricane prep for Miami-Dade"}</p>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close assistant" className="rounded-full p-1 text-muted hover:text-text">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                <path d="M6 6l12 12M18 6 6 18" />
              </svg>
            </button>
          </div>

          <div className="flex border-b border-border text-xs">
            <button
              type="button"
              onClick={() => setTab("chat")}
              className={`flex-1 px-3 py-2 uppercase tracking-[0.15em] transition ${tab === "chat" ? "border-b-2 border-accent text-text" : "text-muted hover:text-text"}`}
            >
              Ask a question
            </button>
            <button
              type="button"
              onClick={() => setTab("quiz")}
              className={`flex-1 px-3 py-2 uppercase tracking-[0.15em] transition ${tab === "quiz" ? "border-b-2 border-accent text-text" : "text-muted hover:text-text"}`}
            >
              Car &amp; storms
            </button>
          </div>

          {tab === "quiz" ? (
            <AutoInsuranceQuiz />
          ) : (
            <>
          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
            {intro ? (
              <div className="rounded-2xl border border-border bg-background p-3 text-xs text-muted">
                <p>{intro.emergency_notice}</p>
                {intro.powered_by.facts_count > 0 ? (
                  <p className="mt-2 text-[11px] uppercase tracking-[0.15em] text-muted/80">{intro.powered_by.data_credit}</p>
                ) : null}
              </div>
            ) : null}

            {messages.length === 0 && intro?.suggested_questions.length ? (
              <div className="flex flex-wrap gap-2">
                {intro.suggested_questions.map((suggestion) => (
                  <button
                    key={suggestion.id}
                    type="button"
                    onClick={() => void send(suggestion.question, suggestion.id)}
                    className="rounded-full border border-border bg-background px-3 py-1.5 text-xs text-muted transition hover:border-accent hover:text-text"
                  >
                    {suggestion.question}
                  </button>
                ))}
              </div>
            ) : null}

            {messages.map((message) => (
              <div key={message.id} className={message.role === "user" ? "flex justify-end" : "flex justify-start"}>
                <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${message.role === "user" ? "bg-accent text-background" : "border border-border bg-background text-text"}`}>
                  <p>{message.content}</p>
                  {message.meta && badgeFor(message.meta) ? (
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-muted">
                      <span className={`rounded-full border px-2 py-0.5 ${badgeFor(message.meta)!.tone === "danger" ? "border-danger/40 text-danger" : badgeFor(message.meta)!.tone === "accent" ? "border-accent/40 text-accent" : "border-border"}`}>
                        {badgeFor(message.meta)!.label}
                      </span>
                      {message.meta.ai_meta?.number_check === "passed" ? (
                        <span className="inline-flex items-center gap-1 text-success">
                          <CheckIcon /> Number-checked
                        </span>
                      ) : null}
                    </div>
                  ) : null}
                  {message.meta?.sources.length ? (
                    <p className="mt-1 text-[11px] text-muted">Source: {message.meta.sources.join(", ")}</p>
                  ) : null}
                </div>
              </div>
            ))}

            {loading ? <div className="text-xs text-muted">Thinking...</div> : null}
            {error ? <div className="rounded-xl border border-danger/30 bg-danger/10 p-2 text-xs text-danger">{error}</div> : null}
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              void send(input);
            }}
            className="flex items-center gap-2 border-t border-border p-3"
          >
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask a question..."
              maxLength={500}
              className="flex-1 rounded-full border border-border bg-background px-4 py-2 text-sm text-text outline-none focus:border-accent"
            />
            <button type="submit" disabled={loading || !input.trim()} className="rounded-full bg-accent px-4 py-2 text-sm font-medium text-background disabled:opacity-50">
              Ask
            </button>
          </form>
            </>
          )}
        </div>
      ) : null}
    </>
  );
}
