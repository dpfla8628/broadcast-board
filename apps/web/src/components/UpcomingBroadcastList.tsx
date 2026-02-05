// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { toKst } from "../lib/time";
import { Broadcast } from "../types/broadcast";
import styles from "./UpcomingBroadcastList.module.css";

export default function UpcomingBroadcastList({
  broadcasts,
  title = "현재 방송",
  emptyText = "현재 진행중인 방송이 없습니다.",
  limit = 5,
}: {
  broadcasts: Broadcast[];
  title?: string;
  emptyText?: string;
  limit?: number;
}) {
  const list = broadcasts.slice(0, limit);

  return (
    <div className={styles.box}>
      <h4 className={styles.title}>{title}</h4>
      {list.length === 0 ? (
        <p className={styles.empty}>{emptyText}</p>
      ) : (
      <ul className={styles.list}>
        {list.map((item) => (
          <li key={item.id} className={styles.item}>
            <span>{toKst(item.start_at).format("HH:mm")}</span>
            <span className={styles.text}>{item.raw_title}</span>
          </li>
        ))}
      </ul>
      )}
    </div>
  );
}
