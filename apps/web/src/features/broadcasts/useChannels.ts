// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../lib/apiClient";
import { queryKeys } from "../../lib/queryKeys";
import { Channel } from "../../types/channel";

export function useChannels() {
  return useQuery({
    queryKey: queryKeys.channels,
    queryFn: () => apiGet<Channel[]>("/api/v1/channels"),
  });
}
