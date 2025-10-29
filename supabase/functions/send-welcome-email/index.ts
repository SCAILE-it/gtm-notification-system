// ABOUTME: Sends welcome email to new users on signup
// ABOUTME: Triggered by database trigger on auth.users INSERT

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { Resend } from 'https://esm.sh/resend@4.0.0'
import { corsHeaders } from '../_shared/cors.ts'

interface WelcomeEmailRequest {
  user_id: string
  user_email?: string // Optional override
}

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('[Welcome Email] Received request')

    // Parse request body
    const { user_id, user_email }: WelcomeEmailRequest = await req.json()

    if (!user_id) {
      return new Response(
        JSON.stringify({ error: 'user_id is required' }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    console.log(`[Welcome Email] Processing for user_id=${user_id}`)

    // Initialize clients
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const resend = new Resend(Deno.env.get('RESEND_API_KEY') ?? '')

    // Get user details
    const { data: user, error: userError } = await supabase.auth.admin.getUserById(user_id)

    if (userError || !user || !user.user) {
      console.error('[Welcome Email] User not found:', userError)
      return new Response(
        JSON.stringify({ error: 'User not found' }),
        {
          status: 404,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    const recipientEmail = user_email || user.user.email
    if (!recipientEmail) {
      console.error('[Welcome Email] User has no email address')
      return new Response(
        JSON.stringify({ error: 'User has no email address' }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    console.log(`[Welcome Email] Sending to ${recipientEmail}`)

    // Email HTML template with SCAILE design system
    const appUrl = Deno.env.get('APP_URL') || 'https://g-gpt.com'
    const docsUrl = Deno.env.get('DOCS_URL') || 'https://g-gpt.com/docs'

    // SCAILE Design System - Email Tokens (aligned with zola-aisdkv5)
    const colors = {
      primary: '#282936',
      success: '#10b981',
      background: '#fafaf9',
      card: '#ffffff',
      foreground: '#1f2937',
      muted: '#6b7280',
      border: '#e5e7eb',
      stats_bg: '#f3f4f6'
    }

    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body {
            font-family: "Geist", -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: ${colors.background};
          }
          .container {
            max-width: 600px;
            margin: 0 auto;
            background: ${colors.card};
            padding: 0;
            border-radius: 8px;
          }
          .header {
            background: ${colors.primary};
            color: white;
            padding: 40px 30px;
            text-align: center;
            border-radius: 8px 8px 0 0;
          }
          .header h1 {
            margin: 0;
            font-size: 28px;
          }
          .content {
            padding: 40px 30px;
            color: ${colors.foreground};
          }
          .steps {
            background: ${colors.stats_bg};
            padding: 25px;
            border-radius: 8px;
            margin: 25px 0;
          }
          .steps ol {
            margin: 0;
            padding-left: 20px;
          }
          .steps li {
            margin: 12px 0;
            line-height: 1.8;
          }
          .steps li strong {
            color: ${colors.primary};
          }
          .cta-button {
            display: inline-block;
            background: ${colors.primary};
            color: white;
            padding: 14px 32px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
          }
          .footer {
            padding: 30px;
            border-top: 1px solid ${colors.border};
            color: ${colors.muted};
            font-size: 14px;
            text-align: center;
          }
          .footer a {
            color: ${colors.primary};
            text-decoration: none;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>🚀 Welcome to SCAILE!</h1>
          </div>

          <div class="content">
            <h2>Hi there!</h2>
            <p>Thanks for signing up! We're excited to help you with GTM intelligence and revenue operations.</p>

            <div class="steps">
              <h3 style="margin-top: 0;">Get Started in 4 Easy Steps:</h3>
              <ol>
                <li><strong>Verify your email</strong> to unlock job notifications</li>
                <li><strong>Upload data</strong> or connect your sources (CSV, CRM, databases)</li>
                <li><strong>Run enrichment</strong> with AI-powered tools and research</li>
                <li><strong>Get results</strong> via email with downloadable data!</li>
              </ol>
            </div>

            <p>We'll email you when your jobs complete, so you don't have to wait around. You can customize which notifications you receive in your settings.</p>

            <center>
              <a href="${appUrl}" class="cta-button">
                Launch SCAILE →
              </a>
            </center>

            <h3>What You Can Do:</h3>
            <ul>
              <li>🔍 <strong>Company Discovery</strong> - Find and research target companies</li>
              <li>📊 <strong>Bulk Processing</strong> - Enrich thousands of leads in parallel</li>
              <li>🤖 <strong>AI Research</strong> - Deep research with multi-source validation</li>
              <li>🌐 <strong>Web Intelligence</strong> - Extract data from websites and PDFs</li>
              <li>📈 <strong>Lead Scoring</strong> - Score and prioritize prospects with AI</li>
              <li>💼 <strong>GTM Intelligence</strong> - Market research and competitive analysis</li>
            </ul>
          </div>

          <div class="footer">
            <p>
              Need help? Reply to this email or check our
              <a href="${docsUrl}">documentation</a>.
            </p>
            <p>
              Manage your notification preferences:
              <a href="${appUrl}/profile/notifications">Settings</a>
            </p>
            <p style="margin-top: 15px; font-size: 12px;">SCAILE - GTM Intelligence Copilot</p>
          </div>
        </div>
      </body>
      </html>
    `

    // Send email via Resend
    const { data: emailData, error: sendError } = await resend.emails.send({
      from: Deno.env.get('FROM_EMAIL') || 'SCAILE <hello@g-gpt.com>',
      to: [recipientEmail],
      subject: 'Welcome to SCAILE! 🚀',
      html: html,
      tags: [
        { name: 'category', value: 'welcome' },
        { name: 'user_id', value: user_id }
      ]
    })

    if (sendError) {
      console.error('[Welcome Email] Resend error:', sendError)
      return new Response(
        JSON.stringify({ error: 'Failed to send email', details: sendError }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    console.log(`[Welcome Email] Sent successfully, email_id=${emailData.id}`)

    // Log to notification_logs
    const { error: logError } = await supabase
      .from('notification_logs')
      .insert({
        user_id: user_id,
        notification_type: 'welcome',
        email_id: emailData.id,
        recipient_email: recipientEmail,
        subject: 'Welcome to SCAILE! 🚀',
        status: 'sent'
      })

    if (logError) {
      console.error('[Welcome Email] Failed to log notification:', logError)
      // Don't fail the request - email was sent successfully
    }

    return new Response(
      JSON.stringify({
        success: true,
        email_id: emailData.id,
        recipient: recipientEmail
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('[Welcome Email] Unexpected error:', error)
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

curl -X POST https://[project].supabase.co/functions/v1/send-welcome-email \
  -H "Authorization: Bearer [SERVICE_ROLE_KEY]" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user-uuid"}'

*/
