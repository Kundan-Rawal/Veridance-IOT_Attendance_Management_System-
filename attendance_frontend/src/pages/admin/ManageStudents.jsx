import { useState, useEffect } from "react";
import axiosClient from "../../api/axiosClient";
import { Search, Trash2, ShieldAlert } from "lucide-react";

export default function ManageStudents() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchStudents = async () => {
    try {
      const response = await axiosClient.get("/api/students");
      setStudents(response.data);
    } catch (err) {
      setError("Failed to load students.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  const handleDelete = async (studentId, studentName) => {
    if (
      !window.confirm(
        `Are you sure you want to remove ${studentName}? This cannot be undone.`,
      )
    )
      return;

    try {
      await axiosClient.delete(`/api/students/${studentId}`);
      setStudents(students.filter((s) => s.id !== studentId));
    } catch (err) {
      alert("Failed to delete student. Check console for details.");
      console.error(err);
    }
  };

  const filteredStudents = students.filter(
    (student) =>
      student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      student.roll_no.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  if (loading)
    return (
      <div className="text-white text-xl animate-pulse">
        Loading students...
      </div>
    );
  if (error)
    return (
      <div className="text-red-800 bg-red-100 p-4 rounded-xl border border-red-300">
        {error}
      </div>
    );

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white drop-shadow-lg">
            Manage Students
          </h2>
          <p className="text-white/90 mt-1 font-medium drop-shadow">
            View and manage enrolled students.
          </p>
        </div>

        {/* High Contrast Search Bar */}
        <div className="relative w-full md:w-72">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-slate-500" />
          </div>
          <input
            type="text"
            placeholder="Search by name or roll no..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/40 border border-white/50 rounded-xl text-slate-800 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400 transition-all shadow-inner backdrop-blur-sm font-medium"
          />
        </div>
      </div>

      {/* Glass Table with Dark Text */}
      <div className="glass-panel overflow-hidden bg-white/20 border border-white/30">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-slate-800">
            <thead className="bg-white/40 text-slate-800 text-sm uppercase font-bold border-b border-white/50">
              <tr>
                <th className="px-6 py-4">Roll Number</th>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Department</th>
                <th className="px-6 py-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/10">
              {filteredStudents.map((student) => (
                <tr
                  key={student.id}
                  className="hover:bg-white/40 transition-colors bg-white/10"
                >
                  <td className="px-6 py-4 font-mono text-sm font-semibold text-slate-700">
                    <span className="bg-slate-800/10 px-2 py-1 rounded border border-slate-800/20">
                      {student.roll_no}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-bold text-slate-800">
                    {student.name}
                  </td>
                  <td className="px-6 py-4">
                    <span className="bg-slate-800/5 px-3 py-1 rounded-full text-xs border border-slate-800/10 font-semibold text-slate-700 shadow-sm">
                      {student.dept_name}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={() => handleDelete(student.id, student.name)}
                      className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors border border-red-600 inline-flex items-center gap-2 text-sm font-medium shadow-sm"
                      title="Remove Student"
                    >
                      <Trash2 size={16} />
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
              {filteredStudents.length === 0 && (
                <tr>
                  <td
                    colSpan="4"
                    className="px-6 py-12 text-center text-slate-600 font-medium bg-white/20"
                  >
                    <ShieldAlert className="h-12 w-12 mx-auto mb-3 text-slate-400" />
                    <p>No students found matching your criteria.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
