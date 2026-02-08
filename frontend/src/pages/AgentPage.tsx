import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Phone, ArrowLeft, Clock, Star, Trophy, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatPanel } from "@/components/ChatPanel";
import { TranscriptPanel } from "@/components/TranscriptPanel";
import { ResultsModal } from "@/components/ResultsModal";
import { ChatMessage, RankedSlot, TaskInput, TaskState } from "@/types/task";
import { createTask, getTaskStatus, confirmAppointment, ApiError } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

function SwarmResultsPanel({
  shortlist,
  onConfirmSlot,
}: {
  shortlist: RankedSlot[];
  onConfirmSlot: (slot: RankedSlot) => void;
}) {
  const top5 = shortlist.slice(0, 5);
  if (top5.length === 0) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-3 py-2 border-b border-border">
          <h3 className="text-xs font-semibold text-foreground">Top ranked providers</h3>
        </div>
        <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm p-3">
          No providers in shortlist
        </div>
      </div>
    );
  }
  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-border">
        <h3 className="text-xs font-semibold text-foreground">Top 5 ranked providers</h3>
        <p className="text-[10px] text-muted-foreground mt-0.5">Based on your preferences · confirm any slot</p>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {top5.map((slot, i) => (
            <Card key={`${slot.provider_id}-${slot.slot}`} className={i === 0 ? "ring-2 ring-accent/50" : ""}>
              <CardContent className="p-3 space-y-1.5">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    {i === 0 && (
                      <span className="text-[10px] font-bold uppercase tracking-wider text-accent bg-accent/10 px-1.5 py-0.5 rounded">
                        Top pick
                      </span>
                    )}
                    <h4 className="font-semibold text-foreground text-sm truncate">
                      {slot.provider_name ?? slot.provider_id}
                    </h4>
                  </div>
                  <span className="text-[10px] text-muted-foreground flex items-center gap-0.5 shrink-0">
                    <Trophy className="w-3 h-3" />#{slot.rank}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-0.5">
                    <Clock className="w-2.5 h-2.5" />
                    {new Date(slot.slot).toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}
                  </span>
                  <span className="flex items-center gap-0.5">
                    <Star className="w-2.5 h-2.5" />
                    {Number(slot.score).toFixed(1)}
                  </span>
                </div>
                <Button
                  size="sm"
                  onClick={() => onConfirmSlot(slot)}
                  className="w-full mt-1.5 h-8 text-xs bg-success text-success-foreground hover:bg-success/90"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                  Confirm appointment
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

export default function AgentPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const stateFromNav = location.state as TaskInput | null;
  const taskInput = stateFromNav || {
    description: "Book me a dental appointment",
    mode: "single",
    urgency: "asap",
  };

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-init",
      role: "user",
      content: taskInput.description,
      timestamp: new Date(),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskState, setTaskState] = useState<TaskState | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const terminalMessageAddedRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    const start = async () => {
      setIsCreating(true);
      terminalMessageAddedRef.current = false;
      setMessages([{ id: "msg-init", role: "user", content: taskInput.description, timestamp: new Date() }]);

      try {
        const res = await createTask({
          user_request: {
            message: taskInput.description,
            mode: taskInput.mode,
            preferences: taskInput.preferences,
          },
        });
        if (cancelled) return;
        setTaskId(res.task_id);
        addAgentMsg("Got it! I'm working on finding you an appointment…");
      } catch (err) {
        if (cancelled) return;
        const msg = err instanceof ApiError ? err.message : "Could not reach the backend. Is it running?";
        toast({ title: "Error", description: msg, variant: "destructive" });
        addAgentMsg(`⚠️ ${msg}`);
      } finally {
        setIsCreating(false);
      }
    };

    start();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!taskId) return;

    const poll = async () => {
      try {
        const state = await getTaskStatus(taskId);
        setTaskState(state);

        if (state.status === "completed") {
          stopPolling();
          if (!terminalMessageAddedRef.current) {
            terminalMessageAddedRef.current = true;
            if (state.shortlist.length > 0) {
              addAgentMsg("Great news! I've found available appointments. Here are your best options:");
              if (taskInput.mode !== "swarm") setShowResults(true);
            } else {
              addAgentMsg("The task completed but no appointment slots were found. Try again with different preferences.");
            }
          }
        } else if (state.status === "failed") {
          stopPolling();
          if (!terminalMessageAddedRef.current) {
            terminalMessageAddedRef.current = true;
            addAgentMsg(`⚠️ ${state.error_message ?? "Something went wrong. Please try again."}`);
          }
        } else if (state.status === "cancelled") {
          stopPolling();
          if (!terminalMessageAddedRef.current) {
            terminalMessageAddedRef.current = true;
            addAgentMsg("The task was cancelled.");
          }
        }
      } catch {
        // Silently retry on transient errors
      }
    };

    pollingRef.current = setInterval(poll, 2500);
    poll(); // immediate first poll
    return stopPolling;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  function stopPolling() {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }

  function addAgentMsg(content: string) {
    const id = `msg-agent-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id, role: "agent", content, timestamp: new Date() },
    ]);
  }

  const handleConfirmSlot = async (slot: RankedSlot) => {
    setShowResults(false);
    try {
      const res = await confirmAppointment({
        task_id: taskId!,
        provider_id: slot.provider_id,
        slot: slot.slot,
      });
      if (res.ok && res.appointment) {
        toast({ title: "Appointment Confirmed!", description: `${slot.provider_name} — ${new Date(slot.slot).toLocaleString()}` });
        addAgentMsg(
          `Your appointment with ${slot.provider_name ?? slot.provider_id} on ${new Date(slot.slot).toLocaleString()} has been confirmed!` +
          (res.appointment.calendar_link ? ` [View in Calendar](${res.appointment.calendar_link})` : "")
        );
      } else {
        toast({ title: "Error", description: res.error ?? "Could not confirm.", variant: "destructive" });
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to confirm appointment.";
      toast({ title: "Error", description: msg, variant: "destructive" });
    }
  };

  const handleSend = (text: string) => {
    setMessages((prev) => [
      ...prev,
      { id: `msg-user-${Date.now()}`, role: "user", content: text, timestamp: new Date() },
    ]);
  };

  const isRunning = taskState && (taskState.status === "pending" || taskState.status === "running");

  const isCompleted = taskState?.status === "completed";

  return (
    <div className="h-screen flex flex-col bg-background">
      <header className="flex items-center gap-3 px-4 py-3 border-b border-border glass-header z-10">
        <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
            <Phone className="w-3.5 h-3.5 text-accent-foreground" />
          </div>
          <span className="font-display text-sm font-bold text-foreground">BookLine Agent</span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${
            isRunning
              ? "bg-accent/10 text-accent"
              : "bg-success/10 text-success"
          }`}>
            ● {isRunning ? "Live" : isCreating ? "Connecting…" : taskState?.status === "completed" ? "Done" : "Ready"}
          </span>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 min-w-0">
          <ChatPanel messages={messages} onSend={handleSend} isTyping={isTyping || !!isRunning} />
        </div>
        {isCompleted && (
          <div className="hidden md:block w-80 border-l border-border bg-card/50">
            {taskInput.mode === "swarm" ? (
              <SwarmResultsPanel
                shortlist={taskState?.shortlist ?? []}
                onConfirmSlot={handleConfirmSlot}
              />
            ) : (
              <div className="h-full flex flex-col">
                <div className="px-3 py-2 border-b border-border">
                  <h3 className="text-xs font-semibold text-foreground">Transcript</h3>
                </div>
                <div className="flex-1 min-h-0">
                  <TranscriptPanel
                    transcript={taskState?.transcript}
                    outcomes={taskState?.outcomes}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {showResults && taskState?.shortlist && (
        <ResultsModal
          rankedSlots={taskState.shortlist}
          isSwarm={taskInput.mode === "swarm"}
          onConfirmSlot={handleConfirmSlot}
          onCancel={() => setShowResults(false)}
        />
      )}
    </div>
  );
}
