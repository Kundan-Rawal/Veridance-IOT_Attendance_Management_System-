import { useState, useEffect, useContext } from "react";
import { AuthContext } from "../../context/AuthContext";
import axiosClient from "../../api/axiosClient";
import {
  LogOut,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  Send,
  BarChart2,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

export default function StudentDashboard() {
  const { logout, user } = useContext(AuthContext);

  const [summary, setSummary] = useState(null);
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);

  // Leave Form State
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const fetchStudentData = async () => {
      try {
        const [summaryRes, leavesRes] = await Promise.all([
          axiosClient.get("/api/attendance/me/summary"),
          axiosClient.get("/api/leaves/me"),
        ]);
        setSummary(summaryRes.data);
        setLeaves(leavesRes.data);
      } catch (err) {
        console.error("Failed to fetch student data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStudentData();
  }, []);

  const handleApplyLeave = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const response = await axiosClient.post("/api/leaves/apply", {
        from_date: fromDate,
        to_date: toDate,
        reason: reason,
      });
      setLeaves([response.data, ...leaves]);
      setFromDate("");
      setToDate("");
      setReason("");
      alert("Leave application submitted successfully.");
    } catch (err) {
      alert(
        err.response?.data?.detail || "Failed to submit leave application.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading)
    return (
      <div className="text-white text-xl animate-pulse p-8">
        Loading your portal...
      </div>
    );

  const chartData = [
    { name: "Present", value: summary?.present || 0, color: "#22c55e" }, // green-500
    { name: "Absent", value: summary?.absent || 0, color: "#ef4444" }, // red-500
    { name: "Leave", value: summary?.leave || 0, color: "#eab308" }, // yellow-500
  ].filter((item) => item.value > 0);

  return (
    <div className="flex flex-col h-screen p-4 gap-4 overflow-hidden animate-in fade-in duration-500">
      {/* Navbar - Keep headers white for contrast against the global background */}
      <div className="glass-panel flex justify-between items-center p-4 md:px-8 bg-white/10 border-white/20">
        <div>
          <h1 className="text-2xl font-bold text-white drop-shadow-lg">
            Student Portal
          </h1>
          <p className="text-white/90 text-sm font-medium drop-shadow">
            Welcome back, {user?.name}
          </p>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-all border border-red-600 font-medium shadow-sm"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pb-12">
        {/* Top Stats Row - Matched to Admin Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white/40 border border-white/50 rounded-xl p-5 text-center shadow-sm backdrop-blur-md">
            <h3 className="text-slate-600 text-sm font-bold uppercase tracking-wider mb-1">
              Total Days
            </h3>
            <p className="text-3xl font-bold text-slate-800">
              {summary?.total || 0}
            </p>
          </div>
          <div className="bg-white/40 border border-white/50 rounded-xl p-5 text-center shadow-sm backdrop-blur-md">
            <h3 className="text-slate-600 text-sm font-bold uppercase tracking-wider mb-1">
              Present
            </h3>
            <p className="text-3xl font-bold text-green-600">
              {summary?.present || 0}
            </p>
          </div>
          <div className="bg-white/40 border border-white/50 rounded-xl p-5 text-center shadow-sm backdrop-blur-md">
            <h3 className="text-slate-600 text-sm font-bold uppercase tracking-wider mb-1">
              Absent
            </h3>
            <p className="text-3xl font-bold text-red-500">
              {summary?.absent || 0}
            </p>
          </div>
          <div className="bg-white/40 border border-white/50 rounded-xl p-5 text-center shadow-sm backdrop-blur-md">
            <h3 className="text-slate-600 text-sm font-bold uppercase tracking-wider mb-1">
              Attendance %
            </h3>
            <p className="text-3xl font-bold text-blue-600">
              {summary?.percentage || 0}%
            </p>
          </div>
        </div>

        {/* Main Grid: Chart & Form */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left Col: Analytics */}
          <div className="glass-panel bg-white/20 border border-white/30 p-6 flex flex-col items-center justify-center min-h-[350px]">
            <h3 className="text-xl font-bold text-slate-800 mb-4 w-full flex items-center gap-2">
              <BarChart2 className="text-slate-700" /> Attendance Analytics
            </h3>
            {summary?.total > 0 ? (
              <div className="w-full h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    {/* High contrast tooltip for Recharts */}
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(255, 255, 255, 0.95)",
                        border: "1px solid #cbd5e1",
                        borderRadius: "12px",
                        color: "#1e293b",
                      }}
                      itemStyle={{ color: "#1e293b", fontWeight: "bold" }}
                    />
                    <Legend wrapperStyle={{ paddingTop: "20px" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-500 font-medium">
                No attendance data recorded yet.
              </div>
            )}
          </div>

          {/* Right Col: Leave Application Form */}
          <div className="glass-panel bg-white/20 border border-white/30 p-6">
            <h3 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
              Apply for Leave
            </h3>
            <form onSubmit={handleApplyLeave} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-700 text-sm font-bold mb-1">
                    From Date
                  </label>
                  <input
                    type="date"
                    required
                    value={fromDate}
                    onChange={(e) => setFromDate(e.target.value)}
                    className="w-full px-4 py-2.5 bg-white/40 border border-white/50 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-400 transition-all font-medium"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 text-sm font-bold mb-1">
                    To Date
                  </label>
                  <input
                    type="date"
                    required
                    value={toDate}
                    onChange={(e) => setToDate(e.target.value)}
                    className="w-full px-4 py-2.5 bg-white/40 border border-white/50 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-400 transition-all font-medium"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-700 text-sm font-bold mb-1">
                  Reason for Leave
                </label>
                <textarea
                  required
                  rows="3"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Explain why you need this leave..."
                  className="w-full px-4 py-3 bg-white/40 border border-white/50 rounded-xl text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400 resize-none font-medium transition-all"
                ></textarea>
              </div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-bold transition-all border border-indigo-600 disabled:opacity-50 shadow-sm"
              >
                <Send size={18} />
                {isSubmitting ? "Submitting..." : "Submit Application"}
              </button>
            </form>
          </div>
        </div>

        {/* Bottom Section: Leave History */}
        <div className="glass-panel bg-white/20 border border-white/30 overflow-hidden">
          <div className="p-5 border-b border-white/40 bg-white/30">
            <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              <Calendar className="text-slate-700" /> My Leave History
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-slate-800">
              <thead className="bg-white/40 text-slate-800 text-sm uppercase font-bold border-b border-white/50">
                <tr>
                  <th className="px-6 py-4">Dates</th>
                  <th className="px-6 py-4">Reason</th>
                  <th className="px-6 py-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/10">
                {leaves.map((leave) => (
                  <tr
                    key={leave.id}
                    className="hover:bg-white/40 transition-colors bg-white/10"
                  >
                    <td className="px-6 py-4 font-bold text-slate-800 whitespace-nowrap">
                      {leave.from_date}{" "}
                      <span className="text-slate-500 mx-1 font-medium">
                        to
                      </span>{" "}
                      {leave.to_date}
                    </td>
                    <td
                      className="px-6 py-4 text-slate-700 font-medium max-w-md truncate"
                      title={leave.reason}
                    >
                      {leave.reason}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm ${
                          leave.status === "PENDING"
                            ? "bg-yellow-200 text-yellow-800 border border-yellow-400"
                            : leave.status === "APPROVED"
                              ? "bg-green-200 text-green-800 border border-green-400"
                              : "bg-red-200 text-red-800 border border-red-400"
                        }`}
                      >
                        {leave.status === "PENDING" && <Clock size={12} />}
                        {leave.status === "APPROVED" && (
                          <CheckCircle size={12} />
                        )}
                        {leave.status === "REJECTED" && <XCircle size={12} />}
                        {leave.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {leaves.length === 0 && (
                  <tr>
                    <td
                      colSpan="3"
                      className="px-6 py-12 text-center text-slate-500 font-medium bg-white/20"
                    >
                      You have not applied for any leaves yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
