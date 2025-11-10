import React, { useState } from "react";
import { Loader2, Home, Check, Plus } from "lucide-react";
import { createRelease } from "../lib/api";
import FormInput from "./FormInput";

export default function NewReleaseForm({ token, onReleaseCreated }) {
  const [projectName, setProjectName] = useState("");
  const [version, setVersion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!projectName || !version) {
      setError("Project name and version are required.");
      return;
    }
    setIsLoading(true);
    setError("");

    try {
      const data = await createRelease(token, projectName, version, "Planned");
      if (data?.id) {
        onReleaseCreated?.(data);
        setProjectName("");
        setVersion("");
      } else {
        setError(data?.error || "Failed to create release.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-lg space-y-4">
      <h3 className="text-lg font-medium">Add New Release</h3>
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <FormInput
          id="project_name"
          name="project_name"
          type="text"
          placeholder="Project Name (e.g., 'Frontend App')"
          value={projectName}
          onChange={e => setProjectName(e.target.value)}
          icon={<Home className="h-5 w-5 text-gray-400" />}
        />
        <FormInput
          id="version"
          name="version"
          type="text"
          placeholder="Version (e.g., 'v1.2.0')"
          value={version}
          onChange={e => setVersion(e.target.value)}
          icon={<Check className="h-5 w-5 text-gray-400" />}
        />
        <button
          type="submit"
          disabled={isLoading}
          className="md:col-span-1 w-full flex justify-center items-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:bg-indigo-300"
        >
          {isLoading ? <Loader2 className="animate-spin h-5 w-5" /> : <Plus className="h-5 w-5 mr-2" />}
          {isLoading ? 'Saving...' : 'Add Release'}
        </button>
      </div>
    </form>
  );
}
