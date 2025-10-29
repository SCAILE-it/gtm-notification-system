-- Mock Auth Schema for Local Testing
-- ABOUTME: Creates minimal auth schema for Docker Compose testing without full Supabase stack
-- ABOUTME: This allows notification_preferences and notification_logs to reference auth.users

-- =============================================================================
-- CREATE AUTH SCHEMA & ROLES
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS auth;

-- Create PostgreSQL roles needed by PostgREST
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN BYPASSRLS;
  END IF;
END $$;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;

-- =============================================================================
-- MOCK AUTH.USERS TABLE
-- =============================================================================

-- Minimal auth.users table structure for testing
-- Only includes fields needed by notification system
CREATE TABLE IF NOT EXISTS auth.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  email_confirmed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  raw_user_meta_data JSONB DEFAULT '{}'::jsonb,
  is_super_admin BOOLEAN DEFAULT false
);

-- Index for fast email lookups
CREATE INDEX IF NOT EXISTS idx_auth_users_email
  ON auth.users(email);

-- =============================================================================
-- MOCK AUTH HELPER FUNCTIONS
-- =============================================================================

-- Mock auth.uid() function for RLS policies
-- In real Supabase, this returns the current user's ID from JWT
-- For testing, we'll return NULL (which means RLS policies won't work in local tests)
CREATE OR REPLACE FUNCTION auth.uid()
RETURNS UUID AS $$
BEGIN
  RETURN NULL;  -- In local testing, we bypass RLS by using service role
END;
$$ LANGUAGE plpgsql STABLE;

-- Mock auth.role() function for RLS policies
-- For testing, always return 'service_role' to bypass RLS
CREATE OR REPLACE FUNCTION auth.role()
RETURNS TEXT AS $$
BEGIN
  RETURN 'service_role';  -- Bypass RLS in local testing
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================================================
-- SEED TEST USERS
-- =============================================================================

-- Insert a few test users for integration testing
INSERT INTO auth.users (id, email, email_confirmed_at)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'test-user-1@example.com', NOW()),
  ('00000000-0000-0000-0000-000000000002', 'test-user-2@example.com', NOW()),
  ('00000000-0000-0000-0000-000000000003', 'test-user-3@example.com', NULL)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
  ASSERT (SELECT COUNT(*) FROM auth.users) >= 3,
         'Mock auth setup failed: no test users created';

  RAISE NOTICE '✅ Mock auth schema created';
  RAISE NOTICE '✅ Created auth.users table with 3 test users';
  RAISE NOTICE '✅ Created auth.uid() and auth.role() functions';
  RAISE NOTICE '⚠️  NOTE: This is a MOCK for local testing only';
  RAISE NOTICE '⚠️  In production, use real Supabase Auth';
END $$;
