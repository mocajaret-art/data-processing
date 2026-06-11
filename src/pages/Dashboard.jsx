import { useState, useEffect, useCallback } from "react";
import { Card, Statistic, Table, Tag, Typography, message } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, ClockCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

const { Title } = Typography;

const statusMap = {
  PENDING: { color: "default", icon: <ClockCircleOutlined />, label: "等待中" },
  RUNNING: { color: "processing", icon: <SyncOutlined spin />, label: "运行中" },
  SUCCESS: { color: "success", icon: <CheckCircleOutlined />, label: "已完成" },
  FAILED: { color: "error", icon: <CloseCircleOutlined />, label: "失败" },
};

export default function Dashboard() {
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({ total: 0, pending: 0, running: 0, success: 0, failed: 0 });
  const navigate = useNavigate();

  const fetchTasks = useCallback(async () => {
    try {
      const { data } = await client.get("/tasks/");
      const items = data.items || [];
      setTasks(items);
      setStats({
        total: items.length,
        pending: items.filter((t) => t.status === "PENDING").length,
        running: items.filter((t) => t.status === "RUNNING").length,
        success: items.filter((t) => t.status === "SUCCESS").length,
        failed: items.filter((t) => t.status === "FAILED").length,
      });
    } catch {
      // 错误已在拦截器处理
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  const columns = [
    {
      title: "任务 ID",
      dataIndex: "id",
      key: "id",
      render: (id) => id.slice(0, 8) + "...",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (s) => {
        const info = statusMap[s] || statusMap.PENDING;
        return <Tag color={info.color} icon={info.icon}>{info.label}</Tag>;
      },
    },
    {
      title: "重试次数",
      dataIndex: "retry_count",
      key: "retry_count",
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (t) => new Date(t).toLocaleString(),
    },
  ];

  return (
    <>
      <Title level={3}>仪表盘</Title>
      <div className="dashboard-cards">
        <Card><Statistic title="总任务数" value={stats.total} /></Card>
        <Card><Statistic title="已完成" value={stats.success} valueStyle={{ color: "#52c41a" }} prefix={<CheckCircleOutlined />} /></Card>
        <Card><Statistic title="失败" value={stats.failed} valueStyle={{ color: "#ff4d4f" }} prefix={<CloseCircleOutlined />} /></Card>
        <Card><Statistic title="运行中" value={stats.running} valueStyle={{ color: "#1677ff" }} prefix={<SyncOutlined spin />} /></Card>
      </div>
      <Card title="最近任务">
        <Table
          dataSource={tasks}
          columns={columns}
          rowKey="id"
          onRow={(record) => ({
            onClick: () => navigate(`/tasks/${record.id}`),
            style: { cursor: "pointer" },
          })}
          pagination={false}
        />
      </Card>
    </>
  );
}
