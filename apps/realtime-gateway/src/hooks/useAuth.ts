import { useState, useEffect } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Set up auth state listener FIRST
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);

        // Log login audit for successful sign-in
        if (event === 'SIGNED_IN' && session?.user) {
          try {
            const { data: { session: currentSession } } = await supabase.auth.getSession();
            if (currentSession?.access_token) {
              // Get device information
              const userAgent = navigator.userAgent;
              const deviceName = /Mobile|Android/i.test(userAgent) ? 'Mobile Device' : 'Desktop';
              
              // Get IP address (client-side approximation)
              const ipAddress = await fetch('https://api.ipify.org?format=json')
                .then(res => res.json())
                .then(data => data.ip)
                .catch(() => 'unknown');

              // Log successful login
              await fetch('/api/auth/login-audit', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${currentSession.access_token}`
                },
                body: JSON.stringify({
                  user_id: session.user.id,
                  login_method: 'password',
                  status: 'success',
                  ip_address: ipAddress,
                  user_agent: userAgent,
                  device_name: deviceName
                })
              }).catch(err => console.error('Failed to log login audit:', err));
            }
          } catch (error) {
            console.error('Error logging login audit:', error);
          }
        }
      }
    );

    // THEN check for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signUp = async (email: string, password: string, salespersonName: string, organizationId: string) => {
    const siteUrl = (import.meta as any)?.env?.VITE_SITE_URL || (typeof window !== 'undefined' ? window.location.origin : '');
    const redirectUrl = siteUrl ? `${siteUrl}/` : undefined;
    
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: redirectUrl,
        data: {
          salesperson_name: salespersonName,
          organization_id: organizationId
        }
      }
    });
    return { error };
  };

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password
    });
    return { error };
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    return { error };
  };

  const resetPassword = async (email: string) => {
    const siteUrl = (import.meta as any)?.env?.VITE_SITE_URL || (typeof window !== 'undefined' ? window.location.origin : '');
    const redirectUrl = siteUrl ? `${siteUrl}/` : undefined;
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: redirectUrl
    });
    return { error };
  };

  return {
    user,
    session,
    loading,
    signUp,
    signIn,
    signOut,
    resetPassword
  };
};