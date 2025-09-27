/**
 * Environment configuration utility
 * Provides type-safe access to environment variables
 */

export enum Environment {
  DEVELOPMENT = 'development',
  STAGING = 'staging',
  PRODUCTION = 'production'
}

export const env = {
  // Backend configuration
  backendHost: process.env.NEXT_PUBLIC_BACKEND_HOST || process.env.BACKEND_HOST || 'http://localhost:8000',
  // Environment info
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',

  // API endpoints
  api: {
    baseUrl: process.env.NEXT_PUBLIC_BACKEND_HOST || process.env.BACKEND_HOST || 'http://localhost:8000',
    timeout: 10000, // 10 seconds
  }
} as const;

export type EnvironmentConfig = typeof env;

// Helper function to get API URL
export function getApiUrl(endpoint: string): string {
  const baseUrl = env.api.baseUrl;
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
}

// Helper function to check if we're in a specific environment
export function isEnvironment(envName: Environment): boolean {
  if (envName === Environment.DEVELOPMENT) return env.isDevelopment;
  if (envName === Environment.PRODUCTION) return env.isProduction;
  // For staging, we check if it's production but with staging host
  if (envName === Environment.STAGING) {
    return env.isProduction && env.backendHost.includes('staging');
  }
  return false;
}

// Helper function to get current environment
export function getCurrentEnvironment(): Environment {
  if (env.isDevelopment) return Environment.DEVELOPMENT;
  if (env.isProduction && env.backendHost.includes('staging')) return Environment.STAGING;
  if (env.isProduction) return Environment.PRODUCTION;
  return Environment.DEVELOPMENT; // fallback
}