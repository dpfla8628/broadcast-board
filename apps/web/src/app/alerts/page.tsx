// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
"use client";

import { Button, message } from "antd";
import { useState } from "react";
import AlertRuleFormModal from "../../components/AlertRuleFormModal";
import AlertRuleTable from "../../components/AlertRuleTable";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import {
  useAlerts,
  useCreateAlert,
  useDeleteAlert,
  useUpdateAlert,
} from "../../features/alerts/useAlerts";
import { Alert } from "../../types/alert";
import styles from "./page.module.css";

export default function AlertsPage() {
  const { data, isLoading, isError } = useAlerts();
  const createMutation = useCreateAlert();
  const updateMutation = useUpdateAlert();
  const deleteMutation = useDeleteAlert();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<Alert | null>(null);

  const handleSubmit = async (payload: any) => {
    try {
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, payload });
        message.success("알림이 수정되었습니다.");
      } else {
        await createMutation.mutateAsync(payload);
        message.success("알림이 생성되었습니다.");
      }
      setIsModalOpen(false);
      setEditing(null);
    } catch {
      message.error("저장에 실패했습니다.");
    }
  };

  const handleDelete = async (alertId: number) => {
    try {
      await deleteMutation.mutateAsync(alertId);
      message.success("삭제되었습니다.");
    } catch {
      message.error("삭제에 실패했습니다.");
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>알림 규칙 관리</h1>
          <p className={styles.subtitle}>키워드와 채널 조건으로 알림을 설정합니다.</p>
        </div>
        <Button type="primary" onClick={() => setIsModalOpen(true)}>
          새 알림
        </Button>
      </header>

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {!isLoading && !isError && data && data.length === 0 && <EmptyState />}
      {!isLoading && !isError && data && data.length > 0 && (
        <AlertRuleTable
          alerts={data}
          onEdit={(alert) => {
            setEditing(alert);
            setIsModalOpen(true);
          }}
          onDelete={handleDelete}
        />
      )}

      <AlertRuleFormModal
        open={isModalOpen}
        initialData={editing}
        onCancel={() => {
          setIsModalOpen(false);
          setEditing(null);
        }}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
