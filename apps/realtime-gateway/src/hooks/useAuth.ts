import { useState, useEffect, useCallback } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Use a ref to track if we've already set up the listener
    // This prevents duplicate listeners in React Strict Mode or component re-mounts
    let isSubscribed = true;
    
    console.log('🔐 useAuth: Setting up auth state listener');
    // Set up auth state listener FIRST
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (!isSubscribed) return; // Ignore if component unmounted
        
        console.log('🔐 useAuth: Auth state changed - event:', event, 'has session:', !!session, 'has user:', !!session?.user);
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);

        // Log login audit for successful sign-in (commented out to prevent loops)
        // if (event === 'SIGNED_IN' && session?.user) {
        //   try {
        //     const { data: { session: currentSession } } = await supabase.auth.getSession();
        //     if (currentSession?.access_token) {
        //       // Get device information
        //       const userAgent = navigator.userAgent;
        //       const deviceName = /Mobile|Android/i.test(userAgent) ? 'Mobile Device' : 'Desktop';
        //       
        //       // Get IP address (client-side approximation)
        //       const ipAddress = await fetch('https://api.ipify.org?format=json')
        //         .then(res => res.json())
        //         .then(data => data.ip)
        //         .catch(() => 'unknown');
        // 
        //       // Log successful login
        //       await fetch('/api/auth/login-audit', {
        //         method: 'POST',
        //         headers: {
        //           'Content-Type': 'application/json',
        //           'Authorization': `Bearer ${currentSession.access_token}`
        //         },
        //         body: JSON.stringify({
        //           user_id: session.user.id,
        //           login_method: 'password',
        //           status: 'success',
        //           ip_address: ipAddress,
        //           user_agent: userAgent,
        //           device_name: deviceName
        //         })
        //       }).catch(err => console.error('Failed to log login audit:', err));
        //     }
        //   } catch (error) {
        //     console.error('Error logging login audit:', error);
        //   }
        // }
      }
    );

    // THEN check for existing session (only once)
    console.log('🔐 useAuth: Checking for existing session...');
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (!isSubscribed) return; // Ignore if component unmounted
      
      console.log('🔐 useAuth: getSession result - has session:', !!session, 'has user:', !!session?.user, 'error:', error);
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => {
      isSubscribed = false;
      subscription.unsubscribe();
    };
  }, []);

  const signUp = useCallback(async (email: string, password: string, salespersonName: string, organizationId: string) => {
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
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password
    });
    return { error };
  }, []);

  const signOut = useCallback(async () => {
    console.log('🔓 useAuth.signOut: Starting sign out...');
    const { error } = await supabase.auth.signOut();
    console.log('🔓 useAuth.signOut: Completed, error:', error);
    return { error };
  }, []);

  const resetPassword = useCallback(async (email: string) => {
    const siteUrl = (import.meta as any)?.env?.VITE_SITE_URL || (typeof window !== 'undefined' ? window.location.origin : '');
    const redirectUrl = siteUrl ? `${siteUrl}/` : undefined;
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: redirectUrl
    });
    return { error };
  }, []);

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