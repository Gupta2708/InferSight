import { API_BASE } from "./api";

export type StreamEvent = {
  event: "start" | "token" | "done" | "error" | "cancelled";
  delta?: string;
  trace_id?: string;
  message_id?: string;
  sequence?: number;
  error_type?: string;
  message?: string;
};

export async function streamConversationMessage(
  conversationId: string,
  body: Record<string, unknown>,
  onEvent: (event: StreamEvent) => void
) {
  const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.trim()) onEvent(JSON.parse(line));
    }
  }
  if (buffer.trim()) onEvent(JSON.parse(buffer));
}

