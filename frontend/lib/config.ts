// API configuration that works for both local and production environments
export const getApiUrl = () => {
  // Prefer explicit API URL from env (set by deploy.py in .env.production.local).
  // This avoids CloudFront SPA fallback HTML being returned for some /api/* errors.
  const explicitApiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (explicitApiUrl) {
    return explicitApiUrl;
  }

  // Fallback behavior:
  // - In local dev on localhost, call local API
  // - Otherwise use relative path and CloudFront routing
  if (typeof window !== 'undefined') {
    // Client-side: check if we're on localhost
    if (window.location.hostname === 'localhost') {
      return 'http://localhost:8000';
    } else {
      // Production fallback: relative path (CloudFront handles routing /api/* to API Gateway)
      return '';
    }
  }
  // Server-side during build
  return '';
};

export const API_URL = getApiUrl();