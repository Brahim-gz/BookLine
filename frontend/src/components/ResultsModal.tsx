import { motion } from "framer-motion";
import { Star, Clock, CheckCircle2, X, Trophy } from "lucide-react";
import { RankedSlot } from "@/types/task";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface ResultsModalProps {
  rankedSlots?: RankedSlot[];
  onConfirmSlot?: (slot: RankedSlot) => void;
  isSwarm: boolean;
  onCancel: () => void;
}

export function ResultsModal({
  rankedSlots,
  isSwarm,
  onConfirmSlot,
  onCancel,
}: ResultsModalProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/30 backdrop-blur-sm p-4"
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-card rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-auto"
      >
        <div className="flex items-center justify-between px-6 pt-5 pb-3">
          <h2 className="font-display text-lg font-bold text-foreground">
            {isSwarm ? "Best Options Found" : "Appointment Found"}
          </h2>
          <button onClick={onCancel} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 pb-6 space-y-3">
          {rankedSlots?.map((slot, i) => (
            <Card
              key={`${slot.provider_id}-${slot.slot}`}
              className={`transition-all ${i === 0 ? "ring-2 ring-accent shadow-md" : "opacity-80"}`}
            >
              <CardContent className="p-4 space-y-2">
                <div className="flex items-start justify-between">
                  <div>
                    {i === 0 && (
                      <span className="text-[10px] font-bold uppercase tracking-wider text-accent bg-accent/10 px-2 py-0.5 rounded-full">
                        Top Pick
                      </span>
                    )}
                    <h3 className="font-semibold text-foreground mt-1">
                      {slot.provider_name ?? slot.provider_id}
                    </h3>
                  </div>
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Trophy className="w-3.5 h-3.5" />
                    <span className="text-xs font-semibold">#{slot.rank}</span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(slot.slot).toLocaleString(undefined, {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </span>
                  <span className="flex items-center gap-1">
                    <Star className="w-3 h-3" />
                    Score: {slot.score.toFixed(1)}
                  </span>
                </div>
                {onConfirmSlot && (
                  <Button
                    onClick={() => onConfirmSlot(slot)}
                    className="w-full mt-2 bg-success text-success-foreground hover:bg-success/90"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    {isSwarm ? "Confirm appointment" : "Confirm & Add to Calendar"}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
