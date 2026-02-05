// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { Modal, Form, Input, InputNumber, Select, Switch } from "antd";
import { useEffect } from "react";
import { Alert, AlertCreatePayload, AlertUpdatePayload } from "../types/alert";

const destinationOptions = [
  { value: "SLACK", label: "Slack" },
  { value: "EMAIL", label: "Email" },
];

function joinList(value?: string[] | null) {
  return value ? value.join(", ") : "";
}

function splitList(value?: string) {
  if (!value) return [];
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function AlertRuleFormModal({
  open,
  initialData,
  onCancel,
  onSubmit,
}: {
  open: boolean;
  initialData?: Alert | null;
  onCancel: () => void;
  onSubmit: (payload: AlertCreatePayload | AlertUpdatePayload) => void;
}) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (initialData) {
      form.setFieldsValue({
        alert_name: initialData.alert_name,
        target_channel_codes: joinList(initialData.target_channel_codes),
        keyword_list: joinList(initialData.keyword_list),
        category_list: joinList(initialData.category_list),
        notify_before_minutes: initialData.notify_before_minutes,
        destination_type: initialData.destination_type,
        destination_value: initialData.destination_value,
        is_active: initialData.is_active,
      });
    } else {
      form.resetFields();
    }
  }, [initialData, form]);

  return (
    <Modal
      title={initialData ? "알림 수정" : "알림 생성"}
      open={open}
      onCancel={onCancel}
      onOk={() => {
        form.validateFields().then((values) => {
          const payload = {
            ...values,
            target_channel_codes: splitList(values.target_channel_codes),
            keyword_list: splitList(values.keyword_list),
            category_list: splitList(values.category_list),
          };
          onSubmit(payload);
        });
      }}
    >
      <Form form={form} layout="vertical" initialValues={{ notify_before_minutes: 30, is_active: true }}>
        <Form.Item label="알림명" name="alert_name" rules={[{ required: true }]}>
          <Input placeholder="예: 야간 침구 알림" />
        </Form.Item>
        <Form.Item label="채널 코드" name="target_channel_codes" rules={[{ required: true }]}>
          <Input placeholder="cjon, hmall" />
        </Form.Item>
        <Form.Item label="키워드" name="keyword_list" rules={[{ required: true }]}>
          <Input placeholder="침구, 매트리스" />
        </Form.Item>
        <Form.Item label="카테고리" name="category_list">
          <Input placeholder="(선택) 리빙, 패션" />
        </Form.Item>
        <Form.Item label="알림 전(분)" name="notify_before_minutes">
          <InputNumber min={0} max={1440} style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item label="목적지" name="destination_type">
          <Select options={destinationOptions} />
        </Form.Item>
        <Form.Item label="웹훅/주소" name="destination_value" rules={[{ required: true }]}>
          <Input placeholder="Slack Webhook URL" />
        </Form.Item>
        <Form.Item label="활성" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  );
}
