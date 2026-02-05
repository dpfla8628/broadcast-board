// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export interface ResponseMeta {
  count?: number;
  message?: string;
  time_policy?: string;
}

export interface ApiResponse<T> {
  data: T;
  meta: ResponseMeta;
}
