import React, { useState } from "react";
import { Loader2, Trash2 } from "lucide-react";
import { updateReleaseStatus, deleteRelease } from "../lib/api";

export default function ReleaseItem({ release, token, onDelete, onUpdate }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const statusOptions = ["Planned", "In Development", "Released", "Archived"];

  const getStatusColor = (status) => {
    switch (status) {
      case "Planned":
        return "bg-blue-100 text-blue-800";
      case "In Development":
        return "bg-yellow-100 text-yellow-800";
      case "Released":
        return "bg-green-100 text-green-800";
      case "Archived":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const handleDelete = async () => {
    const confirmMessage = `Are you sure you want to delete ${release.project_name} ${release.version}?`;
    if (!window.confirm(confirmMessage)) return;
    setIsDeleting(true);
    try {
      const data = await deleteRelease(token, release.id);
      if (data?.error) throw new Error(data.error);
      onDelete?.(release.id);
    } catch (err) {
      alert("Failed to delete: " + err.message);
      setIsDeleting(false);
    }
  };

  const handleStatusChange = async (e) => {
    const newStatus = e.target.value;
    setIsUpdating(true);
    try {
      const updated = await updateReleaseStatus(token, release.id, newStatus);
      if (updated?.error) throw new Error(updated.error);
      onUpdate?.(updated);
    } catch (err) {
      alert("Failed to update: " + err.message);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <li className="px-6 py-4 flex flex-col md:flex-row items-start md:items-center justify-between">
      <div className="mb-4 md:mb-0">
        <div className="flex items-center">
          <span className="text-lg font-semibold text-indigo-700">{release.project_name}</span>
          <span className="ml-3 inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800">
            {release.version}
          </span>
        </div>
        <span className="text-sm text-gray-500">Created: {new Date(release.created_at).toLocaleDateString()}</span>
      </div>

      <div className="flex items-center space-x-3">
        {(isUpdating || isDeleting) ? (
          <Loader2 className="animate-spin h-5 w-5 text-gray-500" />
        ) : (
          <>
            <select
              value={release.status}
              onChange={handleStatusChange}
              className={`text-sm font-medium rounded-full px-3 py-1 focus:outline-none ${getStatusColor(release.status)}`}
            >
              {statusOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </select>

            <button onClick={handleDelete} disabled={isDeleting} className="text-gray-400 hover:text-red-600 focus:outline-none">
              <Trash2 className="h-5 w-5" />
            </button>
          </>
        )}
      </div>
    </li>
  );
}
