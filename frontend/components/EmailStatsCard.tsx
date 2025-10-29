/**
 * Email Stats Card Component
 *
 * Displays email delivery statistics and recent notification history.
 * Standalone component that can be dropped into any dashboard.
 *
 * Usage:
 *   import { EmailStatsCard } from '@/components/notifications/EmailStatsCard'
 *   import { createClient } from '@/lib/supabase/client'
 *
 *   export default function DashboardPage() {
 *     const supabase = createClient()
 *     return <EmailStatsCard supabaseClient={supabase} />
 *   }
 */

'use client'

import { useState, useEffect } from 'react'
import type { SupabaseClient } from '@supabase/supabase-js'

// UI Components
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

interface EmailStatsCardProps {
  supabaseClient: SupabaseClient
  userId?: string
  limit?: number  // Number of recent emails to show
}

interface EmailLog {
  id: string
  notification_type: string
  subject: string
  recipient_email: string
  status: string
  sent_at: string
  delivered_at: string | null
  opened_at: string | null
  clicked_at: string | null
  bounced_at: string | null
  complained_at: string | null
}

interface Stats {
  total_sent: number
  delivered: number
  opened: number
  clicked: number
  bounced: number
  complained: number
  failed: number
}

export function EmailStatsCard({ supabaseClient, userId: propUserId, limit = 10 }: EmailStatsCardProps) {
  const [stats, setStats] = useState<Stats>({
    total_sent: 0,
    delivered: 0,
    opened: 0,
    clicked: 0,
    bounced: 0,
    complained: 0,
    failed: 0
  })
  const [recentEmails, setRecentEmails] = useState<EmailLog[]>([])
  const [loading, setLoading] = useState(true)
  const [userId, setUserId] = useState<string | null>(propUserId || null)

  useEffect(() => {
    async function loadStats() {
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

        const userIdToFetch = propUserId || userId
        if (!userIdToFetch) return

        // Fetch notification logs
        const { data: logs, error } = await supabaseClient
          .from('notification_logs')
          .select('*')
          .eq('user_id', userIdToFetch)
          .order('created_at', { ascending: false })
          .limit(limit)

        if (error) {
          console.error('Failed to load notification logs:', error)
          return
        }

        if (logs && logs.length > 0) {
          setRecentEmails(logs)

          // Calculate stats
          setStats({
            total_sent: logs.length,
            delivered: logs.filter(l => l.delivered_at).length,
            opened: logs.filter(l => l.opened_at).length,
            clicked: logs.filter(l => l.clicked_at).length,
            bounced: logs.filter(l => l.bounced_at).length,
            complained: logs.filter(l => l.complained_at).length,
            failed: logs.filter(l => l.status === 'failed').length
          })
        }
      } catch (error) {
        console.error('Error loading email stats:', error)
      } finally {
        setLoading(false)
      }
    }

    loadStats()
  }, [supabaseClient, propUserId, userId, limit])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Email Activity</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        </CardContent>
      </Card>
    )
  }

  const deliveryRate = stats.total_sent > 0 ? (stats.delivered / stats.total_sent) * 100 : 0
  const openRate = stats.delivered > 0 ? (stats.opened / stats.delivered) * 100 : 0
  const clickRate = stats.opened > 0 ? (stats.clicked / stats.opened) * 100 : 0

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Sent"
          value={stats.total_sent}
          variant="default"
        />
        <StatCard
          label="Delivered"
          value={stats.delivered}
          percentage={deliveryRate}
          variant="success"
        />
        <StatCard
          label="Opened"
          value={stats.opened}
          percentage={openRate}
          variant="info"
        />
        <StatCard
          label="Clicked"
          value={stats.clicked}
          percentage={clickRate}
          variant="primary"
        />
      </div>

      {stats.bounced > 0 || stats.failed > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {stats.bounced > 0 && (
            <StatCard
              label="Bounced"
              value={stats.bounced}
              variant="destructive"
            />
          )}
          {stats.failed > 0 && (
            <StatCard
              label="Failed"
              value={stats.failed}
              variant="destructive"
            />
          )}
        </div>
      ) : null}

      {/* Recent Emails Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Notifications</CardTitle>
          <CardDescription>Last {limit} email notifications</CardDescription>
        </CardHeader>
        <CardContent>
          {recentEmails.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No notifications sent yet
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentEmails.map((email) => (
                  <TableRow key={email.id}>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(email.sent_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {email.notification_type.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      {email.subject}
                    </TableCell>
                    <TableCell>
                      <EmailStatusBadge email={email} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Individual stat card
function StatCard({
  label,
  value,
  percentage,
  variant = 'default'
}: {
  label: string
  value: number
  percentage?: number
  variant?: 'default' | 'success' | 'info' | 'primary' | 'destructive'
}) {
  const colors = {
    default: 'text-foreground',
    success: 'text-green-600 dark:text-green-400',
    info: 'text-blue-600 dark:text-blue-400',
    primary: 'text-violet-600 dark:text-violet-400',
    destructive: 'text-red-600 dark:text-red-400'
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div className={`text-3xl font-bold mt-2 ${colors[variant]}`}>
          {value.toLocaleString()}
        </div>
        {percentage !== undefined && (
          <div className="text-xs text-muted-foreground mt-1">
            {percentage.toFixed(1)}%
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Email status badge with appropriate color
function EmailStatusBadge({ email }: { email: EmailLog }) {
  if (email.bounced_at) {
    return <Badge variant="destructive">Bounced</Badge>
  }

  if (email.complained_at) {
    return <Badge variant="destructive">Spam</Badge>
  }

  if (email.status === 'failed') {
    return <Badge variant="destructive">Failed</Badge>
  }

  if (email.clicked_at) {
    return <Badge variant="default" className="bg-violet-600 text-white">Clicked</Badge>
  }

  if (email.opened_at) {
    return <Badge variant="default" className="bg-blue-600 text-white">Opened</Badge>
  }

  if (email.delivered_at) {
    return <Badge variant="secondary">Delivered</Badge>
  }

  return <Badge variant="outline">Sent</Badge>
}
