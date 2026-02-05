// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
"use client";

import { nowKst, toKst } from "../../lib/time";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import LoadingState from "../../components/LoadingState";
import ErrorState from "../../components/ErrorState";
import { useBroadcasts } from "../../features/broadcasts/useBroadcasts";
import styles from "./page.module.css";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function buildHourlyCounts(times: string[]) {
  const counts = new Array(24).fill(0);
  times.forEach((time) => {
    const hour = toKst(time).hour();
    counts[hour] += 1;
  });
  return counts;
}

export default function TrendsPage() {
  const today = nowKst().format("YYYY-MM-DD");
  const { data, isLoading, isError } = useBroadcasts({ date: today });

  if (isLoading) return <LoadingState />;
  if (isError || !data) return <ErrorState />;

  const labels = Array.from({ length: 24 }, (_, idx) => `${idx}:00`);
  const counts = buildHourlyCounts(data.map((item) => item.start_at));

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>방송 트렌드</h1>
        <p className={styles.subtitle}>시간대별 방송 개수 (KST 기준)</p>
      </header>
      <div className={styles.chartBox}>
        <Bar
          data={{
            labels,
            datasets: [
              {
                label: "편성 슬롯",
                data: counts,
                backgroundColor: "rgba(56, 189, 248, 0.6)",
              },
            ],
          }}
          options={{
            responsive: true,
            plugins: {
              legend: { position: "top" as const },
              title: { display: false },
            },
          }}
        />
      </div>
    </div>
  );
}
