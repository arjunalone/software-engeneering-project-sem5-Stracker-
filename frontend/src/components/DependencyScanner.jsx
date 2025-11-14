import React, { useState, useRef, useEffect } from "react";
import { Loader2, Upload, Plus } from "lucide-react";
import { scanFile, importScanResults } from "../lib/api";

export default function DependencyScanner({ token, onImported }) {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasScanned, setHasScanned] = useState(false);

  const handleScan = async () => {
    if (!file) { setError("Please select a file to scan."); return; }
    setIsLoading(true); setError(""); setResults([]); setSelected({}); setHasScanned(false);
    try {
      const data = await scanFile(token, file);
      if (Array.isArray(data)) setResults(data); else setError(data?.error || "Failed to scan file.");
    } catch (e) { setError(e.message); }
    finally { setIsLoading(false); setHasScanned(true); }
  };

  const toggle = (name) => setSelected(s => ({ ...s, [name]: !s[name] }));

  const handleImport = async () => {
    const rows = results.filter(r => selected[r.name]);
    if (rows.length === 0) { setError("Select at least one row to import."); return; }
    setIsLoading(true); setError("");
    try {
      const resp = await importScanResults(token, rows, "Planned");
      if (resp?.error) setError(resp.error); else { onImported?.(); alert(`Imported ${resp.length} releases`); }
    } catch (e) { setError(e.message); }
    finally { setIsLoading(false); }
  };

  const selectedCount = Object.values(selected).filter(Boolean).length;
  const allSelected = results.length > 0 && selectedCount === results.length;
  const someSelected = selectedCount > 0 && !allSelected;
  const headerCheckboxRef = useRef(null);
  useEffect(() => { if (headerCheckboxRef.current) headerCheckboxRef.current.indeterminate = someSelected; }, [someSelected]);
  const handleSelectAll = (checked) => {
    if (checked) {
      const all = {};
      results.forEach(r => { all[r.name] = true; });
      setSelected(all);
    } else {
      setSelected({});
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <h3 className="text-lg font-medium mb-4">Scan Dependency File</h3>
        {error && (
          <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-4 sm:space-y-0">
          <input type="file" onChange={e => { setFile(e.target.files[0]); setError(""); setHasScanned(false); }} accept=".txt,.toml" className="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100" />
          <button onClick={handleScan} disabled={isLoading || !file} className="group relative w-full sm:w-auto flex justify-center items-center rounded-md border border-transparent bg-indigo-600 py-3 px-6 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:bg-indigo-300">
            {isLoading ? <Loader2 className="animate-spin h-5 w-5" /> : <Upload className="h-5 w-5 mr-2" />}
            {isLoading ? 'Scanning...' : 'Scan File'}
          </button>
          {results.length > 0 && (
            <button onClick={handleImport} disabled={isLoading} className="group relative w-full sm:w-auto flex justify-center items-center rounded-md border border-transparent bg-green-600 py-3 px-6 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:bg-green-300">
              <Plus className="h-5 w-5 mr-2" /> Import selected to Releases
            </button>
          )}
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center items-center h-32">
          <Loader2 className="animate-spin h-8 w-8 text-indigo-600" />
        </div>
      )}

      {hasScanned && !isLoading && (
        <div className="bg-white shadow-lg rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold">Scan Results</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-300">
              <thead className="bg-gray-50">
                <tr>
                  <th className="w-10">
                    <input ref={headerCheckboxRef} type="checkbox" checked={allSelected} onChange={e => handleSelectAll(e.target.checked)} />
                  </th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Package</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Your Spec</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Latest Release</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Published</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Repository</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {results.map(item => (
                  <tr key={item.name}>
                    <td className="px-3 py-4">
                      <input type="checkbox" checked={!!selected[item.name]} onChange={() => toggle(item.name)} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm">{item.name || "N/A"}</td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{item.spec || "N/A"}</td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-indigo-600">{item.pypi_url && item.latest_version ? (<a href={item.pypi_url} target="_blank" rel="noreferrer">{item.latest_version}</a>) : "N/A"}</td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{item.release_date ? new Date(item.release_date).toLocaleDateString() : "N/A"}</td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-indigo-600">{item.repo_url ? (<a href={item.repo_url} target="_blank" rel="noreferrer">{item.repo_url}</a>) : "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
