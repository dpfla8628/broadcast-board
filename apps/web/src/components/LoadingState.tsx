// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { Spin } from "antd";
import styles from "./State.module.css";

export default function LoadingState({ label = "로딩 중입니다" }: { label?: string }) {
  return (
    <div className={styles.stateBox}>
      <Spin size="large" />
      <p>{label}</p>
    </div>
  );
}
