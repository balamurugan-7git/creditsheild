// ============================================================
// CrediShield AI – Auth API Functions
// ============================================================

import apiClient from './client';
import type { AuthTokens, User, UserRole } from '@/types';

/**
 * Authenticate a user with email + password.
 * Uses form-encoded body as required by OAuth2 password flow.
 */
export async function loginUser(email: string, password: string): Promise<AuthTokens> {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await apiClient.post<AuthTokens>('/auth/token', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
}

/**
 * Register a new user account.
 */
export async function registerUser(
  email: string,
  password: string,
  fullName: string,
  role: UserRole,
): Promise<User> {
  const response = await apiClient.post<User>('/auth/register', {
    email,
    password,
    full_name: fullName,
    role,
  });
  return response.data;
}

/**
 * Fetch the currently authenticated user's profile.
 * Requires a valid Bearer token in the request header.
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
}
