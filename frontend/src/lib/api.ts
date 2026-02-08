import type {
  TaskCreateRequest,
  TaskCreateResponse,
  TaskState,
  ConfirmAppointmentRequest,
  ConfirmAppointmentResponse,
} from "@/types/task";

const BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL ?? "http://localhost:5001";

function getErrorMessage(body: unknown): string {
  if (body == null || typeof body !== "object") return "Request failed";
  const d = (body as Record<string, unknown>).detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length > 0) {
    const first = d[0];
    if (first && typeof first === "object" && "msg" in first) return String((first as { msg: unknown }).msg);
    return d.map((x) => (typeof x === "object" && x && "msg" in x ? (x as { msg: unknown }).msg : x)).join("; ");
  }
  return (body as Record<string, unknown>).message != null
    ? String((body as Record<string, unknown>).message)
    : "Request failed";
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, getErrorMessage(body));
  }
  return res.json();
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function createTask(
  body: TaskCreateRequest
): Promise<TaskCreateResponse> {
  return request("/api/v1/tasks/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getTaskStatus(taskId: string): Promise<TaskState> {
  return request(`/api/v1/tasks/${taskId}`);
}

export async function confirmAppointment(
  body: ConfirmAppointmentRequest
): Promise<ConfirmAppointmentResponse> {
  return request("/api/v1/appointments/confirm", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
