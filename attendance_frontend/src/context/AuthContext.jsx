import { createContext, useState, useEffect } from 'react';
import axiosClient from '../api/axiosClient';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in on page load
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    const name = localStorage.getItem('name');

    if (token && role && name) {
      setUser({ token, role, name });
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      // FACT: FastAPI OAuth2 expects form-data, not JSON.
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axiosClient.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const { access_token, role, name } = response.data;

      localStorage.setItem('token', access_token);
      localStorage.setItem('role', role);
      localStorage.setItem('name', name);

      setUser({ token: access_token, role, name });
      return { success: true, role };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || "Login failed. Check your credentials." 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('name');
    setUser(null);
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-white">Loading...</div>;

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};