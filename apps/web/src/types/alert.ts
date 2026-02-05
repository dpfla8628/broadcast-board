// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export type DestinationType = "SLACK" | "EMAIL";

export interface Alert {
  id: number;
  alert_name: string;
  target_channel_codes: string[];
  keyword_list: string[];
  category_list?: string[] | null;
  notify_before_minutes: number;
  destination_type: DestinationType;
  destination_value: string;
  is_active: boolean;
}

export interface AlertCreatePayload {
  alert_name: string;
  target_channel_codes: string[];
  keyword_list: string[];
  category_list?: string[] | null;
  notify_before_minutes: number;
  destination_type: DestinationType;
  destination_value: string;
  is_active: boolean;
}

export type AlertUpdatePayload = Partial<AlertCreatePayload>;
