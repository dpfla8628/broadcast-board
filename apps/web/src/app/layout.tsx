// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import type { ReactNode } from "react";
import "antd/dist/reset.css";
import "../styles/globals.css";
import Providers from "../lib/providers";

export const metadata = {
  title: "BroadcastBoard",
  description: "홈쇼핑 편성표 대시보드",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <Providers>
          <main>{children}</main>
        </Providers>
      </body>
    </html>
  );
}
