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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="rounded-panel border border-border bg-card"
    >
      <div className="flex items-center justify-between border-b border-[#1E1F28] px-5 py-3">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-white">
            {result.scan_name}
          </h3>
          <Badge variant="accent">{result.total_matches} results</Badge>
          {result.run_at && (
            <span className="text-xs text-[#5C5D6E]">
              {formatTime(result.run_at)}
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-[#8B8D9A] transition hover:bg-[#22232D] hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <SortableResultsTable items={result.items ?? []} />
    </motion.div>
  );
}
