// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import styles from "./State.module.css";

export default function ErrorState({
  title = "오류가 발생했습니다",
  description = "잠시 후 다시 시도해 주세요.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className={styles.stateBox}>
      <strong className={styles.error}>{title}</strong>
      <p>{description}</p>
    </div>
  );
}
