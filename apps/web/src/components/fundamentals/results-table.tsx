"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { type ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/data-table";
import { formatMarketCap } from "@/lib/format";
import type { FundamentalData } from "@/lib/api-types";

interface FundamentalsResultsTableProps {
  data: FundamentalData[];
  searchValue?: string;
}

export function FundamentalsResultsTable({
  data,
  searchValue,
}: FundamentalsResultsTableProps) {
  const router = useRouter();

  const columns = useMemo<ColumnDef<FundamentalData, unknown>[]>(
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
        accessorKey: "market_cap",
        header: "Market Cap",
        cell: ({ row }) => (
          <span className="font-mono text-white">
            {formatMarketCap(row.original.market_cap)}
          </span>
        ),
      },
      {
        accessorKey: "pe_ratio",
        header: "P/E",
        cell: ({ row }) => (
          <span className="font-mono text-[#8B8D9A]">
            {row.original.pe_ratio?.toFixed(1) ?? "-"}
          </span>
        ),
      },
      {
        accessorKey: "pb_ratio",
        header: "P/B",
        cell: ({ row }) => (
          <span className="font-mono text-[#8B8D9A]">
            {row.original.pb_ratio?.toFixed(2) ?? "-"}
          </span>
        ),
      },
      {
        accessorKey: "roe",
        header: "ROE %",
        cell: ({ row }) => (
          <span className="font-mono text-[#8B8D9A]">
            {row.original.roe?.toFixed(1) ?? "-"}
          </span>
        ),
      },
      {
        accessorKey: "dividend_yield",
        header: "Div Yield",
        cell: ({ row }) => (
          <span className="font-mono text-[#8B8D9A]">
            {row.original.dividend_yield?.toFixed(2) ?? "-"}%
          </span>
        ),
      },
      {
        accessorKey: "debt_to_equity",
        header: "D/E",
        cell: ({ row }) => (
          <span className="font-mono text-[#8B8D9A]">
            {row.original.debt_to_equity?.toFixed(2) ?? "-"}
          </span>
        ),
      },
      {
        accessorKey: "eps",
        header: "EPS",
        cell: ({ row }) => (
          <span className="font-mono text-[#8B8D9A]">
            {row.original.eps?.toFixed(2) ?? "-"}
          </span>
        ),
      },
    ],
    []
  );

  return (
    <DataTable
      data={data}
      columns={columns}
      searchValue={searchValue}
      searchColumn="symbol"
      onRowClick={(row) => router.push(`/chart/${row.symbol}`)}
    />
  );
}
