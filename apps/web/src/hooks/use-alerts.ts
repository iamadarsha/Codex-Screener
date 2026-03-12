"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAlerts, createAlert } from "@/lib/api";
import { DEFAULT_USER_ID } from "@/lib/constants";
import type { AlertCreateRequest } from "@/lib/api-types";
import { toast } from "sonner";

export function useAlerts(userId: string = DEFAULT_USER_ID) {
  return useQuery({
    queryKey: ["alerts", userId],
    queryFn: () => fetchAlerts(userId),
  });
}

export function useCreateAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: AlertCreateRequest) => createAlert(req),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["alerts", variables.user_id] });
      toast.success("Alert created");
    },
    onError: () => {
      toast.error("Failed to create alert");
    },
  });
}
