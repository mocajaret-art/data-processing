import { Layout, Menu, Button, Space } from "antd";
import { DashboardOutlined, UploadOutlined, UserOutlined, LogoutOutlined } from "@ant-design/icons";
import { useNavigate, useLocation } from "react-router-dom";

const { Header } = Layout;

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  const menuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "仪表盘" },
    { key: "/upload", icon: <UploadOutlined />, label: "上传文件" },
  ];

  const currentKey = location.pathname === "/upload" ? "/upload" : "/";

  return (
    <Header style={{ display: "flex", alignItems: "center", padding: "0 24px", background: "#001529" }}>
      <div style={{ color: "#fff", fontSize: 18, fontWeight: 700, marginRight: 40, whiteSpace: "nowrap" }}>
        FBS 数据处理平台
      </div>
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={[currentKey]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
        style={{ flex: 1, minWidth: 0 }}
      />
      <Space style={{ marginLeft: "auto" }}>
        <Button type="text" icon={<UserOutlined />} style={{ color: "#fff" }}>
          {user.username || "用户"}
        </Button>
        <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout} style={{ color: "#fff" }}>
          退出登录
        </Button>
      </Space>
    </Header>
  );
}
