-- GTM Notification System - Database Schema
-- Version: 1.0
-- Date: 2025-01-28
-- Description: Notification preferences and audit logging tables

-- =============================================================================
-- NOTIFICATION PREFERENCES TABLE
-- =============================================================================

-- User notification preferences (opt-in/opt-out for each notification type)
CREATE TABLE IF NOT EXISTS notification_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE NOT NULL,

  -- Email notification toggles
  email_job_complete BOOLEAN DEFAULT true NOT NULL,
  email_job_failed BOOLEAN DEFAULT true NOT NULL,
  email_quota_warning BOOLEAN DEFAULT true NOT NULL,
  email_quota_exceeded BOOLEAN DEFAULT true NOT NULL,
  email_weekly_summary BOOLEAN DEFAULT false NOT NULL,

  -- Future: In-app notifications
  inapp_job_complete BOOLEAN DEFAULT true NOT NULL,
  inapp_job_failed BOOLEAN DEFAULT true NOT NULL,

  -- Digest settings (future feature)
  digest_frequency TEXT CHECK (digest_frequency IN ('realtime', 'hourly', 'daily', 'never')) DEFAULT 'realtime' NOT NULL,

  -- Metadata
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index for fast user lookups
CREATE INDEX IF NOT EXISTS idx_notification_prefs_user_id
  ON notification_preferences(user_id);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_notification_prefs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_notification_prefs_timestamp
  BEFORE UPDATE ON notification_preferences
  FOR EACH ROW
  EXECUTE FUNCTION update_notification_prefs_updated_at();

-- =============================================================================
-- NOTIFICATION LOGS TABLE
-- =============================================================================

-- Audit trail for all sent notifications with delivery tracking
CREATE TABLE IF NOT EXISTS notification_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,

  -- Notification details
  notification_type TEXT NOT NULL CHECK (notification_type IN (
    'job_complete',
    'job_failed',
    'quota_warning',
    'quota_exceeded',
    'welcome',
    'verify',
    'weekly_summary'
  )),

  -- Email details
  email_id TEXT UNIQUE,  -- Resend email ID (e.g., "email_abc123xyz")
  recipient_email TEXT NOT NULL,
  subject TEXT NOT NULL,

  -- Delivery tracking (updated by Resend webhooks)
  sent_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  delivered_at TIMESTAMPTZ,
  opened_at TIMESTAMPTZ,
  clicked_at TIMESTAMPTZ,
  bounced_at TIMESTAMPTZ,
  complained_at TIMESTAMPTZ,  -- User marked as spam

  -- Current status
  status TEXT DEFAULT 'sent' CHECK (status IN (
    'sent',
    'delivered',
    'opened',
    'clicked',
    'bounced',
    'complained',
    'failed'
  )),

  -- Additional metadata
  resend_event_data JSONB,  -- Full webhook payload from Resend
  job_id UUID,  -- Reference to workflow_executions (if applicable)

  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for analytics and queries
CREATE INDEX IF NOT EXISTS idx_notification_logs_user_id
  ON notification_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_notification_logs_email_id
  ON notification_logs(email_id);

CREATE INDEX IF NOT EXISTS idx_notification_logs_type
  ON notification_logs(notification_type);

CREATE INDEX IF NOT EXISTS idx_notification_logs_status
  ON notification_logs(status);

CREATE INDEX IF NOT EXISTS idx_notification_logs_sent_at
  ON notification_logs(sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_notification_logs_job_id
  ON notification_logs(job_id) WHERE job_id IS NOT NULL;

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Enable RLS on both tables
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;

-- Notification Preferences Policies
-- Users can only view/edit their own preferences
CREATE POLICY "Users can view their own notification preferences"
  ON notification_preferences
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own notification preferences"
  ON notification_preferences
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own notification preferences"
  ON notification_preferences
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Service role can manage all preferences (for backend operations)
CREATE POLICY "Service role can manage all notification preferences"
  ON notification_preferences
  FOR ALL
  USING (auth.role() = 'service_role');

-- Notification Logs Policies
-- Users can only view their own logs
CREATE POLICY "Users can view their own notification logs"
  ON notification_logs
  FOR SELECT
  USING (auth.uid() = user_id);

-- Service role can manage all logs (for backend logging and webhook updates)
CREATE POLICY "Service role can manage all notification logs"
  ON notification_logs
  FOR ALL
  USING (auth.role() = 'service_role');

-- =============================================================================
-- AUTO-CREATE DEFAULT PREFERENCES ON USER SIGNUP
-- =============================================================================

CREATE OR REPLACE FUNCTION create_default_notification_preferences()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO notification_preferences (user_id)
  VALUES (NEW.id)
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create preferences when user signs up
DROP TRIGGER IF EXISTS on_auth_user_created_notification_prefs ON auth.users;
CREATE TRIGGER on_auth_user_created_notification_prefs
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION create_default_notification_preferences();

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Get notification stats for a user
CREATE OR REPLACE FUNCTION get_user_notification_stats(target_user_id UUID)
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'total_sent', COUNT(*),
    'delivered', COUNT(*) FILTER (WHERE delivered_at IS NOT NULL),
    'opened', COUNT(*) FILTER (WHERE opened_at IS NOT NULL),
    'clicked', COUNT(*) FILTER (WHERE clicked_at IS NOT NULL),
    'bounced', COUNT(*) FILTER (WHERE bounced_at IS NOT NULL),
    'complained', COUNT(*) FILTER (WHERE complained_at IS NOT NULL),
    'failed', COUNT(*) FILTER (WHERE status = 'failed'),
    'by_type', json_object_agg(notification_type, type_count)
  )
  INTO result
  FROM (
    SELECT
      notification_type,
      COUNT(*) as type_count
    FROM notification_logs
    WHERE user_id = target_user_id
    GROUP BY notification_type
  ) AS type_counts,
  notification_logs
  WHERE user_id = target_user_id;

  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE notification_preferences IS 'User preferences for email and in-app notifications';
COMMENT ON TABLE notification_logs IS 'Audit trail for all sent notifications with Resend delivery tracking';

COMMENT ON COLUMN notification_preferences.digest_frequency IS 'How often to batch notifications (realtime, hourly, daily, never)';
COMMENT ON COLUMN notification_logs.email_id IS 'Resend email ID used for webhook matching';
COMMENT ON COLUMN notification_logs.resend_event_data IS 'Full JSON payload from Resend webhooks';
COMMENT ON COLUMN notification_logs.job_id IS 'Optional reference to workflow_executions table';

-- =============================================================================
-- MIGRATION VERIFICATION
-- =============================================================================

-- Verify tables were created
DO $$
BEGIN
  ASSERT (SELECT COUNT(*) FROM information_schema.tables
          WHERE table_name IN ('notification_preferences', 'notification_logs')) = 2,
         'Migration failed: tables not created';

  RAISE NOTICE 'Migration completed successfully';
  RAISE NOTICE '✅ Created: notification_preferences table';
  RAISE NOTICE '✅ Created: notification_logs table';
  RAISE NOTICE '✅ Created: RLS policies';
  RAISE NOTICE '✅ Created: auto-create trigger for new users';
  RAISE NOTICE '✅ Created: helper function get_user_notification_stats()';
END $$;
