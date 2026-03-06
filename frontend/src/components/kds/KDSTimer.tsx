"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface KDSTimerProps {
  startTime: string;
  warningAfterMinutes?: number;
  criticalAfterMinutes?: number;
}

export function KDSTimer({
  startTime,
  warningAfterMinutes = 10,
  criticalAfterMinutes = 15,
}: KDSTimerProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = new Date(startTime).getTime();
    const tick = () => setElapsed(Math.floor((Date.now() - start) / 1000));
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  const display = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  const isCritical = minutes >= criticalAfterMinutes;
  const isWarning = minutes >= warningAfterMinutes && !isCritical;

  return (
    <span
      className={cn(
        "font-mono font-semibold tabular-nums",
        isCritical && "text-danger animate-pulse",
        isWarning && "text-warning",
        !isWarning && !isCritical && "text-muted",
      )}
    >
      {display}
    </span>
  );
}
