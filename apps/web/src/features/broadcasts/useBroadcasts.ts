// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../lib/apiClient";
import { queryKeys } from "../../lib/queryKeys";
import { Broadcast } from "../../types/broadcast";

export interface BroadcastQueryParams {
  date?: string;
  channelCode?: string;
  keyword?: string;
  category?: string;
  status?: string;
}

export function useBroadcasts(params: BroadcastQueryParams) {
  return useQuery({
    queryKey: queryKeys.broadcasts(params),
    queryFn: () => {
      const query = new URLSearchParams();
      if (params.date) query.append("date", params.date);
      if (params.channelCode) query.append("channelCode", params.channelCode);
      if (params.keyword) query.append("keyword", params.keyword);
      if (params.category) query.append("category", params.category);
      if (params.status) query.append("status", params.status);

      const queryString = query.toString();
      return apiGet<Broadcast[]>(`/api/v1/broadcasts${queryString ? `?${queryString}` : ""}`);
    },
  });
}
