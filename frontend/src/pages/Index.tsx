import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Phone, Users, ChevronDown, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { TaskMode, TaskUrgency, PreferenceWeights } from "@/types/task";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

const Index = () => {
  const navigate = useNavigate();
  const [description, setDescription] = useState("");
  const [mode, setMode] = useState<TaskMode>("single");
  const [urgency, setUrgency] = useState<TaskUrgency>("asap");
  const [optionsOpen, setOptionsOpen] = useState(false);
  const [preferences, setPreferences] = useState<PreferenceWeights>({
    availability_weight: 0.5,
    rating_weight: 0.3,
    distance_weight: 0.2,
  });

  const updateWeight = (key: keyof PreferenceWeights, value: number) => {
    setPreferences((prev) => ({ ...prev, [key]: Math.round(value * 100) / 100 }));
  };

  const handleStart = () => {
    if (!description.trim()) return;
    navigate("/agent", {
      state: { description, mode, urgency, preferences },
    });
  };

  return (
    <div className="min-h-screen bg-background flex flex-col relative overflow-hidden">
      <div className="absolute inset-0 bg-dot-pattern opacity-40 pointer-events-none" />
      <div className="gradient-orb gradient-orb-primary w-[600px] h-[600px] -top-40 left-1/2 -translate-x-1/2" />
      <div className="gradient-orb gradient-orb-accent w-[400px] h-[400px] top-1/3 -right-32" />
      <div className="gradient-orb gradient-orb-accent w-[300px] h-[300px] bottom-20 -left-20 opacity-60" />

      <nav className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-border/50 glass-header">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
            <Phone className="w-4 h-4 text-accent-foreground" />
          </div>
          <span className="font-display text-xl font-bold text-foreground">BookLine</span>
        </div>
        <Button variant="outline" size="sm" className="text-muted-foreground">
          Sign in with Google
        </Button>
      </nav>

      <main className="relative z-10 flex-1 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-2xl space-y-8"
        >
          <div className="text-center space-y-3">
            <h1 className="text-4xl md:text-5xl font-display font-bold text-foreground tracking-tight">
              Your AI scheduling assistant
            </h1>
            <p className="text-lg text-muted-foreground max-w-md mx-auto">
              Describe what you need — BookLine calls providers, negotiates times, and books for you.
            </p>
          </div>

          <div className="space-y-4">
            <Textarea
              placeholder="e.g. Book me a dental cleaning appointment this week near downtown…"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="min-h-[120px] text-base resize-none bg-card/80 backdrop-blur-sm border-border/60 focus:border-accent shadow-sm"
            />

            <div className="grid grid-cols-2 gap-3">
              <ModeCard
                selected={mode === "single"}
                onClick={() => setMode("single")}
                icon={<Phone className="w-5 h-5" />}
                title="Single Call"
                desc="One provider at a time"
              />
              <ModeCard
                selected={mode === "swarm"}
                onClick={() => setMode("swarm")}
                icon={<Users className="w-5 h-5" />}
                title="Swarm Mode"
                desc="Call multiple in parallel"
              />
            </div>

            <Collapsible open={optionsOpen} onOpenChange={setOptionsOpen}>
              <CollapsibleTrigger asChild>
                <button className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mx-auto">
                  <ChevronDown className={`w-4 h-4 transition-transform ${optionsOpen ? "rotate-180" : ""}`} />
                  More options
                </button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-3 space-y-5">
                <div className="flex gap-2 justify-center">
                  {(["asap", "flexible", "specific"] as TaskUrgency[]).map((u) => (
                    <Button
                      key={u}
                      variant={urgency === u ? "default" : "outline"}
                      size="sm"
                      onClick={() => setUrgency(u)}
                      className="capitalize"
                    >
                      {u === "asap" ? "ASAP" : u}
                    </Button>
                  ))}
                </div>

                <div className="space-y-3 bg-card/80 backdrop-blur-sm border border-border rounded-xl p-4">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Preference Weights</p>
                  <WeightSlider
                    label="Availability"
                    value={preferences.availability_weight}
                    onChange={(v) => updateWeight("availability_weight", v)}
                  />
                  <WeightSlider
                    label="Rating"
                    value={preferences.rating_weight}
                    onChange={(v) => updateWeight("rating_weight", v)}
                  />
                  <WeightSlider
                    label="Distance"
                    value={preferences.distance_weight}
                    onChange={(v) => updateWeight("distance_weight", v)}
                  />
                </div>
              </CollapsibleContent>
            </Collapsible>

            <Button
              onClick={handleStart}
              disabled={!description.trim()}
              className="w-full h-12 text-base font-semibold bg-accent text-accent-foreground hover:bg-accent/90 shadow-lg shadow-accent/25 transition-shadow hover:shadow-xl hover:shadow-accent/30"
            >
              <Zap className="w-5 h-5 mr-2" />
              Start Scheduling
            </Button>
          </div>
        </motion.div>
      </main>
    </div>
  );
};

function WeightSlider({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between">
        <Label className="text-xs text-muted-foreground">{label}</Label>
        <span className="text-xs font-mono text-muted-foreground">{value.toFixed(2)}</span>
      </div>
      <Slider
        min={0}
        max={1}
        step={0.05}
        value={[value]}
        onValueChange={([v]) => onChange(v)}
      />
    </div>
  );
}

function ModeCard({
  selected,
  onClick,
  icon,
  title,
  desc,
}: {
  selected: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-3 p-4 rounded-xl border-2 text-left transition-all ${
        selected
          ? "border-accent bg-accent/5 card-glow-selected"
          : "border-border bg-card/80 backdrop-blur-sm hover:border-accent/40"
      }`}
    >
      <div className={`${selected ? "text-accent" : "text-muted-foreground"}`}>{icon}</div>
      <div>
        <p className="font-semibold text-sm text-foreground">{title}</p>
        <p className="text-xs text-muted-foreground">{desc}</p>
      </div>
    </button>
  );
}

export default Index;
