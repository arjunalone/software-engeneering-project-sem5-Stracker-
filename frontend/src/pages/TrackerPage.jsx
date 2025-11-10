import React, { useEffect, useState, useCallback } from "react";
import { Loader2 } from "lucide-react";
import { getReleases } from "../lib/api";
import NewReleaseForm from "../components/NewReleaseForm";
import ReleaseItem from "../components/ReleaseItem";
import DependencyScanner from "../components/DependencyScanner";

export default function TrackerPage({ user, token }) {
  const [releases, setReleases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchReleases = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await getReleases(token);
      if (Array.isArray(data)) setReleases(data);
      else setError(data?.error || "Failed to fetch releases.");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchReleases(); }, [fetchReleases]);

  const handleReleaseCreated = (newRelease) => setReleases([newRelease, ...releases]);
  const handleReleaseDeleted = (releaseId) => setReleases(releases.filter(r => r.id !== releaseId));
  const handleReleaseUpdated = (updatedRelease) => setReleases(releases.map(r => r.id === updatedRelease.id ? updatedRelease : r));

  return (
    <div className="max-w-6xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Welcome, {user.name}</h1>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      {user.role === "admin" && (
        <NewReleaseForm token={token} onReleaseCreated={handleReleaseCreated} />
      )}

      <div className="mt-8 bg-white shadow-lg rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">{user.role === "admin" ? "All Releases" : "Your Releases"}</h2>
        </div>
        {isLoading ? (
          <div className="flex justify-center items-center h-64"><Loader2 className="animate-spin h-8 w-8 text-indigo-600" /></div>
        ) : releases.length === 0 ? (
          <p className="text-center text-gray-500 py-10">You don't have any releases yet. Add one above!</p>
        ) : (
          <ul className="divide-y divide-gray-200">
            {releases.map(release => (
              <ReleaseItem key={release.id} release={release} token={token} onDelete={handleReleaseDeleted} onUpdate={handleReleaseUpdated} />
            ))}
          </ul>
        )}
      </div>

      <div className="mt-8"><DependencyScanner token={token} onImported={fetchReleases} /></div>
    </div>
  );
}
