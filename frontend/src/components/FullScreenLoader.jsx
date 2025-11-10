import React from "react";
import { Loader2 } from "lucide-react";

export default function FullScreenLoader() {
  return (
    <div className="fixed inset-0 bg-white flex items-center justify-center z-50">
      <div className="flex flex-col items-center">
        <Loader2 className="animate-spin h-12 w-12 text-indigo-600" />
        <span className="mt-4 text-lg text-gray-700">Loading...</span>
      </div>
    </div>
  );
}
