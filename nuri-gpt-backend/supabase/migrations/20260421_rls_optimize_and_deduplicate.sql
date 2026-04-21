-- =============================================================================
-- Step 1: RLS 정책 최적화 — auth.uid() → (select auth.uid())
-- Supabase Performance Advisor auth_rls_initplan WARN 해소
-- =============================================================================

-- observation_journals
ALTER POLICY "Users can manage their own journals"
  ON observation_journals
  USING ((select auth.uid()) = user_id);

-- templates
ALTER POLICY "Users can manage their own templates"
  ON templates
  USING ((select auth.uid()) = user_id);

-- user_logs
ALTER POLICY "Users can delete their own logs"
  ON user_logs
  USING ((select auth.uid()) = user_id);

ALTER POLICY "Users can insert their own logs"
  ON user_logs
  WITH CHECK ((select auth.uid()) = user_id);

ALTER POLICY "Users can read their own logs"
  ON user_logs
  USING ((select auth.uid()) = user_id);

-- user_preferences
ALTER POLICY "Users can delete own preferences"
  ON user_preferences
  USING ((select auth.uid()) = user_id);

ALTER POLICY "Users can read own preferences"
  ON user_preferences
  USING ((select auth.uid()) = user_id);

-- user_usages
ALTER POLICY "Users can insert their own usage"
  ON user_usages
  WITH CHECK ((select auth.uid()) = user_id);

ALTER POLICY "Users can read their own usage"
  ON user_usages
  USING ((select auth.uid()) = user_id);

ALTER POLICY "Users can update their own usage"
  ON user_usages
  USING ((select auth.uid()) = user_id)
  WITH CHECK ((select auth.uid()) = user_id);

-- users
ALTER POLICY "Users can manage their own profile"
  ON users
  USING ((select auth.uid()) = id);


-- =============================================================================
-- Step 2: 중복 RLS 정책 병합 — ALL 정책 삭제 (개별 정책 유지)
-- Supabase Performance Advisor multiple_permissive_policies WARN 해소
-- =============================================================================

-- observation_journals: ALL 정책 삭제, 개별 DELETE/INSERT/UPDATE/SELECT 유지
DROP POLICY IF EXISTS "Users can manage their own journals" ON observation_journals;

-- templates: ALL 정책 삭제, 개별 DELETE/INSERT/UPDATE/SELECT 유지
DROP POLICY IF EXISTS "Users can manage their own templates" ON templates;

-- users: ALL 정책 삭제, 개별 INSERT/UPDATE/SELECT 유지
DROP POLICY IF EXISTS "Users can manage their own profile" ON users;

-- 중복 SELECT 정책 삭제 (read vs view 동일 액션)
-- user_logs: "read" 삭제, "view" 유지 (이미 최적화됨)
DROP POLICY IF EXISTS "Users can read their own logs" ON user_logs;

-- user_preferences: "read" 삭제, "view" 유지 (이미 최적화됨)
DROP POLICY IF EXISTS "Users can read own preferences" ON user_preferences;

-- user_usages: "read" 삭제, "view" 유지 (이미 최적화됨)
DROP POLICY IF EXISTS "Users can read their own usage" ON user_usages;
