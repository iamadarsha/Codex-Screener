"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { type ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/data-table";
import { Badge } from "@/components/ui/badge";
import { formatPrice, formatPercent, formatVolume } from "@/lib/format";
import type { ScanResultItem } from "@/lib/api-types";

interface SortableResultsTableProps {
  items: ScanResultItem[];
}

export function SortableResultsTable({ items }: SortableResultsTableProps) {
  const router = useRouter();

  const columns = useMemo<ColumnDef<ScanResultItem, unknown>[]>(
    () => [
      {
        accessorKey: "symbol",
        header: "Symbol",
        cell: ({ row }) => (
          <div>
            <span className="font-mono font-semibold text-text-primary">
              {row.original.symbol}
            </span>
            <div className="text-xs text-text-muted">{row.original.company_name ?? row.original.name}</div>
          </div>
        ),
      },
      {
        accessorKey: "sector",
        header: "Sector",
        cell: ({ row }) => (
          <span className="text-xs text-text-secondary">{row.original.sector}</span>
        ),
      },
      {
        accessorKey: "ltp",
        header: "LTP",
        cell: ({ row }) => (
          <span className="font-mono text-text-primary">
            {formatPrice(row.original.ltp)}
          </span>
        ),
      },
      {
        accessorKey: "change_pct",
        header: "Change %",
        cell: ({ row }) => (
          <Badge
            variant={
              row.original.change_pct >= 0 ? "bullish" : "bearish"
            }
          >
            {formatPercent(row.original.change_pct)}
          </Badge>
        ),
      },
      {
        accessorKey: "volume",
        header: "Volume",
        cell: ({ row }) => (
          <span className="font-mono text-text-secondary">
            {formatVolume(row.original.volume)}
          </span>
        ),
      },
      {
        accessorKey: "signal_strength",
        header: "Signal",
        cell: ({ row }) => {
          const strength = row.original.signal_strength;
          if (!strength) return <span className="text-text-muted">-</span>;
          return (
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-border">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${Math.min(strength * 100, 100)}%` }}
                />
              </div>
              <span className="font-mono text-xs text-text-secondary">
                {(strength * 100).toFixed(0)}%
              </span>
            </div>
          );
        },
      },
    ],
    []
  );

  return (
    <DataTable
      data={items}
      columns={columns}
      onRowClick={(row) => router.push(`/chart/${row.symbol}`)}
    />
  );
}
