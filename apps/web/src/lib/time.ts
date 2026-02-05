// why: API가 UTC로 내려주는 시간을 KST로 일관되게 표시하기 위한 공통 유틸
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";

dayjs.extend(utc);
dayjs.extend(timezone);

export const DEFAULT_TIMEZONE = "Asia/Seoul";

// 전역 기본 시간대를 KST로 고정 (UI 표시 기준)
dayjs.tz.setDefault(DEFAULT_TIMEZONE);

export { dayjs };

export function toKst(dateString: string) {
  // API는 UTC 기준이므로, 무조건 UTC로 파싱 후 KST로 변환
  return dayjs.utc(dateString).tz(DEFAULT_TIMEZONE);
}

export function nowKst() {
  // 로컬 타임존에 영향받지 않고 KST 기준 현재 시간을 고정
  return dayjs().tz(DEFAULT_TIMEZONE);
}
