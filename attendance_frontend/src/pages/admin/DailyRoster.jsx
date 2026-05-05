import { useState, useEffect } from "react";
import axiosClient from "../../api/axiosClient";
import {
  Calendar as CalendarIcon,
  UserCheck,
  UserX,
  AlertCircle,
} from "lucide-react";

export default function DailyRoster() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Default to today
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split("T")[0],
  );

  useEffect(() => {
    const fetchRoster = async () => {
      setLoading(true);
      try {
        const response = await axiosClient.get(
          `/api/attendance/logs?date=${selectedDate}`,
        );
        setLogs(response.data);
        setError(null);
      } catch (err) {
        setError("Failed to load roster for this date.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRoster();
  }, [selectedDate]);

  // Split the data into two distinct arrays
  const presentStudents = logs.filter((log) => log.status === "PRESENT");
  const absentStudents = logs.filter((log) => log.status !== "PRESENT");

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white drop-shadow-lg">
            Daily Roster
          </h2>
          <p className="text-white/90 mt-1 font-medium drop-shadow">
            See exactly who is present and who is missing.
          </p>
        </div>

        {/* Date Picker */}
        <div className="relative w-full md:w-auto">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <CalendarIcon className="h-5 w-5 text-slate-500" />
          </div>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/40 border border-white/50 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-400 transition-all shadow-inner backdrop-blur-sm font-medium"
          />
        </div>
      </div>

      {error && (
        <div className="text-red-800 bg-red-100 p-4 rounded-xl border border-red-300 font-medium">
          {error}
        </div>
      )}

      {/* Two-Column Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Present Column */}
        <div className="glass-panel bg-white/20 border border-white/30 overflow-hidden flex flex-col h-[600px]">
          <div className="p-5 border-b border-white/40 bg-white/30 flex justify-between items-center">
            <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              <UserCheck className="text-green-600" /> Present
            </h3>
            <span className="bg-green-200 text-green-800 px-3 py-1 rounded-full text-sm font-bold border border-green-400">
              {presentStudents.length}
            </span>
          </div>
          <div className="overflow-y-auto flex-1 p-2">
            {loading ? (
              <div className="p-8 text-center text-slate-500 font-medium animate-pulse">
                Loading data...
              </div>
            ) : presentStudents.length > 0 ? (
              <ul className="space-y-2 p-2">
                {presentStudents.map((student) => (
                  <li
                    key={student.id}
                    className="bg-white/40 border border-white/50 rounded-lg p-3 flex justify-between items-center shadow-sm"
                  >
                    <span className="font-bold text-slate-800">
                      {student.student_name}
                    </span>
                    <span className="text-xs font-mono bg-white/50 px-2 py-1 rounded text-slate-600 border border-white/60">
                      {student.roll_no}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 opacity-70">
                <AlertCircle size={32} className="mb-2" />
                <p>No students marked present yet.</p>
              </div>
            )}
          </div>
        </div>

        {/* Absent Column */}
        <div className="glass-panel bg-white/20 border border-white/30 overflow-hidden flex flex-col h-[600px]">
          <div className="p-5 border-b border-white/40 bg-white/30 flex justify-between items-center">
            <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              <UserX className="text-red-500" /> Absent / Missing
            </h3>
            <span className="bg-red-200 text-red-800 px-3 py-1 rounded-full text-sm font-bold border border-red-400">
              {absentStudents.length}
            </span>
          </div>
          <div className="overflow-y-auto flex-1 p-2">
            {loading ? (
              <div className="p-8 text-center text-slate-500 font-medium animate-pulse">
                Loading data...
              </div>
            ) : absentStudents.length > 0 ? (
              <ul className="space-y-2 p-2">
                {absentStudents.map((student) => (
                  <li
                    key={student.id}
                    className="bg-white/40 border border-white/50 rounded-lg p-3 flex justify-between items-center shadow-sm"
                  >
                    <span className="font-bold text-slate-800">
                      {student.student_name}
                    </span>
                    <span className="text-xs font-mono bg-white/50 px-2 py-1 rounded text-slate-600 border border-white/60">
                      {student.roll_no}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 opacity-70">
                <UserCheck size={32} className="mb-2 text-slate-400" />
                <p>Everyone is accounted for.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
