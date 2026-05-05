import { useState, useEffect } from "react";
import axiosClient from "../../api/axiosClient";
import {
  CheckCircle,
  XCircle,
  Calendar,
  MessageSquare,
  Clock,
} from "lucide-react";

export default function LeaveApprovals() {
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLeaves = async () => {
    try {
      const response = await axiosClient.get("/api/leaves/admin");
      setLeaves(response.data);
    } catch (err) {
      setError("Failed to load leave requests.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaves();
  }, []);

  const handleAction = async (leaveId, status) => {
    try {
      await axiosClient.patch(`/api/leaves/admin/${leaveId}`, {
        status: status,
        admin_note: `Leave ${status.toLowerCase()} by Admin.`,
      });
      setLeaves(
        leaves.map((leave) =>
          leave.id === leaveId ? { ...leave, status: status } : leave,
        ),
      );
    } catch (err) {
      alert(`Failed to ${status.toLowerCase()} leave. Check console.`);
      console.error(err);
    }
  };

  if (loading)
    return (
      <div className="text-white text-xl animate-pulse">
        Loading leave requests...
      </div>
    );
  if (error)
    return (
      <div className="text-red-800 bg-red-100 p-4 rounded-xl border border-red-300">
        {error}
      </div>
    );

  const pendingLeaves = leaves.filter((l) => l.status === "PENDING");
  const resolvedLeaves = leaves.filter((l) => l.status !== "PENDING");

  const renderLeaveCard = (leave) => (
    <div
      key={leave.id}
      className="bg-white/40 border border-white/50 rounded-xl p-5 hover:bg-white/60 transition-colors shadow-sm backdrop-blur-md"
    >
      <div className="flex flex-col md:flex-row justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            {/* Darker Text for Name */}
            <h3 className="text-xl font-bold text-slate-800">{leave.name}</h3>
            {/* High Contrast Roll Number */}
            <span className="bg-slate-800/10 px-2 py-1 rounded text-xs border border-slate-800/20 text-slate-700 font-mono font-semibold">
              {leave.roll_no}
            </span>
            {/* High Contrast Badges */}
            <span
              className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider ${
                leave.status === "PENDING"
                  ? "bg-yellow-200 text-yellow-800 border border-yellow-400"
                  : leave.status === "APPROVED"
                    ? "bg-green-200 text-green-800 border border-green-400"
                    : "bg-red-200 text-red-800 border border-red-400"
              }`}
            >
              {leave.status}
            </span>
          </div>
          {/* Darker Date Text */}
          <p className="text-slate-600 text-sm flex items-center gap-2 mb-1 font-medium">
            <Calendar size={16} />
            {leave.from_date} to {leave.to_date}
          </p>
          {/* High Contrast Reason Box */}
          <div className="text-slate-800 text-sm flex items-start gap-2 mt-3 bg-white/50 p-3 rounded-lg border border-white/60 shadow-inner">
            <MessageSquare
              size={16}
              className="mt-0.5 shrink-0 text-slate-500"
            />
            <p className="leading-relaxed font-medium">{leave.reason}</p>
          </div>
        </div>

        {leave.status === "PENDING" && (
          <div className="flex flex-row md:flex-col gap-2 justify-center shrink-0">
            <button
              onClick={() => handleAction(leave.id, "APPROVED")}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors border border-green-600 font-medium shadow-sm"
            >
              <CheckCircle size={18} /> Approve
            </button>
            <button
              onClick={() => handleAction(leave.id, "REJECTED")}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors border border-red-600 font-medium shadow-sm"
            >
              <XCircle size={18} /> Reject
            </button>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        {/* Main Headers remain white with a stronger drop shadow for contrast against the purple background */}
        <h2 className="text-3xl font-bold text-white drop-shadow-lg">
          Leave Requests
        </h2>
        <p className="text-white/90 mt-1 font-medium drop-shadow">
          Review and manage student leave applications.
        </p>
      </div>

      <div className="glass-panel p-6 space-y-6 bg-white/20">
        <h3 className="text-xl font-bold text-slate-800 border-b border-slate-800/20 pb-2 flex items-center gap-2">
          <Clock className="text-slate-700" /> Pending Action (
          {pendingLeaves.length})
        </h3>

        <div className="grid grid-cols-1 gap-4">
          {pendingLeaves.length > 0 ? (
            pendingLeaves.map(renderLeaveCard)
          ) : (
            <div className="bg-white/40 border border-white/50 rounded-xl p-8 text-center">
              <p className="text-slate-600 font-medium">
                No pending leave requests right now.
              </p>
            </div>
          )}
        </div>

        {resolvedLeaves.length > 0 && (
          <>
            <h3 className="text-xl font-bold text-slate-800 border-b border-slate-800/20 pb-2 mt-8">
              Past Requests
            </h3>
            <div className="grid grid-cols-1 gap-4 opacity-90">
              {resolvedLeaves.map(renderLeaveCard)}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
