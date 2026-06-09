"use client";

import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import clsx from "clsx";
import { api } from "@/lib/api";
import { getModelsForProvider, getDefaultModelForProvider, isValidProviderModel } from "@/lib/providers";
import { compactDate } from "@/lib/formatters";
import { streamConversationMessage } from "@/lib/stream";
import type { Conversation, Message, ProviderCatalog, ProviderModel } from "@/lib/types";
import { Badge, StatusChip, StatusDot } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageIcon, SendIcon, SparkIcon, StopIcon, TraceIcon, TrashIcon } from "@/components/ui/icons";

export function ChatConsole() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [active, setActive] = useState<Conversation | null>(null);
  const [models, setModels] = useState<ProviderModel[]>([]);
  const [provider, setProvider] = useState("mock");
  const [model, setModel] = useState("mock-fast");
  const [input, setInput] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [mockScenario, setMockScenario] = useState("");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const messagePanelRef = useRef<HTMLDivElement | null>(null);
  const conversationListRef = useRef<HTMLDivElement | null>(null);

  async function refresh(preferredId = active?.id) {
    const list = await api<Conversation[]>("/api/conversations");
    setConversations(list);
    const nextSummary = preferredId ? list.find((item) => item.id === preferredId) : list[0];
    if (nextSummary) {
      setActive(await api<Conversation>(`/api/conversations/${nextSummary.id}`));
    } else {
      setActive(null);
    }
  }

  useEffect(() => {
    api<ProviderCatalog>("/api/providers")
      .then((data) => {
        setModels(data.models);
        const providers = [...new Set(data.models.filter((m) => m.enabled).map((m) => m.provider))];
        const currentProvider = providers.includes(provider) ? provider : providers[0] || provider;
        const defaultModel = getDefaultModelForProvider(data.models, currentProvider) || model;
        setProvider(currentProvider);
        setModel(defaultModel);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load providers"));
    refresh();
  }, []);

  const providerModels = useMemo(() => getModelsForProvider(models, provider), [models, provider]);

  useEffect(() => {
    if (!models.length) return;
    if (!isValidProviderModel(models, provider, model)) {
      setModel(getDefaultModelForProvider(models, provider));
    }
  }, [models, provider, model]);

  const visibleConversations = conversations;

  async function createConversation(): Promise<Conversation | null> {
    try {
      setError("");
      const conversation = await api<Conversation>("/api/conversations", {
        method: "POST",
        body: JSON.stringify({})
      });
      setActive(conversation);
      setConversations((current) => [conversation, ...current.filter((item) => item.id !== conversation.id)]);
      conversationListRef.current?.scrollTo({ top: 0 });
      messagePanelRef.current?.scrollTo({ top: 0 });
      requestAnimationFrame(() => inputRef.current?.focus());
      await refresh(conversation.id);
      return await api<Conversation>(`/api/conversations/${conversation.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create conversation");
      return null;
    }
  }

  async function deleteActiveConversation() {
    if (!active || isStreaming) return;
    if (!window.confirm(`Delete "${active.title}"? This removes only the currently selected conversation.`)) {
      return;
    }
    try {
      setError("");
      await api<{ status: string }>(`/api/conversations/${active.id}`, { method: "DELETE" });
      const nextList = conversations.filter((conversation) => conversation.id !== active.id);
      setConversations(nextList);
      const next = nextList[0];
      if (next) {
        setActive(await api<Conversation>(`/api/conversations/${next.id}`));
      } else {
        setActive(null);
      }
      messagePanelRef.current?.scrollTo({ top: 0 });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete conversation");
    }
  }

  async function selectConversation(conversationId: string) {
    try {
      setError("");
      setStreamingText("");
      const conversation = await api<Conversation>(`/api/conversations/${conversationId}`);
      setActive(conversation);
      messagePanelRef.current?.scrollTo({ top: 0 });
      requestAnimationFrame(() => inputRef.current?.focus());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load conversation");
    }
  }

  async function send() {
    if (!input.trim() || isStreaming) return;
    let conversation = active;
    if (!conversation) {
      conversation = await createConversation();
      if (!conversation) return;
    }
    const prompt = input.trim();
    setInput("");
    setStreamingText("");
    setIsStreaming(true);
    setError("");
    setActive({
      ...conversation,
      messages: [
        ...(conversation.messages || []),
        optimisticMessage(conversation.id, "user", prompt),
        optimisticMessage(conversation.id, "assistant", "")
      ]
    });
    try {
      await streamConversationMessage(
        conversation.id,
        {
          content: prompt,
          provider,
          model,
          temperature: 0.7,
          max_tokens: 800,
          mock_scenario: mockScenario || null
        },
        (event) => {
          if (event.event === "token") setStreamingText((current) => current + (event.delta || ""));
          if (event.event === "error" || event.event === "cancelled") {
            setError(formatProviderError(event.error_type, event.message));
          }
        }
      );
      await refresh(conversation.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setIsStreaming(false);
      setStreamingText("");
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  async function cancel() {
    if (!active || !isStreaming) return;
    await api(`/api/conversations/${active.id}/cancel`, { method: "POST" });
    setIsStreaming(false);
    await refresh(active.id);
  }

  const messages = active?.messages || [];

  return (
    <main className="page-enter mx-auto grid h-[calc(100dvh-88px)] max-w-7xl grid-cols-1 gap-4 overflow-hidden px-4 py-5 lg:grid-cols-[330px_minmax(0,1fr)]">
      <aside className="surface-card flex min-h-0 overflow-hidden">
        <div className="flex min-h-0 w-full flex-col">
        <div className="flex items-center justify-between gap-3 border-b border-black/10 p-3">
          <div>
            <h1 className="text-base font-semibold">Conversations</h1>
            <p className="text-xs text-ink/50">{conversations.length} saved threads</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              title="Delete current conversation"
              aria-label="Delete current conversation"
              onClick={deleteActiveConversation}
              disabled={!active || isStreaming}
              className="focus-ring inline-grid h-10 w-10 place-items-center rounded-md border border-black/10 bg-card text-ink/55 transition hover:-translate-y-0.5 hover:border-red-300/50 hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-35 disabled:hover:translate-y-0"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
            <Button onClick={createConversation} className="h-10 px-3">New</Button>
          </div>
        </div>
        <div ref={conversationListRef} className="min-h-0 flex-1 overflow-auto">
          {visibleConversations.map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => selectConversation(conversation.id)}
              className={clsx(
                "block w-full border-l-4 border-l-transparent border-b border-black/5 px-4 py-2.5 text-left text-sm transition-all hover:bg-paper/80",
                active?.id === conversation.id && "border-l-signal bg-paper shadow-inner"
              )}
            >
              <div className="flex min-w-0 items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-ink">{conversation.title}</div>
                  <div className="mt-0.5 line-clamp-2 text-xs leading-5 text-ink/60">
                    {conversation.preview || "No messages yet."}
                  </div>
                </div>
                <span className="shrink-0 pt-0.5 text-[11px] text-ink/45">{compactDate(conversation.last_message_at || conversation.updated_at)}</span>
              </div>
              <div className="mt-1.5 flex min-w-0 items-center gap-2">
                <StatusDot status={conversation.status} />
                {(conversation.message_count ?? 0) === 0 && <Badge className="ml-auto border-dashed">No messages</Badge>}
              </div>
            </button>
          ))}
          {!visibleConversations.length && (
            <div className="p-6 text-sm text-ink/55">No conversations yet. Start with New or send a prompt.</div>
          )}
        </div>
        </div>
      </aside>

      <section className="surface-card flex min-h-0 min-w-0 flex-col overflow-hidden">
        <div className="flex flex-wrap items-end gap-3 border-b border-black/10 bg-card/90 p-4">
          <Control label="Provider">
            <select
              className="rounded-md border border-black/15 bg-white px-3 py-2 text-sm shadow-sm transition focus:border-signal focus:outline-none"
              value={provider}
              onChange={(e) => {
                const nextProvider = e.target.value;
                setProvider(nextProvider);
                // reset model to default for selected provider
                const defaultModel = getDefaultModelForProvider(models, nextProvider);
                setModel(defaultModel || "");
              }}
            >
              {[...new Set(models.map((item) => item.provider))].map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </Control>
          <Control label="Model">
            <select
              className="rounded-md border border-black/15 bg-white px-3 py-2 text-sm shadow-sm transition focus:border-signal focus:outline-none"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {providerModels.map((item) => (
                <option key={item.model}>{item.model}</option>
              ))}
            </select>
          </Control>
          <Control label="Mock scenario">
            <select className="min-w-56 rounded-md border border-black/15 bg-white px-3 py-2 text-sm shadow-sm transition focus:border-signal focus:outline-none" value={mockScenario} onChange={(e) => setMockScenario(e.target.value)}>
              <option value="">normal</option>
              <option value="timeout">mock timeout</option>
              <option value="rate_limit">mock rate limit</option>
              <option value="provider_error">mock provider error</option>
              <option value="cancel_after_3">mock cancel test</option>
            </select>
          </Control>
          <Button onClick={cancel} disabled={!isStreaming} variant="warning">
            <StopIcon className="h-4 w-4" />
            Cancel
          </Button>
          {isStreaming && (
            <div className="ml-auto inline-flex items-center gap-2 rounded-full border border-signal/20 bg-signal/10 px-3 py-2 text-sm text-signal">
              <span className="typing-dot h-2 w-2 rounded-full bg-signal" />
              Streaming
            </div>
          )}
        </div>

        <div ref={messagePanelRef} className="min-h-0 flex-1 overflow-auto bg-paper p-5">
          {!active && <EmptyChat />}
          {active && messages.length === 0 && <EmptyChat />}
          <div className="space-y-4">
            {messages.map((message, index) => (
              <MessageBubble key={message.id || index} message={message} />
            ))}
            {isStreaming && streamingText && (
              <div className="max-w-4xl rounded-xl border border-signal/25 bg-signal/10 p-4 text-sm shadow-sm">
                <div className="mb-2 inline-flex items-center gap-2 text-[11px] font-medium uppercase text-signal">
                  <span className="typing-dot h-2 w-2 rounded-full bg-signal" />
                  Streaming
                </div>
                <div className="whitespace-pre-wrap leading-6">{streamingText}</div>
              </div>
            )}
            {error && (
              <div className="max-w-4xl rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {error}
              </div>
            )}
          </div>
        </div>

        <div className="sticky bottom-0 border-t border-black/10 bg-card/95 p-4 backdrop-blur">
          <div className="flex gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              className="min-h-16 flex-1 resize-none rounded-xl border border-black/15 px-4 py-3 text-sm shadow-sm transition focus:border-signal focus:outline-none focus:ring-4 focus:ring-signal/10"
              placeholder="Send a message. Try including an email to verify PII redaction in logs."
              onKeyDown={(event) => {
                if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) void send();
              }}
            />
            <Button onClick={send} disabled={isStreaming || !input.trim()} className="min-w-24 self-stretch">
              <SendIcon className="h-4 w-4" />
              {isStreaming ? "Sending" : "Send"}
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}

function formatProviderError(errorType?: string, message?: string) {
  if (errorType === "provider_auth_error" || errorType === "provider_invalid_model") {
    return "Provider model unavailable. Check API key/model config.";
  }
  return message || errorType || "Streaming failed";
}

function Control({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="grid gap-1 text-xs font-medium uppercase text-ink/50">
      {label}
      {children}
    </label>
  );
}

function EmptyChat() {
  return (
    <div className="grid min-h-72 place-items-center rounded-xl border border-dashed border-black/15 bg-card/80 p-8 text-center">
      <div>
        <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-signal/10 text-signal">
          <MessageIcon className="h-6 w-6" />
        </div>
        <h2 className="mt-3 font-semibold">No messages yet</h2>
        <p className="mt-1 max-w-sm text-sm text-ink/55">
          Send a prompt to generate observable inference traffic.
        </p>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const assistant = message.role === "assistant";
  const cancelled = message.status === "cancelled";
  const failed = message.status === "error" || message.status === "failed";
  return (
    <div
      className={clsx(
        "max-w-4xl rounded-lg border p-3 text-sm shadow-sm",
        assistant && !cancelled && !failed && "border-signal/20 bg-signal/10",
        assistant && cancelled && "border-amber-500/25 bg-amber-500/10",
        assistant && failed && "border-red-500/25 bg-red-500/10",
        !assistant && "ml-auto border-black/10 bg-card"
      )}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          {assistant ? <SparkIcon className="h-4 w-4 text-signal" /> : <MessageIcon className="h-4 w-4 text-ink/45" />}
          <span className="text-[11px] font-semibold uppercase tracking-wide text-ink/50">{message.role}</span>
          <StatusChip status={message.status} />
        </div>
        {message.trace_id && (
          <Link className="inline-flex items-center gap-1 rounded-md border border-signal/15 bg-card px-1.5 py-0.5 text-[11px] font-medium text-signal transition hover:bg-signal/10" href={`/traces/${message.trace_id}`}>
            <TraceIcon className="h-3.5 w-3.5" />
            Trace
          </Link>
        )}
      </div>
      <div className="whitespace-pre-wrap leading-6 text-ink">{message.content || (message.status === "streaming" ? "Waiting for first token..." : "")}</div>
    </div>
  );
}

function optimisticMessage(conversationId: string, role: "user" | "assistant", content: string): Message {
  const now = new Date().toISOString();
  return {
    id: `${role}-${now}`,
    conversation_id: conversationId,
    role,
    content,
    status: role === "assistant" ? "streaming" : "completed",
    created_at: now,
    updated_at: now
  };
}
