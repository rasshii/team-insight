"use client";

import { cn } from "@/lib/utils";
import { Period } from "@/types/period";

interface FilterBarProps {
  selectedPeriod: Period;
  onPeriodChange: (period: Period) => void;
}

export function FilterBar({ selectedPeriod, onPeriodChange }: FilterBarProps) {
  const periods: Period[] = ["今月", "先月", "過去3ヶ月"];

  return (
    <div className="flex space-x-2">
      {periods.map((period) => (
        <button
          key={period}
          onClick={() => onPeriodChange(period)}
          className={cn(
            "px-4 py-2 rounded-md text-sm font-medium transition-colors",
            selectedPeriod === period
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          {period}
        </button>
      ))}
    </div>
  );
}
