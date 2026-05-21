"use client";

import { GraduationCap, Sparkles } from "lucide-react";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useAppStore } from "@/lib/store";

export function ModeToggle() {
  const mode = useAppStore((s) => s.mode);
  const setMode = useAppStore((s) => s.setMode);
  const isExpert = mode === "expert";

  return (
    <div className="flex items-center gap-3 px-3 py-2 rounded-xl glass">
      <div className="flex items-center gap-1.5 text-xs">
        <Sparkles
          className={`h-3.5 w-3.5 transition-colors ${
            !isExpert ? "text-primary" : "text-muted-foreground/60"
          }`}
        />
        <span
          className={`font-medium transition-colors ${
            !isExpert ? "text-foreground" : "text-muted-foreground"
          }`}
        >
          Découverte
        </span>
      </div>
      <Switch
        id="mode-toggle"
        checked={isExpert}
        onCheckedChange={(checked) => setMode(checked ? "expert" : "simple")}
        aria-label="Basculer entre mode découverte et mode expert"
      />
      <Label
        htmlFor="mode-toggle"
        className="flex items-center gap-1.5 cursor-pointer text-xs"
      >
        <span
          className={`font-medium transition-colors ${
            isExpert ? "text-foreground" : "text-muted-foreground"
          }`}
        >
          Expert
        </span>
        <GraduationCap
          className={`h-3.5 w-3.5 transition-colors ${
            isExpert ? "text-primary" : "text-muted-foreground/60"
          }`}
        />
      </Label>
    </div>
  );
}
