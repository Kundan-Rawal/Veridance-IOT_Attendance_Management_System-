import { useState, useEffect } from "react";
import axiosClient from "../../api/axiosClient";
import { Users, UserCheck, UserX, Clock, Building2 } from "lucide-react";

export default function DashboardStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Replace with your actual overview endpoint if different
        const response = await axiosClient.get("/api/admin/overview");
        setStats(response.data);
      } catch (error) {
        console.error("Failed to load dashboard stats", error);
        // Fallback mock data matching your database state for UI testing
        setStats({
          totalEnrolled: 4,
          presentToday: 2,
          absentToday: 0,
          pendingLeaves: 0,
          departments: [
            {
              code: "CS",
              name: "Computer Science",
              enrolled: 4,
              present: 2,
              percentage: 50,
            },
          ],
        });
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  if (loading)
    return (
      <div className="text-white text-xl animate-pulse">
        Loading overview...
      </div>
    );

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white drop-shadow-lg">
            System Overview
          </h2>
          <p className="text-white/90 mt-1 font-medium drop-shadow">
            Real-time attendance metrics.
          </p>
        </div>
        <div className="bg-white/20 px-5 py-2.5 rounded-full border border-white/30 text-white font-semibold shadow-inner backdrop-blur-md">
          {today}
        </div>
      </div>

      {/* Stat Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Enrolled */}
        <div className="bg-white/40 border border-white/50 rounded-xl p-5 hover:bg-white/50 transition-colors shadow-sm backdrop-blur-md">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-slate-600 text-sm font-bold uppercase tracking-wider mb-1">
                Total Enrolled
              </h3>
              <p className="text-4xl font-bold text-slate-800">
                {stats?.totalEnrolled || 0}
              </p>
            </div>
            <div className="p-3 bg-white/50 rounded-lg text-slate-500 shadow-sm border border-white/60">
              <Users size={24} />
            </div>
          </div>
        </div>

        {/* Present Today */}
        <div className="bg-white/40 border border-white/50 rounded-xl p-5 hover:bg-white/50 transition-colors shadow-sm backdrop-blur-md">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-slate-600 text-sm font-bold uppercase tracking-wider mb-1">
                Present Today
              </h3>
              <p className="text-4xl font-bold text-green-600">
                {stats?.presentToday || 0}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg text-green-600 shadow-sm border border-green-200">
              <UserCheck size={24} />
            </div>
          </div>
        </div>

        {/* Absent Today */}
        <div className="bg-white/40 border border-white/50 rounded-xl p-5 hover:bg-white/50 transition-colors shadow-sm backdrop-blur-md">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-slate-600 text-sm font-bold uppercase tracking-wider mb-1">
                Absent Today
              </h3>
              <p className="text-4xl font-bold text-red-500">
                {stats?.absentToday || 0}
              </p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg text-red-500 shadow-sm border border-red-200">
              <UserX size={24} />
            </div>
          </div>
        </div>

        {/* Pending Leaves */}
        <div className="bg-white/40 border border-white/50 rounded-xl p-5 hover:bg-white/50 transition-colors shadow-sm backdrop-blur-md">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-slate-600 text-sm font-bold uppercase tracking-wider mb-1">
                Pending Leaves
              </h3>
              <p className="text-4xl font-bold text-yellow-600">
                {stats?.pendingLeaves || 0}
              </p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-lg text-yellow-600 shadow-sm border border-yellow-200">
              <Clock size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* Department Breakdown */}
      <div className="glass-panel overflow-hidden bg-white/20 border border-white/30">
        <div className="p-5 border-b border-white/40 bg-white/30">
          <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Building2 className="text-slate-700" /> Department Breakdown
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-slate-800">
            <thead className="bg-white/40 text-slate-800 text-sm uppercase font-bold border-b border-white/50">
              <tr>
                <th className="px-6 py-4">Department</th>
                <th className="px-6 py-4 text-center">Enrolled</th>
                <th className="px-6 py-4 text-center">Present Today</th>
                <th className="px-6 py-4 text-right">Attendance %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/10">
              {stats?.departments?.map((dept, index) => (
                <tr
                  key={index}
                  className="hover:bg-white/40 transition-colors bg-white/10"
                >
                  <td className="px-6 py-4 font-bold text-slate-800 flex items-center gap-3">
                    <span className="bg-slate-800/10 px-2 py-1 rounded text-xs border border-slate-800/20 font-mono text-slate-700">
                      {dept.code}
                    </span>
                    {dept.name}
                  </td>
                  <td className="px-6 py-4 text-center font-semibold text-slate-700">
                    {dept.enrolled}
                  </td>
                  <td className="px-6 py-4 text-center font-bold text-green-600">
                    {dept.present}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <span className="font-bold text-slate-700">
                        {dept.percentage}%
                      </span>
                      <div className="w-20 h-2.5 bg-white/50 rounded-full overflow-hidden border border-white/60 shadow-inner">
                        <div
                          className="h-full bg-slate-700 rounded-full transition-all duration-1000"
                          style={{ width: `${dept.percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
