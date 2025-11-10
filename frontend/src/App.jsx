import React, { useState, useEffect, useCallback } from "react";
import { LogOut, Zap, LayoutDashboard, Shield } from 'lucide-react';
import { me } from "./lib/api";
import FullScreenLoader from "./components/FullScreenLoader";
import AuthPage from "./pages/AuthPage";
import TrackerPage from "./pages/TrackerPage";
import AdminPage from "./pages/AdminPage";
    
    
    // --- Main App Component ---
    
    function App() {
      const [token, setToken] = useState(localStorage.getItem("token") || "");
      const [user, setUser] = useState(null);
      const [isLoading, setIsLoading] = useState(true);
      const [error, setError] = useState("");
      const [view, setView] = useState("tracker");
    
      useEffect(() => {
        if (token) {
          setIsLoading(true);
          me(token)
            .then(data => {
              if (data?.user) {
                setUser(data.user);
                setView(data.user.role === 'admin' ? 'admin' : 'tracker');
              } else {
                localStorage.removeItem("token");
                setToken("");
                setError(data?.error || "Your session has expired. Please log in.");
              }
              setIsLoading(false);
            })
            .catch(err => {
              setIsLoading(false);
              setError(err.message);
            });
        } else {
          setIsLoading(false); 
        }
      }, [token]); 
    
      const handleLoginSuccess = ({ user, token }) => {
        localStorage.setItem("token", token);
        setToken(token);
        setUser(user);
        setView(user.role === 'admin' ? 'admin' : 'tracker');
        setError("");
      };
    
      const handleLogout = () => {
        localStorage.removeItem("token");
        setToken("");
        setUser(null);
        setError("");
        setView("tracker");
      };
    
      if (isLoading) {
        return <FullScreenLoader />;
      }
      
      return (
        <div className="min-h-screen bg-gray-100 text-gray-900">
          <nav className="bg-gradient-to-r from-indigo-100 to-white shadow-md">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <Zap className="h-6 w-6 text-indigo-600" />
                  <span className="ml-2 font-semibold text-lg">ReleaseTracker</span>
                </div>
                <div className="flex items-center space-x-4">
                  {user && user.role === 'admin' && (
                    <>
                      <button className={`px-3 py-1 rounded inline-flex items-center gap-2 transition-colors ${view === 'tracker' ? 'bg-indigo-700 text-white shadow-sm' : 'text-gray-800 hover:text-indigo-800 hover:bg-indigo-50'}`} onClick={() => setView('tracker')}>
                        <LayoutDashboard className="h-4 w-4" />
                        Dashboard
                      </button>
                      <button className={`px-3 py-1 rounded inline-flex items-center gap-2 transition-colors relative ${view === 'admin' ? 'bg-indigo-700 text-white shadow-sm' : 'text-gray-800 hover:text-indigo-800 hover:bg-indigo-50'}`} onClick={() => setView('admin')}>
                        <Shield className="h-4 w-4" />
                        Admin
                        <span className={`ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${view === 'admin' ? 'bg-white/20 text-white' : 'bg-indigo-600 text-white'}`}>NEW</span>
                      </button>
                    </>
                  )}
                  {user && (
                    <span className="text-sm text-gray-500">{user.name}</span>
                  )}
                  {user && (
                    <button onClick={handleLogout} className="flex items-center text-gray-600 hover:text-indigo-600 focus:outline-none">
                      <LogOut className="h-5 w-5 mr-1" />
                      Logout
                    </button>
                  )}
                </div>
              </div>
            </div>
          </nav>

          <main>
            {user ? (
              view === 'admin' ? (
                <AdminPage token={token} />
              ) : (
                <TrackerPage user={user} token={token} />
              )
            ) : (
              <AuthPage onLoginSuccess={handleLoginSuccess} initialError={error} />
            )}
          </main>
        </div>
      );
    }
    
    export default App;