import { Outlet } from "react-router-dom";

export function AuthLayout() {
  return (
    <div className="auth-page-bg flex min-h-dvh min-h-screen flex-col">
      <main className="flex flex-1 items-center justify-center px-3 py-6 sm:px-6 sm:py-10 lg:py-14">
        <Outlet />
      </main>
    </div>
  );
}
