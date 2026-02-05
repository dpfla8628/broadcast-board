// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiPatch, apiPost, apiGet } from "../../lib/apiClient";
import { queryKeys } from "../../lib/queryKeys";
import { Alert, AlertCreatePayload, AlertUpdatePayload } from "../../types/alert";

export function useAlerts() {
  return useQuery({
    queryKey: queryKeys.alerts,
    queryFn: () => apiGet<Alert[]>("/api/v1/alerts"),
  });
}

export function useCreateAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AlertCreatePayload) => apiPost<Alert, AlertCreatePayload>("/api/v1/alerts", payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.alerts }),
  });
}

export function useUpdateAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: AlertUpdatePayload }) =>
      apiPatch<Alert, AlertUpdatePayload>(`/api/v1/alerts/${id}`, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.alerts }),
  });
}

export function useDeleteAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiDelete<{ deleted: boolean }>(`/api/v1/alerts/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.alerts }),
  });
}
