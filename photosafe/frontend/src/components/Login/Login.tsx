import React, { FormEvent, useState } from "react";
import { useHistory, useLocation } from "react-router-dom";
import { useAuth } from "../../services/auth-service";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const auth = useAuth();
  const history = useHistory();
  const location = useLocation<{ redirectPath: string | null | undefined }>();
  const redirectPath = location.state?.redirectPath || "/photos";

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      setError(null);
      await auth.handleLogin(username, password);
      history.push(redirectPath);
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <form
      className="space-y-8 divide-y divide-gray-200"
      onSubmit={handleSubmit}
    >
      <div className="space-y-8 divide-y divide-gray-200">
        <div>
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Login
            </h3>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
            <div className="sm:col-span-4">
              <label
                htmlFor="username"
                className="block text-sm font-medium text-gray-700"
              >
                Username
              </label>
              <div className="mt-1 flex rounded-md shadow-sm">
                {/* <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                  workcation.com/
                </span> */}
                <input
                  type="text"
                  name="username"
                  id="username"
                  autoComplete="username"
                  className="flex-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full min-w-0 rounded-none rounded-r-md sm:text-sm border-gray-300"
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </div>
          </div>
          <div className="mt-6 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
            <div className="sm:col-span-4">
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <input
                  type="password"
                  name="password"
                  id="password"
                  autoComplete="password"
                  className="flex-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full min-w-0 rounded-none rounded-r-md sm:text-sm border-gray-300"
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>
          </div>
          {error ? (
            <p className="mt-2 text-sm text-red-600" id="error">
              {error}
            </p>
          ) : (
            ""
          )}
        </div>
      </div>

      <div className="pt-5">
        <div className="flex justify-end">
          <button
            type="submit"
            className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Login
          </button>
        </div>
      </div>
    </form>
  );
}
