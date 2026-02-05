// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import type { Dayjs } from "dayjs";
import { toKst } from "../lib/time";
import { Broadcast } from "../types/broadcast";
import BroadcastCard from "./BroadcastCard";
import styles from "./BroadcastTimeline.module.css";

function groupByHour(broadcasts: Broadcast[]) {
  const groups: Record<string, Broadcast[]> = {};
  broadcasts.forEach((item) => {
    const key = toKst(item.start_at).format("HH:00");
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
  });
  return groups;
}

export default function BroadcastTimeline({
  broadcasts,
  channelLiveUrlMap,
  now,
}: {
  broadcasts: Broadcast[];
  channelLiveUrlMap?: Record<number, string>;
  now?: Dayjs;
}) {
  const groups = groupByHour(broadcasts);
  const hours = Object.keys(groups).sort();

  return (
    <div className={styles.timeline}>
      {hours.map((hour) => (
        <section key={hour} className={styles.group}>
          <div className={styles.hourLabel}>{hour}</div>
          <div className={styles.cards}>
            {groups[hour].map((item) => (
              <BroadcastCard
                key={item.id}
                broadcast={item}
                liveUrl={channelLiveUrlMap?.[item.channel_id]}
                now={now}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
