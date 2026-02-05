// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export const queryKeys = {
  channels: ["channels"] as const,
  broadcasts: (params: Record<string, string | undefined>) =>
    ["broadcasts", params] as const,
  broadcastDetail: (id: string | number) => ["broadcast", id] as const,
  alerts: ["alerts"] as const,
};
