"use client";

import { Play, SkipBack, SkipForward } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { useAppStore } from "@/lib/store";

export function PlaybackControl() {
  const isSimulating = useAppStore((s) => s.isSimulating);
  const totalGen = useAppStore((s) => s.totalGen);
  const viewGen = useAppStore((s) => s.viewGen);
  const setViewGen = useAppStore((s) => s.setViewGen);
  const mode = useAppStore((s) => s.mode);

  if (isSimulating || totalGen === 0) return null;

  const currentValue = viewGen ?? totalGen;
  const isFollowingLatest = viewGen === null || viewGen === totalGen;

  return (
    <div className="mt-4 p-3 rounded-lg glass space-y-3">
      <div className="flex items-center justify-between text-xs">
        <Label className="text-muted-foreground">
          {mode === "simple"
            ? "Rejouer la recherche"
            : "Replay des générations"}
        </Label>
        <span className="font-mono text-foreground font-medium">
          {mode === "simple" ? "Étape" : "Génération"} {currentValue} /{" "}
          {totalGen}
          {isFollowingLatest && (
            <span className="ml-2 text-[10px] uppercase text-primary">
              final
            </span>
          )}
        </span>
      </div>

      <Slider
        min={1}
        max={totalGen}
        step={1}
        value={[currentValue]}
        onValueChange={(v) => {
          const g = v[0];
          setViewGen(g >= totalGen ? null : g);
        }}
      />

      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setViewGen(1)}
          className="h-7 px-2 text-xs"
        >
          <SkipBack className="h-3 w-3 mr-1" />
          Début
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setViewGen(Math.max(1, currentValue - 1))}
          disabled={currentValue <= 1}
          className="h-7 px-2 text-xs"
        >
          ◀
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            const next = currentValue + 1;
            setViewGen(next >= totalGen ? null : next);
          }}
          disabled={currentValue >= totalGen}
          className="h-7 px-2 text-xs"
        >
          ▶
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setViewGen(null)}
          className="h-7 px-2 text-xs"
        >
          <SkipForward className="h-3 w-3 mr-1" />
          Final
        </Button>
        <div className="flex-1" />
        <Button
          size="sm"
          variant="ghost"
          onClick={async () => {
            for (let g = 1; g <= totalGen; g++) {
              setViewGen(g === totalGen ? null : g);
              await new Promise((r) => setTimeout(r, 120));
            }
          }}
          className="h-7 px-2 text-xs"
        >
          <Play className="h-3 w-3 mr-1" />
          {mode === "simple" ? "Rejouer" : "Auto-play"}
        </Button>
      </div>
    </div>
  );
}
