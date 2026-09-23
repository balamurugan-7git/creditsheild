// ============================================================
// CrediShield AI – Applications API Functions
// ============================================================

import apiClient from './client';
import type {
  Application,
  ApplicationListResponse,
  LoanApplicationInput,
  OverrideRequest,
} from '@/types';

/**
 * Submit a new loan application for AI scoring.
 * Returns the scored Application including probability and SHAP factors.
 */
export async function submitApplication(data: LoanApplicationInput): Promise<Application> {
  const response = await apiClient.post<Application>('/applications/', data);
  return response.data;
}

/**
 * Retrieve a paginated list of applications.
 * Applicants see their own; officers see all.
 */
export async function getApplications(
  skip = 0,
  limit = 20,
): Promise<ApplicationListResponse> {
  const response = await apiClient.get<ApplicationListResponse>('/applications/', {
    params: { skip, limit },
  });
  return response.data;
}

/**
 * Retrieve a single application by ID.
 */
export async function getApplication(id: number): Promise<Application> {
  const response = await apiClient.get<Application>(`/applications/${id}`);
  return response.data;
}

/**
 * Loan officer override for an application's AI decision.
 * @param id       Application ID
 * @param data     Override decision + reason
 */
export async function overrideApplication(
  id: number,
  data: OverrideRequest,
): Promise<Application> {
  const response = await apiClient.patch<Application>(`/applications/${id}/override`, data);
  return response.data;
}
