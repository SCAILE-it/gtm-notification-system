// ABOUTME: Resend webhook handler - updates notification_logs with delivery events
// ABOUTME: Handles: email.delivered, email.opened, email.clicked, email.bounced, email.complained

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { Webhook } from 'https://esm.sh/standardwebhooks@1.0.0'
import { corsHeaders } from '../_shared/cors.ts'

interface ResendWebhookEvent {
  type: 'email.sent' | 'email.delivered' | 'email.delivery_delayed' | 'email.complained' | 'email.bounced' | 'email.opened' | 'email.clicked'
  created_at: string
  data: {
    created_at: string
    email_id: string
    from: string
    to: string[]
    subject?: string
    click?: {
      ipAddress: string
      link: string
      timestamp: string
      userAgent: string
    }
    // ... other fields
  }
}

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('[Resend Webhook] Received request')

    // Get webhook secret from environment
    const webhookSecret = Deno.env.get('RESEND_WEBHOOK_SECRET')
    if (!webhookSecret) {
      console.error('[Resend Webhook] RESEND_WEBHOOK_SECRET not configured')
      return new Response(
        JSON.stringify({ error: 'Webhook secret not configured' }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Get request body and headers for verification
    const payload = await req.text()
    const headers = {
      'svix-id': req.headers.get('svix-id') || '',
      'svix-timestamp': req.headers.get('svix-timestamp') || '',
      'svix-signature': req.headers.get('svix-signature') || '',
    }

    console.log('[Resend Webhook] Headers:', JSON.stringify(headers))

    // Verify webhook signature
    const wh = new Webhook(webhookSecret)
    let event: ResendWebhookEvent

    try {
      event = wh.verify(payload, headers) as ResendWebhookEvent
      console.log('[Resend Webhook] Signature verified ✓')
    } catch (err) {
      console.error('[Resend Webhook] Signature verification failed:', err.message)
      return new Response(
        JSON.stringify({ error: 'Invalid signature' }),
        {
          status: 401,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    console.log(`[Resend Webhook] Event type: ${event.type}, email_id: ${event.data.email_id}`)

    // Initialize Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Map event type to status and timestamp field
    const eventType = event.type.replace('email.', '') // 'delivered', 'opened', etc.
    const timestampField = `${eventType}_at`

    // Prepare update data
    const updateData: any = {
      status: eventType,
      [timestampField]: new Date(event.created_at).toISOString(),
      resend_event_data: event.data
    }

    console.log(`[Resend Webhook] Updating notification_logs for email_id=${event.data.email_id}`)

    // Update notification_logs table
    const { data, error } = await supabase
      .from('notification_logs')
      .update(updateData)
      .eq('email_id', event.data.email_id)
      .select()

    if (error) {
      console.error('[Resend Webhook] Database update failed:', error)
      return new Response(
        JSON.stringify({ error: error.message }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    if (!data || data.length === 0) {
      console.warn(`[Resend Webhook] No matching notification log found for email_id=${event.data.email_id}`)
      // Not an error - webhook might arrive before we log the email
      return new Response('OK (no match)', { headers: corsHeaders })
    }

    console.log(`[Resend Webhook] Successfully updated ${data.length} row(s)`)
    console.log(`[Resend Webhook] Updated status: ${eventType}, timestamp: ${updateData[timestampField]}`)

    return new Response(
      JSON.stringify({ success: true, updated: data.length }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('[Resend Webhook] Unexpected error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

/* Test with curl:

curl -X POST https://[project].supabase.co/functions/v1/resend-webhook \
  -H "Content-Type: application/json" \
  -H "svix-id: test-id" \
  -H "svix-timestamp: 1234567890" \
  -H "svix-signature: test-signature" \
  -d '{
    "type": "email.delivered",
    "created_at": "2025-01-28T10:00:00Z",
    "data": {
      "created_at": "2025-01-28T10:00:00Z",
      "email_id": "test-email-123",
      "from": "jobs@gtmpowerapp.com",
      "to": ["user@example.com"],
      "subject": "Test Email"
    }
  }'

*/
