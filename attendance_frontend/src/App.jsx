import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import { useContext } from 'react';

// Pages (we will create these next)
import Login from './pages/auth/Login';
import AdminDashboard from './pages/admin/AdminDashboard';
import StudentDashboard from './pages/student/StudentDashboard';

// Protected Route Wrapper
const ProtectedRoute = ({ children, allowedRole }) => {
  const { user } = useContext(AuthContext);

  if (!user) return <Navigate to="/" />;
  if (user.role !== allowedRole) {
    return <Navigate to={user.role === 'admin' ? '/admin' : '/student'} />;
  }

  return children;
};

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Login />} />
          
          <Route 
            path="/admin/*" 
            element={
              <ProtectedRoute allowedRole="admin">
                <AdminDashboard />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/student/*" 
            element={
              <ProtectedRoute allowedRole="student">
                <StudentDashboard />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}