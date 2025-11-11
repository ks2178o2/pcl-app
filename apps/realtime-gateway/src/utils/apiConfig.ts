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
 * 1. Use VITE_API_URL if explicitly set (build-time environment variable)
 * 2. In production (https or non-localhost), use empty string for relative URLs
 * 3. In development, default to http://localhost:8001
 */
export function getApiBaseUrl(): string {
  // Check if VITE_API_URL is explicitly set at build time
  // Vite replaces import.meta.env.VITE_* at build time
  const envApiUrl = import.meta.env?.VITE_API_URL as string | undefined;
  
  if (envApiUrl && envApiUrl.trim() !== '') {
    return envApiUrl.trim();
  }
  
  // If no explicit URL is set, check if we're in production
  // Production is detected by checking window.location (browser only)
  if (typeof window !== 'undefined' && window.location) {
    const isProduction = 
      window.location.protocol === 'https:' || 
      (!window.location.hostname.includes('localhost') && 
       !window.location.hostname.includes('127.0.0.1'));
    
    if (isProduction) {
      // Use relative URL in production - API is served from same domain
      // This avoids CORS issues when frontend and backend are on the same domain
      return '';
    }
  }
  
  // Default to localhost for development
  // This is safe because in development, we're always on localhost
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

