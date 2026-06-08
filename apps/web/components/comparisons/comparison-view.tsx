"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { money, ms } from "@/lib/formatters";
import { Badge, ModelChip, ProviderChip, StatusChip } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CompareIcon, PlayIcon, TraceIcon } from "@/components/ui/icons";

type Result = {
  id: string;
  trace_id: string;
  provider: string;
  model: string;
  status: string;
  latency_ms?: number | null;
  time_to_first_token_ms?: number | null;
  total_tokens: number;
  estimated_total_cost: number;
  output_preview: string;
  error_type?: string | null;
};

type Run = {
  id: string;
  prompt: string;
  status: string;
  results: Result[];
};

const targets = [
  { provider: "mock", model: "mock-fast" },
  { provider: "mock", model: "mock-slow" },
  { provider: "mock", model: "mock-error" }
];

export function ComparisonView() {
  const [prompt, setPrompt] = useState("Summarize why LLM observability matters.");
  const [run, setRun] = useState<Run | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  async function start() {
    setRunning(true);
    setError("");
    try {
      const result = await api<Run>("/api/comparisons", {
        method: "POST",
        body: JSON.stringify({
          prompt,
          context_mode: "none",
          temperature: 0.7,
          max_tokens: 800,
          targets
        })
      });
      setRun(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run comparison");
    } finally {
      setRunning(false);
    }
  }

  const completed = [...(run?.results.filter((r) => r.status === "completed") || [])];
  const fastest = [...completed].sort((a, b) => (a.latency_ms || 0) - (b.latency_ms || 0))[0];
  const cheapest = [...completed].sort((a, b) => a.estimated_total_cost - b.estimated_total_cost)[0];

  return (
    <main className="page-enter mx-auto max-w-7xl px-4 py-6">
      <div className="mb-5">
        <p className="text-sm font-medium uppercase tracking-wide text-signal">Provider comparison</p>
        <h1 className="mt-1 text-2xl font-semibold">Compare provider behavior</h1>
        <p className="mt-1 max-w-2xl text-sm text-ink/55">
          Run the same prompt across providers/models and compare latency, tokens, cost, and failures.
        </p>
      </div>

      <section className="surface-card p-5">
        <label className="grid gap-2 text-sm font-medium text-ink/70">
          Prompt
          <textarea
            className="min-h-36 w-full resize-none rounded-xl border border-black/15 px-4 py-3 text-sm shadow-sm transition focus:border-signal focus:outline-none focus:ring-4 focus:ring-signal/10"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
        </label>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {targets.map((target) => (
              <Badge key={`${target.provider}-${target.model}`} tone={target.model === "mock-error" ? "warning" : "info"}>
                {target.provider}/{target.model}
              </Badge>
            ))}
          </div>
          <Button onClick={start} disabled={running || !prompt.trim()}>
            <PlayIcon className="h-4 w-4" />
            {running ? "Running comparison" : "Run Comparison"}
          </Button>
        </div>
      </section>

      {error && (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {!run && (
        <div className="mt-5 grid min-h-64 place-items-center rounded-xl border border-dashed border-black/15 bg-white/70 p-8 text-center">
          <div>
            <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-signal/10 text-signal">
              <CompareIcon className="h-6 w-6" />
            </div>
            <h2 className="mt-3 font-semibold">Run a comparison</h2>
            <p className="mt-1 text-sm text-ink/55">Run a comparison to see provider performance side by side.</p>
          </div>
        </div>
      )}

      {run && (
        <section className="mt-5 grid gap-4 lg:grid-cols-3">
          {run.results.map((result) => (
            <article
              key={result.id || result.trace_id}
              className={`surface-card overflow-hidden p-4 ${result.status === "completed" ? "" : "border-red-500/20 bg-red-500/5"}`}
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <ProviderChip provider={result.provider} />
                    <ModelChip model={result.model} />
                  </div>
                </div>
                <StatusChip status={result.status === "completed" ? "completed" : "error"} />
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <Metric label="Latency" value={ms(result.latency_ms)} />
                <Metric label="First token" value={ms(result.time_to_first_token_ms)} />
                <Metric label="Tokens" value={result.total_tokens} />
                <Metric label="Cost" value={money(result.estimated_total_cost)} />
                <Metric label="Error" value={result.error_type || "-"} />
                <div>
                  <div className="text-xs uppercase text-ink/45">Trace</div>
                  <Link className="mt-1 inline-flex items-center gap-1 font-medium text-signal underline" href={`/traces/${result.trace_id}`}>
                    <TraceIcon className="h-3.5 w-3.5" />
                    Open trace
                  </Link>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                {result.status !== "completed" && <StatusChip status="error" />}
                {fastest?.trace_id === result.trace_id && <Badge tone="info">fastest</Badge>}
                {cheapest?.trace_id === result.trace_id && <Badge tone="warning">cheapest</Badge>}
              </div>
              <pre className="mt-4 max-h-52 overflow-auto whitespace-pre-wrap rounded-lg bg-paper p-3 text-xs leading-6">
                {result.output_preview || result.error_type || "No output captured."}
              </pre>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <div className="text-xs uppercase text-ink/45">{label}</div>
      <div className="mt-1 font-semibold">{value}</div>
    </div>
  );
}
