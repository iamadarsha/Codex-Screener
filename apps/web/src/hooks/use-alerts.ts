"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAlerts, createAlert } from "@/lib/api";
import type { AlertCreateRequest } from "@/lib/api-types";
import { toast } from "sonner";

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: () => fetchAlerts(),
  });
}

export function useCreateAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: AlertCreateRequest) => createAlert(req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      toast.success("Alert created");
    },
    onError: () => {
      toast.error("Failed to create alert");
    },
  });
}
