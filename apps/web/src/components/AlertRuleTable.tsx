// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { Table, Button, Space, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { Alert } from "../types/alert";

export default function AlertRuleTable({
  alerts,
  onEdit,
  onDelete,
}: {
  alerts: Alert[];
  onEdit: (alert: Alert) => void;
  onDelete: (alertId: number) => void;
}) {
  const columns: ColumnsType<Alert> = [
    {
      title: "알림명",
      dataIndex: "alert_name",
    },
    {
      title: "채널",
      dataIndex: "target_channel_codes",
      render: (codes: string[]) => (
        <Space wrap>
          {codes.map((code) => (
            <Tag key={code}>{code}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: "키워드",
      dataIndex: "keyword_list",
      render: (keywords: string[]) => keywords.join(", "),
    },
    {
      title: "알림 전(분)",
      dataIndex: "notify_before_minutes",
    },
    {
      title: "상태",
      dataIndex: "is_active",
      render: (active: boolean) => (active ? "활성" : "비활성"),
    },
    {
      title: "액션",
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => onEdit(record)}>
            수정
          </Button>
          <Button danger size="small" onClick={() => onDelete(record.id)}>
            삭제
          </Button>
        </Space>
      ),
    },
  ];

  return <Table rowKey="id" columns={columns} dataSource={alerts} pagination={false} />;
}
