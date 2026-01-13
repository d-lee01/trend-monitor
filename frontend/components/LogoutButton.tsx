'use client';

import { useRouter } from 'next/navigation';
import { clearAuthCookie } from '@/app/actions';

export function LogoutButton() {
  const handleLogout = async () => {
    // Clear the auth cookie
    await fetch('/api/logout', { method: 'POST' });

    // Redirect to login
    window.location.href = '/';
  };

  return (
    <button
      onClick={handleLogout}
      className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
    >
      Logout
    </button>
  );
}
