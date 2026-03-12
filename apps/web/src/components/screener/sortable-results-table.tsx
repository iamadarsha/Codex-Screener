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
            <span className="font-mono font-semibold text-white">
              {row.original.symbol}
            </span>
            <div className="text-xs text-[#5C5D6E]">{row.original.name}</div>
          </div>
        ),
      },
      {
        accessorKey: "sector",
        header: "Sector",
        cell: ({ row }) => (
          <span className="text-xs text-[#8B8D9A]">{row.original.sector}</span>
        ),
      },
      {
        accessorKey: "ltp",
        header: "LTP",
        cell: ({ row }) => (
          <span className="font-mono text-white">
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
          <span className="font-mono text-[#8B8D9A]">
            {formatVolume(row.original.volume)}
          </span>
        ),
      },
      {
        accessorKey: "signal_strength",
        header: "Signal",
        cell: ({ row }) => {
          const strength = row.original.signal_strength;
          if (!strength) return <span className="text-[#5C5D6E]">-</span>;
          return (
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-[#1E1F28]">
                <div
                  className="h-full rounded-full bg-[#7C5CFC]"
                  style={{ width: `${Math.min(strength * 100, 100)}%` }}
                />
              </div>
              <span className="font-mono text-xs text-[#8B8D9A]">
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
