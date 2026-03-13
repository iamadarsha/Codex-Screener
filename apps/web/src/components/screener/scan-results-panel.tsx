"use client";

import { X } from "lucide-react";
import { motion } from "framer-motion";
import { SortableResultsTable } from "./sortable-results-table";
import { Badge } from "@/components/ui/badge";
import type { ScanResult } from "@/lib/api-types";
import { formatTime } from "@/lib/format";

interface ScanResultsPanelProps {
  result: ScanResult;
  onClose: () => void;
}

export function ScanResultsPanel({ result, onClose }: ScanResultsPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="glass-card rounded-panel"
    >
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-text-primary">
            {result.scan_name}
          </h3>
          <Badge variant="accent">{result.total_matches} results</Badge>
          {result.is_demo && (
            <span className="rounded-full bg-warning/15 px-2 py-0.5 text-[10px] font-semibold text-warning">
              Demo Data
            </span>
          )}
          <span className="text-xs text-text-muted">
            {formatTime(result.run_at)}
          </span>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-text-secondary transition hover:bg-elevated hover:text-text-primary"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <SortableResultsTable items={result.items} />
    </motion.div>
  );
}
