// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import styles from "./State.module.css";

export default function EmptyState({
  title = "데이터가 없습니다",
  description = "조건을 변경해 다시 확인해 주세요.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className={styles.stateBox}>
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}
