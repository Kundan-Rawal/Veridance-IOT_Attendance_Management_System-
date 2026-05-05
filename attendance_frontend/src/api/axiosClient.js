import axios from 'axios';

// FACT: Change this to your Render URL when deploying.
const baseURL = import.meta.env.VITE_API_URL || 'https://veridance-iot-attendance-management.onrender.com';

const axiosClient = axios.create({
  baseURL,
});

axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default axiosClient;