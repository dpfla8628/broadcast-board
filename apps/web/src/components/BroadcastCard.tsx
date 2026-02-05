// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import type { Dayjs } from "dayjs";
import { toKst } from "../lib/time";
import { formatDiscount, formatPrice } from "../lib/format";
import { Broadcast } from "../types/broadcast";
import styles from "./BroadcastCard.module.css";

export default function BroadcastCard({
  broadcast,
  liveUrl,
  now,
}: {
  broadcast: Broadcast;
  liveUrl?: string;
  now?: Dayjs;
}) {
  const start = toKst(broadcast.start_at);
  const end = toKst(broadcast.end_at);
  const liveLink = broadcast.live_url || liveUrl;
  const computedStatus = now
    ? start.isAfter(now)
      ? "SCHEDULED"
      : end.isBefore(now)
        ? "ENDED"
        : "LIVE"
    : broadcast.status;

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.time}>
            {start.format("HH:mm")}
          </span>
          {broadcast.channel_name && (
            <span className={styles.channel}>{broadcast.channel_name}</span>
          )}
          {computedStatus === "LIVE" && liveLink ? (
            <a
              href={liveLink}
              target="_blank"
              rel="noopener noreferrer"
              className={`${styles.status} ${styles.statusLive} ${styles.statusLink}`}
              aria-label="라이브 TV 새 탭 열기"
              title="라이브 TV 새 탭 열기"
            >
              {computedStatus}
            </a>
          ) : null}
        </div>
        <div className={styles.actions}>
          {broadcast.product_url && (
            <a
              href={broadcast.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.linkButton}
              aria-label="상품 페이지 새 탭 열기"
              title="상품 페이지 새 탭 열기"
            >
              <svg viewBox="0 0 24 24" className={styles.linkIcon} aria-hidden="true">
                <path
                  d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3z"
                  fill="currentColor"
                />
                <path
                  d="M5 5h6v2H7v10h10v-4h2v6H5V5z"
                  fill="currentColor"
                />
              </svg>
            </a>
          )}
        </div>
      </div>
      <h3 className={styles.title}>{broadcast.raw_title}</h3>
      <div className={styles.meta}>
        {broadcast.original_price ? (
          <span className={styles.originalPrice}>
            정가 {formatPrice(broadcast.original_price)}
          </span>
        ) : null}
        <span className={styles.salePrice}>
          할인가{" "}
          {broadcast.sale_price !== null && broadcast.sale_price !== undefined
            ? formatPrice(broadcast.sale_price)
            : broadcast.price_text || "정보없음"}
        </span>
        {broadcast.discount_rate !== null && broadcast.discount_rate !== undefined && (
          <span className={styles.discountBadge}>
            정가대비 {formatDiscount(broadcast.discount_rate)} 할인
          </span>
        )}
      </div>
    </div>
  );
}
