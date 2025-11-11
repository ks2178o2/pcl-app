/**
 * API Configuration Utility
 * 
 * This utility provides a centralized way to get the API base URL.
 * In production, if VITE_API_URL is not set, it defaults to relative URLs
 * to avoid CORS issues when frontend and backend are served from the same domain.
 */

/**
 * Get the API base URL for making requests
 * 
 * Priority:
 * 1. Use VITE_API_URL if explicitly set (build-time environment variable) - REQUIRED in production
 * 2. In production (https or non-localhost), use empty string for relative URLs (only if API is on same domain)
 * 3. In development, default to http://localhost:8001
 * 
 * IMPORTANT: For production deployments where frontend and backend are on different domains,
 * you MUST set VITE_API_URL at build time. Relative URLs only work if there's a reverse proxy
 * routing /api/* requests to the backend.
 */
export function getApiBaseUrl(): string {
  // Check if VITE_API_URL is explicitly set at build time
  // Vite replaces import.meta.env.VITE_* at build time
  const envApiUrl = import.meta.env?.VITE_API_URL as string | undefined;
  
  // Debug logging to help diagnose issues
  if (typeof window !== 'undefined') {
    console.log('🔍 API Config Debug:', {
      VITE_API_URL: envApiUrl || 'NOT SET',
      windowLocation: window.location.href,
      importMetaEnv: import.meta.env
    });
  }
  
  if (envApiUrl && envApiUrl.trim() !== '') {
    const cleanUrl = envApiUrl.trim();
    console.log('✅ Using VITE_API_URL:', cleanUrl);
    return cleanUrl;
  }
  
  // If no explicit URL is set, check if we're in production
  // Production is detected by checking window.location (browser only)
  if (typeof window !== 'undefined' && window.location) {
    const isProduction = 
      window.location.protocol === 'https:' || 
      (!window.location.hostname.includes('localhost') && 
       !window.location.hostname.includes('127.0.0.1'));
    
    if (isProduction) {
      // Use relative URL in production - ONLY works if there's a reverse proxy
      // routing /api/* to the backend, or if API is on same domain
      // If you see HTML errors instead of JSON, set VITE_API_URL at build time!
      console.error('❌ VITE_API_URL not set in production build! Using relative URLs which may not work.');
      console.error('💡 To fix: Set VITE_API_URL environment variable BEFORE running npm run build');
      return '';
    }
  }
  
  // Default to localhost for development
  // This is safe because in development, we're always on localhost
  console.log('🔧 Using development default: http://localhost:8001');
  return 'http://localhost:8001';
}

/**
 * Get the full API URL for a given endpoint
 * @param endpoint - API endpoint path (e.g., '/api/bulk-import/jobs')
 * @returns Full URL or relative path
 */
export function getApiUrl(endpoint: string): string {
  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  if (!baseUrl) {
    // Return relative URL
    return cleanEndpoint;
  }
  
  // Remove trailing slash from baseUrl if present
  const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  return `${cleanBaseUrl}${cleanEndpoint}`;
}

