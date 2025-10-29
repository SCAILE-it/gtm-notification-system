/**
 * Notification Preferences Component
 *
 * Standalone React component for managing user notification preferences.
 * Can be dropped into any Next.js app with Supabase.
 *
 * Usage:
 *   import { NotificationPreferences } from '@/components/notifications/NotificationPreferences'
 *   import { createClient } from '@/lib/supabase/client'
 *
 *   export default function NotificationsPage() {
 *     const supabase = createClient()
 *     return <NotificationPreferences supabaseClient={supabase} />
 *   }
 */

'use client'

import { useState, useEffect } from 'react'
import type { SupabaseClient } from '@supabase/supabase-js'

// UI Components (assuming shadcn/ui)
// Replace these imports with your UI library
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'

interface NotificationPreferencesProps {
  supabaseClient: SupabaseClient
  userId?: string // Optional: if not provided, will fetch from auth
}

interface Preferences {
  email_job_complete: boolean
  email_job_failed: boolean
  email_quota_warning: boolean
  email_quota_exceeded: boolean
  email_weekly_summary: boolean
  inapp_job_complete: boolean
  inapp_job_failed: boolean
  digest_frequency: 'realtime' | 'hourly' | 'daily' | 'never'
}

const defaultPreferences: Preferences = {
  email_job_complete: true,
  email_job_failed: true,
  email_quota_warning: true,
  email_quota_exceeded: true,
  email_weekly_summary: false,
  inapp_job_complete: true,
  inapp_job_failed: true,
  digest_frequency: 'realtime'
}

export function NotificationPreferences({ supabaseClient, userId: propUserId }: NotificationPreferencesProps) {
  const [preferences, setPreferences] = useState<Preferences>(defaultPreferences)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [userId, setUserId] = useState<string | null>(propUserId || null)

  // Load user ID and preferences
  useEffect(() => {
    async function loadData() {
      try {
        // Get user ID if not provided
        if (!propUserId) {
          const { data: { user }, error: userError } = await supabaseClient.auth.getUser()
          if (userError) throw userError
          if (!user) throw new Error('Not authenticated')
          setUserId(user.id)
        } else {
          setUserId(propUserId)
        }

        // Load preferences
        const userIdToFetch = propUserId || userId
        if (!userIdToFetch) return

        const { data, error } = await supabaseClient
          .from('notification_preferences')
          .select('*')
          .eq('user_id', userIdToFetch)
          .single()

        if (error && error.code !== 'PGRST116') { // PGRST116 = no rows returned
          console.error('Failed to load preferences:', error)
          toast.error('Failed to load preferences')
        }

        if (data) {
          setPreferences({
            email_job_complete: data.email_job_complete,
            email_job_failed: data.email_job_failed,
            email_quota_warning: data.email_quota_warning,
            email_quota_exceeded: data.email_quota_exceeded,
            email_weekly_summary: data.email_weekly_summary,
            inapp_job_complete: data.inapp_job_complete,
            inapp_job_failed: data.inapp_job_failed,
            digest_frequency: data.digest_frequency
          })
        }
      } catch (error) {
        console.error('Error loading preferences:', error)
        toast.error('Failed to load preferences')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [supabaseClient, propUserId, userId])

  // Save preferences
  async function savePreferences() {
    if (!userId) {
      toast.error('Not authenticated')
      return
    }

    setSaving(true)

    try {
      const { error } = await supabaseClient
        .from('notification_preferences')
        .upsert({
          user_id: userId,
          ...preferences,
          updated_at: new Date().toISOString()
        })

      if (error) throw error

      toast.success('Preferences saved successfully')
    } catch (error) {
      console.error('Error saving preferences:', error)
      toast.error('Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  // Update preference
  function updatePreference<K extends keyof Preferences>(key: K, value: Preferences[K]) {
    setPreferences(prev => ({ ...prev, [key]: value }))
  }

  if (loading) {
    return (
      <Card className="max-w-2xl">
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-8">
            <div className="text-muted-foreground">Loading preferences...</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Notification Preferences</CardTitle>
        <CardDescription>
          Choose which emails and notifications you'd like to receive
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Email Notifications Section */}
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold">Email Notifications</h3>
            <p className="text-sm text-muted-foreground">
              Get notified about important events via email
            </p>
          </div>

          <div className="space-y-4">
            <PreferenceToggle
              label="Job completed successfully"
              description="Get notified when your jobs finish processing"
              checked={preferences.email_job_complete}
              onCheckedChange={(checked) => updatePreference('email_job_complete', checked)}
            />

            <PreferenceToggle
              label="Job failed or encountered errors"
              description="Alert me when jobs fail to complete"
              checked={preferences.email_job_failed}
              onCheckedChange={(checked) => updatePreference('email_job_failed', checked)}
            />

            <PreferenceToggle
              label="Quota warning (80% used)"
              description="Warn me before I hit my monthly limit"
              checked={preferences.email_quota_warning}
              onCheckedChange={(checked) => updatePreference('email_quota_warning', checked)}
            />

            <PreferenceToggle
              label="Quota exceeded"
              description="Alert me when quota is exceeded"
              checked={preferences.email_quota_exceeded}
              onCheckedChange={(checked) => updatePreference('email_quota_exceeded', checked)}
            />

            <PreferenceToggle
              label="Weekly summary report"
              description="Receive a weekly digest of your activity"
              checked={preferences.email_weekly_summary}
              onCheckedChange={(checked) => updatePreference('email_weekly_summary', checked)}
            />
          </div>
        </div>

        <Separator />

        {/* In-App Notifications Section */}
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold">In-App Notifications</h3>
            <p className="text-sm text-muted-foreground">
              Toast notifications while using the app
            </p>
          </div>

          <div className="space-y-4">
            <PreferenceToggle
              label="Job completed"
              description="Show toast notification when jobs complete"
              checked={preferences.inapp_job_complete}
              onCheckedChange={(checked) => updatePreference('inapp_job_complete', checked)}
            />

            <PreferenceToggle
              label="Job failed"
              description="Show toast notification when jobs fail"
              checked={preferences.inapp_job_failed}
              onCheckedChange={(checked) => updatePreference('inapp_job_failed', checked)}
            />
          </div>
        </div>

        <Separator />

        {/* Digest Settings Section */}
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold">Notification Timing</h3>
            <p className="text-sm text-muted-foreground">
              Choose how often to receive notifications
            </p>
          </div>

          <div className="space-y-2">
            <DigestOption
              label="Immediately (realtime)"
              description="Send notifications as events happen"
              value="realtime"
              selected={preferences.digest_frequency === 'realtime'}
              onSelect={() => updatePreference('digest_frequency', 'realtime')}
            />
            <DigestOption
              label="Hourly digest"
              description="Batch notifications every hour"
              value="hourly"
              selected={preferences.digest_frequency === 'hourly'}
              onSelect={() => updatePreference('digest_frequency', 'hourly')}
            />
            <DigestOption
              label="Daily digest (9am)"
              description="Receive one email per day with all updates"
              value="daily"
              selected={preferences.digest_frequency === 'daily'}
              onSelect={() => updatePreference('digest_frequency', 'daily')}
            />
            <DigestOption
              label="Never"
              description="Disable all notifications"
              value="never"
              selected={preferences.digest_frequency === 'never'}
              onSelect={() => updatePreference('digest_frequency', 'never')}
            />
          </div>
        </div>
      </CardContent>

      <CardFooter>
        <Button onClick={savePreferences} disabled={saving}>
          {saving ? 'Saving...' : 'Save Preferences'}
        </Button>
      </CardFooter>
    </Card>
  )
}

// Helper component for toggle preferences
function PreferenceToggle({
  label,
  description,
  checked,
  onCheckedChange
}: {
  label: string
  description: string
  checked: boolean
  onCheckedChange: (checked: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex-1 space-y-0.5">
        <Label className="text-base">{label}</Label>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <Switch
        checked={checked}
        onCheckedChange={onCheckedChange}
      />
    </div>
  )
}

// Helper component for digest radio options
function DigestOption({
  label,
  description,
  value,
  selected,
  onSelect
}: {
  label: string
  description: string
  value: string
  selected: boolean
  onSelect: () => void
}) {
  return (
    <div
      className={`
        flex items-start gap-3 rounded-lg border p-4 cursor-pointer transition-colors
        ${selected ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}
      `}
      onClick={onSelect}
    >
      <div className="mt-0.5">
        <div className={`
          h-4 w-4 rounded-full border-2 flex items-center justify-center
          ${selected ? 'border-primary' : 'border-border'}
        `}>
          {selected && (
            <div className="h-2 w-2 rounded-full bg-primary" />
          )}
        </div>
      </div>
      <div className="flex-1 space-y-0.5">
        <Label className="cursor-pointer text-base">{label}</Label>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  )
}
