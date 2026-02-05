// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
"use client";

import { DatePicker, Input, Select } from "antd";
import { dayjs, nowKst, toKst } from "../lib/time";
import { useEffect, useMemo, useState } from "react";
import BroadcastTimeline from "../components/BroadcastTimeline";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import UpcomingBroadcastList from "../components/UpcomingBroadcastList";
import ThemeToggle from "../components/ThemeToggle";
import { useBroadcasts } from "../features/broadcasts/useBroadcasts";
import { useChannels } from "../features/broadcasts/useChannels";
import styles from "./page.module.css";

export default function HomePage() {
  const [selectedDate, setSelectedDate] = useState(() => nowKst());
  const [channelCode, setChannelCode] = useState<string | undefined>();
  const [keyword, setKeyword] = useState<string | undefined>();
  const [categories, setCategories] = useState<string[]>([]);

  const { data: channels } = useChannels();
  const channelLiveUrlMap = useMemo(() => {
    const map: Record<number, string> = {};
    (channels ?? []).forEach((channel) => {
      if (channel.channel_live_url) {
        map[channel.id] = channel.channel_live_url;
      }
    });
    return map;
  }, [channels]);


  const queryParams = useMemo(
    () => ({
      date: selectedDate.format("YYYY-MM-DD"),
      channelCode,
      keyword,
      category: categories.length > 0 ? categories.join(",") : undefined,
    }),
    [selectedDate, channelCode, keyword, categories]
  );

  const today = nowKst().startOf("day");
  const tomorrow = today.add(1, "day");
  const disabledDate = (current: dayjs.Dayjs | null) => {
    if (!current) return false;
    const target = current.startOf("day");
    return target.isBefore(today) || target.isAfter(tomorrow);
  };

  const { data, isLoading, isError, refetch } = useBroadcasts(queryParams);
  const [now, setNow] = useState(() => nowKst());
  const liveDate = now.format("YYYY-MM-DD");
  const liveQueryParams = useMemo(
    () => ({
      date: liveDate,
    }),
    [liveDate]
  );
  const { data: liveData, refetch: refetchLive } = useBroadcasts(liveQueryParams);

  // 1분 단위로 현재 시간을 갱신하고, 정각에만 데이터 리프레시
  useEffect(() => {
    const tick = () => {
      const current = nowKst();
      setNow(current);
      if (current.minute() === 0) {
        refetch();
        refetchLive();
      }
    };

    tick();
    const interval = setInterval(tick, 60 * 1000);
    return () => clearInterval(interval);
  }, [refetch, refetchLive]);

  const broadcastList = data ?? [];
  const liveBroadcasts = (liveData ?? []).filter((item) => {
    const start = toKst(item.start_at);
    const end = toKst(item.end_at);
    return start.isBefore(now) && end.isAfter(now);
  });
  const upcomingBroadcasts = broadcastList.filter((item) => {
    const start = toKst(item.start_at);
    return start.isAfter(now);
  });
  const pastBroadcasts = broadcastList.filter((item) => {
    const end = toKst(item.end_at);
    return end.isBefore(now);
  });
  const timelineBroadcasts = [...liveBroadcasts, ...upcomingBroadcasts];
  const [showPast, setShowPast] = useState(false);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>오늘/내일 홈쇼핑 편성표</h1>
          <p className={styles.subtitle}>지금 진행중인 방송과 예정 방송을 한눈에 확인하세요.</p>
        </div>
        <ThemeToggle />
      </header>

      <section className={styles.categoryFilter}>
        <span className={styles.filterLabel}>카테고리</span>
        <div className={styles.categoryButtons}>
          {[
            "식품",
            "의류",
            "리빙",
            "가전",
            "뷰티",
            "건강",
            "패션잡화",
            "기타",
          ].map((item) => {
            const active = categories.includes(item);
            return (
              <button
                key={item}
                type="button"
                className={`${styles.categoryButton} ${
                  active ? styles.categoryButtonActive : ""
                }`}
                onClick={() =>
                  setCategories((prev) =>
                    prev.includes(item)
                      ? prev.filter((value) => value !== item)
                      : [...prev, item]
                  )
                }
              >
                {item}
              </button>
            );
          })}
        </div>
      </section>

      <section className={styles.filtersRow}>
        <DatePicker
          value={selectedDate}
          onChange={(value) => value && setSelectedDate(value)}
          allowClear={false}
          disabledDate={disabledDate}
        />
        <Select
          placeholder="채널 선택"
          allowClear
          options={[
            { value: "", label: "전체" },
            ...(channels?.map((channel) => ({
              value: channel.channel_code,
              label: channel.channel_name,
            })) ?? []),
          ]}
          onChange={(value) => setChannelCode(value ? value : undefined)}
          className={styles.select}
        />
        <Input.Search
          placeholder="키워드 검색"
          onSearch={(value) => setKeyword(value || undefined)}
          className={styles.search}
        />
      </section>

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {!isLoading && !isError && data && data.length === 0 && <EmptyState />}

      {!isLoading && !isError && broadcastList.length > 0 && (
        <div className={styles.content}>
          <div className={styles.timelineWrap}>
            {pastBroadcasts.length > 0 && (
              <section className={styles.pastSection}>
                <button
                  type="button"
                  className={styles.pastToggle}
                  onClick={() => setShowPast((prev) => !prev)}
                >
                  이전 방송 {showPast ? "숨기기" : "보기"}
                </button>
                {showPast && (
                  <div className={styles.pastList}>
                    {pastBroadcasts.map((item) => (
                      <div key={item.id} className={styles.pastItem}>
                        <span>{toKst(item.start_at).format("HH:mm")}</span>
                        <span className={styles.pastText}>{item.raw_title}</span>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}
            <BroadcastTimeline
              broadcasts={timelineBroadcasts}
              channelLiveUrlMap={channelLiveUrlMap}
              now={now}
            />
          </div>
          <UpcomingBroadcastList
            broadcasts={liveBroadcasts}
            title="현재 방송"
            emptyText="현재 진행중인 방송이 없습니다."
          />
        </div>
      )}
    </div>
  );
}
