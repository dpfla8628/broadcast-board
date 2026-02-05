// why: 라이트/다크 모드를 사용자가 전환할 수 있도록 제공하는 UI
import { Switch } from "antd";
import { useContext } from "react";
import { ThemeContext } from "../lib/providers";
import styles from "./ThemeToggle.module.css";

export default function ThemeToggle() {
  const { themeMode, toggleTheme } = useContext(ThemeContext);
  const isDark = themeMode === "dark";

  return (
    <div className={styles.toggle}>
      <span className={styles.label}>테마</span>
      <Switch
        checked={isDark}
        onChange={toggleTheme}
        checkedChildren="다크"
        unCheckedChildren="라이트"
      />
    </div>
  );
}
