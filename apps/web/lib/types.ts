export type Conversation = {
  id: string;
  title: string;
  status: string;
  preview?: string | null;
  message_count?: number;
  created_at: string;
  updated_at: string;
  last_message_at?: string | null;
  messages?: Message[];
};

export type Message = {
  id: string;
  conversation_id: string;
  role: "system" | "user" | "assistant";
  content: string;
  status: string;
  provider?: string | null;
  model?: string | null;
  trace_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type ProviderModel = {
  provider: string;
  model: string;
  enabled: boolean;
  key_configured: boolean;
  available: boolean;
  status_label: string;
  supports_streaming: boolean;
  input_cost_per_1k_tokens?: number | null;
  output_cost_per_1k_tokens?: number | null;
};

export type ProviderCatalog = {
  providers: string[];
  models: ProviderModel[];
  mock_mode: boolean;
};

export type LogRow = {
  trace_id: string;
  provider: string;
  model: string;
  status: string;
  latency_ms?: number | null;
  time_to_first_token_ms?: number | null;
  total_tokens: number;
  estimated_total_cost: number;
  input_preview: string;
  output_preview: string;
  error_type?: string | null;
  created_at: string;
};
