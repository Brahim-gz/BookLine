export type TaskMode = "single" | "swarm";
export type TaskUrgency = "asap" | "flexible" | "specific";

export interface TaskInput {
  description: string;
  mode: TaskMode;
  urgency: TaskUrgency;
  duration?: string;
  specificDate?: string;
  preferences?: PreferenceWeights;
}

export type AgentEventType =
  | "tool_call"
  | "call_started"
  | "call_finished"
  | "decision"
  | "error"
  | "info";

export interface AgentEvent {
  id: string;
  type: AgentEventType;
  message: string;
  timestamp: Date;
  icon?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  timestamp: Date;
}

export type TaskStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface PreferenceWeights {
  availability_weight: number;
  rating_weight: number;
  distance_weight: number;
}

export interface UserRequest {
  message: string;
  mode: TaskMode;
  preferences?: PreferenceWeights;
}

export interface TaskCreateRequest {
  user_request: UserRequest;
}

export interface TaskCreateResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TranscriptTurn {
  role: "agent" | "receptionist";
  text: string;
}

export interface NegotiationOutcome {
  provider_id: string;
  proposed_slot: string | null;
  confidence_score: number;
  rejection_reasons: string[];
  raw_metadata: Record<string, unknown>;
  transcript: TranscriptTurn[];
}

export interface RankedSlot {
  provider_id: string;
  provider_name: string | null;
  slot: string;
  score: number;
  rank: number;
}

export interface BookedAppointment {
  task_id: string;
  provider_id: string;
  slot: string;
  booked_at: string;
  calendar_event_id: string | null;
  calendar_link: string | null;
}

export interface ToolCallLogEntry {
  tool?: string;
  params?: Record<string, unknown>;
  result?: unknown;
}

export interface TaskState {
  task_id: string;
  status: TaskStatus;
  mode: TaskMode;
  user_request: UserRequest;
  created_at: string;
  updated_at: string;
  outcomes: NegotiationOutcome[];
  tool_calls_log: ToolCallLogEntry[];
  error_message: string | null;
  shortlist: RankedSlot[];
  confirmed_appointment: BookedAppointment | null;
  transcript: TranscriptTurn[];
}

export interface ConfirmAppointmentRequest {
  task_id: string;
  provider_id: string;
  slot: string;
}

export interface ConfirmAppointmentResponse {
  ok: boolean;
  appointment: BookedAppointment | null;
  error: string | null;
}
