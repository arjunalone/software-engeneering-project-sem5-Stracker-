import React, { useEffect, useState, useCallback, useRef } from "react";
import { Loader2, Shield } from "lucide-react";
import { adminListUsers } from "../lib/api";

export default function AdminPage({ token }) {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const fetchedRef = useRef(false);

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError("");
    const data = await adminListUsers(token);
    if (data?.users) setUsers(data.users);
    else setError(data?.error || "Failed to fetch users");
    setIsLoading(false);
  }, [token]);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    fetchUsers();
  }, [fetchUsers]);

  const handleRoleChange = async () => {};

  return (
    <div className="max-w-6xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center"><Shield className="h-7 w-7 text-indigo-600 mr-2" /> Admin</h1>
      <p className="text-sm text-gray-600 mb-6">Single-admin mode enabled. Roles are read-only.</p>
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      <div className="bg-white shadow-lg rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Users</h2>
        </div>
        {isLoading ? (
          <div className="flex justify-center items-center h-64"><Loader2 className="animate-spin h-8 w-8 text-indigo-600" /></div>
        ) : users.length === 0 ? (
          <p className="text-center text-gray-500 py-10">No users found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map(u => (
                  <tr key={u.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.name || "-"}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.email}</td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${u.role === 'admin' ? 'text-indigo-700' : 'text-gray-600'}`}>{u.role || "user"}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-400">—</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
