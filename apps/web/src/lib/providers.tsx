// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
"use client";

import { PropsWithChildren, createContext, useEffect, useMemo, useState } from "react";
import { ConfigProvider, theme } from "antd";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

type ThemeMode = "light" | "dark";

export const ThemeContext = createContext({
  themeMode: "light" as ThemeMode,
  toggleTheme: () => {},
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,
      retry: 1,
    },
  },
});

export default function Providers({ children }: PropsWithChildren) {
  const [themeMode, setThemeMode] = useState<ThemeMode>("light");

  useEffect(() => {
    const stored = window.localStorage.getItem("themeMode");
    if (stored === "dark" || stored === "light") {
      setThemeMode(stored);
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode;
    window.localStorage.setItem("themeMode", themeMode);
  }, [themeMode]);

  const toggleTheme = () => {
    setThemeMode((prev) => (prev === "light" ? "dark" : "light"));
  };

  const antdTheme = useMemo(
    () => ({
      algorithm: themeMode === "dark" ? theme.darkAlgorithm : theme.defaultAlgorithm,
      token: {
        colorPrimary: themeMode === "dark" ? "#38bdf8" : "#2563eb",
        borderRadius: 10,
      },
    }),
    [themeMode]
  );

  return (
    <ThemeContext.Provider value={{ themeMode, toggleTheme }}>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider theme={antdTheme}>{children}</ConfigProvider>
      </QueryClientProvider>
    </ThemeContext.Provider>
  );
}
