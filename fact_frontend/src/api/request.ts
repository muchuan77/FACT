import axios from "axios";
import { ElMessage } from "element-plus";

export const request = axios.create({
  baseURL: "",
  timeout: 8000,
});

request.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const status = error?.response?.status;
    const detail =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "请求失败";

    ElMessage.error(status ? `请求失败（${status}）：${detail}` : `请求失败：${detail}`);
    return Promise.reject(error);
  },
);

