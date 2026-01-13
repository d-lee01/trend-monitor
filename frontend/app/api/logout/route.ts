import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function POST() {
  const cookieStore = cookies();

  // Clear the auth cookie
  cookieStore.delete('auth_token');

  return NextResponse.json({ success: true });
}
