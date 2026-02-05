// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export type BroadcastStatus = "SCHEDULED" | "LIVE" | "ENDED";

export interface Broadcast {
  id: number;
  channel_id: number;
  channel_code?: string | null;
  channel_name?: string | null;
  source_code: string;
  start_at: string;
  end_at: string;
  raw_title: string;
  normalized_title: string;
  category?: string | null;
  product_url?: string | null;
  live_url?: string | null;
  sale_price?: number | null;
  original_price?: number | null;
  discount_rate?: number | null;
  price_text?: string | null;
  image_url?: string | null;
  status: BroadcastStatus;
  slot_hash: string;
}
