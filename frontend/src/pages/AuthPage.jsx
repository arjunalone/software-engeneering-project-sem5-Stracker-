import React, { useState } from "react";
import { LogIn, UserPlus, Loader2 } from "lucide-react";
import { login, register } from "../lib/api";
import FormInput from "../components/FormInput";

export default function AuthPage({ onLoginSuccess, initialError }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [registerAsAdmin, setRegisterAsAdmin] = useState(false);
  const [adminSecret, setAdminSecret] = useState("");
  const [loginRole, setLoginRole] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(initialError || "");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      let data;
      if (mode === "login") {
        if (!loginRole) {
          setError("Please choose a role to login as.");
          setIsLoading(false);
          return;
        }
        data = await login(email, password, loginRole);
      }
      else data = await register(name, email, password, registerAsAdmin ? "admin" : "user", adminSecret);
      if (data?.token && data?.user) onLoginSuccess(data);
      else setError(data?.error || "An unexpected error occurred.");
    } catch (err) {
      setError(err.message || "Failed to connect to the server.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-lg shadow-lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {mode === "login" ? "Sign in to your account" : "Create a new account"}
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {mode === "register" && (
            <FormInput id="name" name="name" type="text" placeholder="Full Name" value={name} onChange={e => setName(e.target.value)} icon={<UserPlus className="h-5 w-5 text-gray-400" />} />
          )}
          <FormInput id="email-address" name="email" type="email" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} icon={<LogIn className="h-5 w-5 text-gray-400" />} />
          <FormInput id="password" name="password" type="password" placeholder="Password (min. 8 characters)" value={password} onChange={e => setPassword(e.target.value)} icon={<LogIn className="h-5 w-5 text-gray-400" />} />
          {mode === "login" && (
            <div className="space-y-2">
              <div className="text-sm text-gray-700">Login as</div>
              <div className="flex items-center space-x-6">
                <label className="flex items-center space-x-2">
                  <input type="radio" name="role" value="user" checked={loginRole === "user"} onChange={() => setLoginRole("user")} />
                  <span>User</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="radio" name="role" value="admin" checked={loginRole === "admin"} onChange={() => setLoginRole("admin")} />
                  <span>Admin</span>
                </label>
              </div>
            </div>
          )}
          {mode === "register" && (
            <div className="space-y-3">
              <label className="flex items-center space-x-2 text-sm text-gray-700">
                <input type="checkbox" checked={registerAsAdmin} onChange={e => setRegisterAsAdmin(e.target.checked)} />
                <span>Register as admin</span>
              </label>
              {registerAsAdmin && (
                <input className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm" type="password" placeholder="Admin signup secret" value={adminSecret} onChange={e => setAdminSecret(e.target.value)} />
              )}
            </div>
          )}
          {error && (<div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert"><span className="block sm:inline">{error}</span></div>)}
          <div>
            <button type="submit" disabled={isLoading} className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300">
              {isLoading ? (<Loader2 className="animate-spin h-5 w-5" />) : (mode === "login" ? "Sign in" : "Create Account")}
            </button>
          </div>
        </form>
        <div className="text-sm text-center">
          {mode === "login" ? (
            <p>Don't have an account? <button onClick={() => { setMode("register"); setError(""); }} className="font-medium text-indigo-600 hover:text-indigo-500">Sign up</button></p>
          ) : (
            <p>Already have an account? <button onClick={() => { setMode("login"); setError(""); }} className="font-medium text-indigo-600 hover:text-indigo-500">Sign in</button></p>
          )}
        </div>
      </div>
    </div>
  );
}
