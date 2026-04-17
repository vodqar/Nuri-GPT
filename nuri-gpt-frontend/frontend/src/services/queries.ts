import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTemplates,
  getUserUsage,
  getJournals,
  getBootstrap,
  deleteTemplate,
  updateTemplate,
  updateTemplateOrder,
  createTemplate,
  deleteJournalGroup,
} from './api';
// ── Query Keys ──

export const queryKeys = {
  bootstrap: ['bootstrap'] as const,
  templates: ['templates'] as const,
  usage: ['usage'] as const,
  journals: (limit?: number, offset?: number) => ['journals', limit, offset] as const,
};

// ── Query Hooks ──

export function useTemplates() {
  return useQuery({
    queryKey: queryKeys.templates,
    queryFn: getTemplates,
    staleTime: 60_000,
  });
}

interface UsageDetail {
  used_today: number;
  limit_today: number;
  next_reset_kst: string;
}

interface UserUsageResponse {
  plan: string;
  features: {
    [key: string]: UsageDetail;
  };
}

export function useUserUsage() {
  return useQuery<UserUsageResponse>({
    queryKey: queryKeys.usage,
    queryFn: () => getUserUsage<UserUsageResponse>(),
    staleTime: 60_000,
  });
}

export function useJournals(limit = 20, offset = 0) {
  return useQuery({
    queryKey: queryKeys.journals(limit, offset),
    queryFn: () => getJournals(limit, offset),
    staleTime: 30_000,
  });
}

// ── Mutation Hooks ──

export function useDeleteTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string } }) =>
      updateTemplate(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });
}

export function useUpdateTemplateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateTemplateOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });
}

export function useDeleteJournalGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteJournalGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journals'] });
    },
  });
}

// ── Bootstrap Hook ──

interface BootstrapData {
  user: unknown;
  templates: unknown[];
  usage: UserUsageResponse;
}

export function useBootstrap() {
  return useQuery<BootstrapData>({
    queryKey: queryKeys.bootstrap,
    queryFn: () => getBootstrap<BootstrapData>(),
    staleTime: 60_000,
  });
}

// ── Prefetch Helpers ──

/** 라우트 전환 시 데이터를 미리 로드하여 체감 0ms 달성 */
export function prefetchRouteData(queryClient: import('@tanstack/react-query').QueryClient, route: string) {
  if (route.startsWith('/observations/history')) {
    queryClient.prefetchQuery({ queryKey: queryKeys.journals(20, 0), queryFn: () => getJournals(20, 0), staleTime: 30_000 });
  }
  if (route.startsWith('/observations')) {
    queryClient.prefetchQuery({ queryKey: queryKeys.templates, queryFn: getTemplates, staleTime: 60_000 });
  }
  if (route.startsWith('/settings/account')) {
    queryClient.prefetchQuery({ queryKey: queryKeys.usage, queryFn: () => getUserUsage(), staleTime: 60_000 });
  }
}

/** 로그인 성공 직후 bootstrap 데이터를 prefetch하여 첫 페이지 체감 로딩 최소화 */
export function prefetchBootstrap(queryClient: import('@tanstack/react-query').QueryClient) {
  queryClient.prefetchQuery({
    queryKey: queryKeys.bootstrap,
    queryFn: () => getBootstrap(),
    staleTime: 60_000,
  });
}
