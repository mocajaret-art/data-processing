import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Card, Descriptions, Tag, Typography, Table, Button, Timeline, Spin, Empty } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, ClockCircleOutlined, DownloadOutlined, ArrowLeftOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

const { Title } = Typography;

const statusMap = {
  PENDING: { color: "default", icon: <ClockCircleOutlined />, label: "等待中" },
  RUNNING: { color: "processing", icon: <SyncOutlined spin />, label: "运行中" },
  SUCCESS: { color: "success", icon: <CheckCircleOutlined />, label: "已完成" },
  FAILED: { color: "error", icon: <CloseCircleOutlined />, label: "失败" },
};

export default function TaskDetail() {
  const { id } = useParams();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchTask = useCallback(async () => {
    try {
      const { data } = await client.get(`/tasks/${id}`);
      setTask(data);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchTask();
    const interval = setInterval(() => {
      if (task && (task.status === "PENDING" || task.status === "RUNNING")) {
        fetchTask();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [fetchTask, task?.status]);

  const handleDownload = async () => {
    const { data } = await client.get(`/tasks/${id}/result`);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `结果-${id.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <Spin size="large" style={{ display: "block", marginTop: 100 }} />;
  if (!task) return <Empty description="未找到任务" />;

  const st = statusMap[task.status] || statusMap.PENDING;

  return (
    <>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/")} style={{ marginBottom: 16 }}>
        返回
      </Button>
      <Card>
        <Title level={3}>
          任务详情 <Tag color={st.color} icon={st.icon}>{st.label}</Tag>
        </Title>
        <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
          <Descriptions.Item label="任务 ID">{task.id}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={st.color}>{st.label}</Tag></Descriptions.Item>
          <Descriptions.Item label="文件名">{task.file?.original_filename || "N/A"}</Descriptions.Item>
          <Descriptions.Item label="文件类型">{task.file?.file_type || "N/A"}</Descriptions.Item>
          <Descriptions.Item label="重试次数">{task.retry_count}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(task.created_at).toLocaleString()}</Descriptions.Item>
          {task.completed_at && (
            <Descriptions.Item label="完成时间">{new Date(task.completed_at).toLocaleString()}</Descriptions.Item>
          )}
        </Descriptions>

        {task.error_message && (
          <Card title="错误信息" style={{ marginBottom: 24, borderColor: "#ff4d4f" }}>
            <Typography.Text type="danger">{task.error_message}</Typography.Text>
          </Card>
        )}

        {task.result_data && (
          <>
            <Card title="分析结果" style={{ marginBottom: 24 }}>
              <Descriptions bordered column={3} size="small">
                <Descriptions.Item label="数据行数">{task.result_data.row_count}</Descriptions.Item>
                <Descriptions.Item label="列数">{task.result_data.column_count}</Descriptions.Item>
                <Descriptions.Item label="列名">{task.result_data.columns?.join(", ")}</Descriptions.Item>
              </Descriptions>

              {task.result_data.missing_values && Object.keys(task.result_data.missing_values).length > 0 && (
                <>
                  <Title level={5} style={{ marginTop: 16 }}>缺失值统计</Title>
                  <Descriptions bordered column={2} size="small">
                    {Object.entries(task.result_data.missing_values).map(([col, count]) => (
                      <Descriptions.Item key={col} label={col}>{count}</Descriptions.Item>
                    ))}
                  </Descriptions>
                </>
              )}

              {task.result_data.numeric_stats && Object.keys(task.result_data.numeric_stats).length > 0 && (
                <>
                  <Title level={5} style={{ marginTop: 16 }}>数值统计</Title>
                  {Object.entries(task.result_data.numeric_stats).map(([col, stats]) => (
                    <Descriptions key={col} bordered column={4} size="small" style={{ marginBottom: 8 }}>
                      <Descriptions.Item label="列名">{col}</Descriptions.Item>
                      <Descriptions.Item label="平均值">{stats.mean}</Descriptions.Item>
                      <Descriptions.Item label="标准差">{stats.std}</Descriptions.Item>
                      <Descriptions.Item label="范围">[{stats.min}, {stats.max}]</Descriptions.Item>
                    </Descriptions>
                  ))}
                </>
              )}

              {task.result_data.top_values && Object.keys(task.result_data.top_values).length > 0 && (
                <>
                  <Title level={5} style={{ marginTop: 16 }}>高频值统计</Title>
                  {Object.entries(task.result_data.top_values).map(([col, values]) => (
                    <Card key={col} size="small" title={col} style={{ marginBottom: 8 }}>
                      <Table
                        dataSource={values}
                        columns={[
                          { title: "值", dataIndex: "value", key: "value" },
                          { title: "出现次数", dataIndex: "count", key: "count" },
                        ]}
                        rowKey="value"
                        pagination={false}
                        size="small"
                      />
                    </Card>
                  ))}
                </>
              )}
            </Card>
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload} size="large">
              下载结果 JSON
            </Button>
          </>
        )}
      </Card>
    </>
  );
}
