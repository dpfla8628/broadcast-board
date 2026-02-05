// why: 가격 및 할인율 표시 포맷을 일관되게 유지하기 위한 유틸
export function formatPrice(value?: number | null) {
  if (value === undefined || value === null) return "정보없음";
  return `${new Intl.NumberFormat("ko-KR").format(value)}원`;
}

export function formatDiscount(rate?: number | null) {
  if (rate === undefined || rate === null) return null;
  return `${rate.toFixed(1)}%`;
}
