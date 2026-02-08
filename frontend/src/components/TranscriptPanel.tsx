import { TranscriptTurn, NegotiationOutcome } from "@/types/task";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Phone, User } from "lucide-react";

interface TranscriptPanelProps {
  transcript?: TranscriptTurn[];
  outcomes?: NegotiationOutcome[];
}

function TranscriptView({ turns }: { turns: TranscriptTurn[] }) {
  if (!turns || turns.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No transcript available
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-3 space-y-2">
        {turns.map((turn, i) => {
          const isAgent = turn.role === "agent";
          return (
            <div
              key={i}
              className={`flex gap-2 ${isAgent ? "justify-start" : "justify-end"}`}
            >
              {isAgent && (
                <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                  <Phone className="w-3 h-3 text-primary" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                  isAgent
                    ? "bg-primary/5 text-foreground border border-primary/10"
                    : "bg-accent/30 text-accent-foreground border border-accent/20"
                }`}
              >
                <span className="font-medium text-[10px] uppercase tracking-wider opacity-60 block mb-0.5">
                  {isAgent ? "Agent" : "Receptionist"}
                </span>
                {turn.text}
              </div>
              {!isAgent && (
                <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <User className="w-3 h-3 text-accent-foreground" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}

export function TranscriptPanel({ transcript, outcomes }: TranscriptPanelProps) {
  if (transcript && transcript.length > 0 && (!outcomes || outcomes.length === 0)) {
    return (
      <div className="h-full flex flex-col">
        <div className="px-3 py-2 border-b border-border">
          <h3 className="text-xs font-semibold text-foreground">Call Transcript</h3>
        </div>
        <div className="flex-1 min-h-0">
          <TranscriptView turns={transcript} />
        </div>
      </div>
    );
  }

  if (outcomes && outcomes.length > 0) {
    const withTranscripts = outcomes.filter((o) => o.transcript?.length > 0);
    if (withTranscripts.length === 0) {
      return (
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
          No transcripts available
        </div>
      );
    }

    return (
      <div className="h-full flex flex-col">
        <Tabs defaultValue={withTranscripts[0].provider_id} className="flex flex-col h-full">
          <div className="px-3 py-2 border-b border-border">
            <TabsList className="h-7 w-full">
              {withTranscripts.map((o) => (
                <TabsTrigger key={o.provider_id} value={o.provider_id} className="text-[10px] flex-1">
                  {o.provider_id.slice(0, 12)}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>
          {withTranscripts.map((o) => (
            <TabsContent key={o.provider_id} value={o.provider_id} className="flex-1 min-h-0 mt-0">
              <TranscriptView turns={o.transcript} />
            </TabsContent>
          ))}
        </Tabs>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
      Transcript will appear after the call completes
    </div>
  );
}
