'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LoginForm } from '@/components/LoginForm';
import { auth } from '@/lib/auth';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard if already logged in
    if (auth.isAuthenticated()) {
      router.push('/dashboard');
    }
  }, [router]);

  return <LoginForm />;
}
