// ============================================================
// CrediShield AI – React Query Hooks for Applications
// ============================================================

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  submitApplication,
  getApplications,
  getApplication,
  overrideApplication,
} from '@/api/applications';
import type {
  Application,
  ApplicationListResponse,
  LoanApplicationInput,
  OverrideRequest,
} from '@/types';

// ---- Query key factories ---- //
export const applicationKeys = {
  all: ['applications'] as const,
  lists: () => [...applicationKeys.all, 'list'] as const,
  list: (skip: number, limit: number) =>
    [...applicationKeys.lists(), { skip, limit }] as const,
  details: () => [...applicationKeys.all, 'detail'] as const,
  detail: (id: number) => [...applicationKeys.details(), id] as const,
};

// ============================================================
// Submit a new loan application (mutation)
// ============================================================
export function usePrediction() {
  const queryClient = useQueryClient();

  const mutation = useMutation<Application, Error, LoanApplicationInput>({
    mutationFn: (data: LoanApplicationInput) => submitApplication(data),
    onSuccess: () => {
      // Invalidate the applications list so it refreshes
      void queryClient.invalidateQueries({ queryKey: applicationKeys.lists() });
    },
  });

  return {
    mutate: mutation.mutate,
    mutateAsync: mutation.mutateAsync,
    isLoading: mutation.isPending,
    data: mutation.data,
    error: mutation.error,
    reset: mutation.reset,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
  };
}

// ============================================================
// Fetch a paginated list of applications
// ============================================================
export function useApplications(skip = 0, limit = 20) {
  return useQuery<ApplicationListResponse, Error>({
    queryKey: applicationKeys.list(skip, limit),
    queryFn: () => getApplications(skip, limit),
    placeholderData: (prev) => prev, // keep stale data while fetching
  });
}

// ============================================================
// Fetch a single application by ID
// ============================================================
export function useApplication(id: number) {
  return useQuery<Application, Error>({
    queryKey: applicationKeys.detail(id),
    queryFn: () => getApplication(id),
    enabled: id > 0,
  });
}

// ============================================================
// Override an application's decision (mutation)
// ============================================================
export function useOverrideApplication(applicationId: number) {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    Application,
    Error,
    OverrideRequest
  >({
    mutationFn: (data: OverrideRequest) => overrideApplication(applicationId, data),
    onSuccess: (updated) => {
      // Update the cached detail and invalidate list
      queryClient.setQueryData(applicationKeys.detail(applicationId), updated);
      void queryClient.invalidateQueries({ queryKey: applicationKeys.lists() });
    },
  });

  return {
    mutate: mutation.mutate,
    mutateAsync: mutation.mutateAsync,
    isLoading: mutation.isPending,
    data: mutation.data,
    error: mutation.error,
    reset: mutation.reset,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
  };
}
