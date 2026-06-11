import { useState } from "react";
import { Upload as AntUpload, Button, Card, Typography, message, Space, Table } from "antd";
import { InboxOutlined, ThunderboltOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

const { Dragger } = AntUpload;
const { Title } = Typography;

export default function Upload() {
  const [uploading, setUploading] = useState(false);
  const [fileList, setFileList] = useState([]);
  const navigate = useNavigate();

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning("请先选择文件");
      return;
    }
    setUploading(true);
    try {
      const file = fileList[0].originFileObj;
      const formData = new FormData();
      formData.append("file", file);

      const { data: fileData } = await client.post("/files/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // 创建分析任务
      const { data: taskData } = await client.post("/tasks/", { file_id: fileData.id });
      message.success("任务已创建，正在处理中...");
      setFileList([]);
      navigate(`/tasks/${taskData.id}`);
    } finally {
      setUploading(false);
    }
  };

  const uploadProps = {
    onRemove: () => setFileList([]),
    beforeUpload: (file) => {
      const allowed = [".csv", ".xlsx", ".xls", ".json"];
      const ext = "." + file.name.split(".").pop().toLowerCase();
      if (!allowed.includes(ext)) {
        message.error(`仅支持 ${allowed.join(", ")} 格式的文件`);
        return false;
      }
      setFileList([{ name: file.name, size: file.size, originFileObj: file }]);
      return false; // 阻止自动上传
    },
    fileList,
    maxCount: 1,
  };

  return (
    <>
      <Title level={3}>文件上传</Title>
      <Card>
        <Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">支持格式：CSV、Excel（.xlsx / .xls）、JSON</p>
        </Dragger>
        <div style={{ marginTop: 16, textAlign: "center" }}>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={handleUpload}
            loading={uploading}
            disabled={fileList.length === 0}
            size="large"
          >
            上传并开始分析
          </Button>
        </div>
      </Card>
    </>
  );
}
