// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export interface Channel {
  id: number;
  channel_code: string;
  channel_name: string;
  channel_logo_url?: string | null;
  channel_live_url?: string | null;
  channel_stream_url?: string | null;
}
