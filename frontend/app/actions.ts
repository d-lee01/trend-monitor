'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

/**
 * Server action to set authentication cookie
 * This allows server components to access the auth token
 */
export async function setAuthCookie(token: string) {
  const cookieStore = cookies();

  // Set cookie with 7 days expiration (matching JWT expiration)
  cookieStore.set('auth_token', token, {
    httpOnly: false, // Allow client-side access
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7, // 7 days in seconds
    path: '/',
  });
}

/**
 * Server action to clear authentication cookie
 */
export async function clearAuthCookie() {
  const cookieStore = cookies();
  cookieStore.delete('auth_token');
}

/**
 * Server action to handle login
 */
export async function loginAction(username: string, password: string) {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({ username, password }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        return { success: false, error: 'Invalid username or password' };
      }
      return { success: false, error: 'Connection failed. Please try again.' };
    }

    const data = await response.json();

    // Set the cookie
    await setAuthCookie(data.access_token);

    return { success: true };
  } catch (error) {
    console.error('Login error:', error);
    return { success: false, error: 'Connection failed. Please try again.' };
  }
}
