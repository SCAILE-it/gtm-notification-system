# Email Visual Verification Checklist

**Use this checklist after sending test emails to verify SCAILE branding and email rendering.**

---

## 🎨 SCAILE Design System Verification

### Branding

- [ ] **Brand name** - All emails say "SCAILE" (not "GTM Power App")
- [ ] **Footer** - Shows "SCAILE - GTM Intelligence Copilot"
- [ ] **From address** - `SCAILE <hello@g-gpt.com>` (not gtmpowerapp.com)
- [ ] **Links** - All URLs point to `g-gpt.com` (not gtmpowerapp.com)

### Colors

- [ ] **Primary color** - `#282936` (dark blue-purple) used for:
  - CTA buttons
  - Job Complete header background
  - Links
- [ ] **Success color** - `#10b981` (green) in Job Complete header
- [ ] **Error color** - `#ef4444` (red) in Job Failed header
- [ ] **Warning color** - `#f59e0b` (amber) in Quota Warning header
- [ ] **Background** - `#fafaf9` (warm off-white) for email body
- [ ] **Text** - `#1f2937` (dark gray) for body text
- [ ] **Muted text** - `#6b7280` (gray) for secondary text

### Typography

- [ ] **Font family** - Geist or system fallback loads correctly
- [ ] **Heading size** - 28px headers are readable
- [ ] **Body text** - 16px body text is comfortable to read
- [ ] **Stats** - 24px stat values are prominent

### Layout

- [ ] **Container width** - Max 600px (fits email clients)
- [ ] **Padding** - Consistent 20-30px padding throughout
- [ ] **Border radius** - Buttons have 6px rounded corners
- [ ] **Headers** - Full-width colored headers look good
- [ ] **Stats grid** - Stats display in clean grid layout

---

## 📧 Email-Specific Checks

### 1. Job Complete Email

**Subject:** `✅ Job Complete - [Job ID]`

**Visual checks:**
- [ ] Green success header (#10b981)
- [ ] Stats grid shows all metrics clearly:
  - Total Rows
  - Successful
  - Failed
  - Processing Time
- [ ] "View in App" button is prominent (primary color)
- [ ] "Download CSV" link is visible
- [ ] Job ID displayed correctly
- [ ] Footer links work

### 2. Job Failed Email

**Subject:** `❌ Job Failed - [Job ID]`

**Visual checks:**
- [ ] Red error header (#ef4444)
- [ ] Error details box has light red background (#fef2f2)
- [ ] Error message text is readable
- [ ] Darker red heading (#dc2626) for "Error Details"
- [ ] "View Logs" button works
- [ ] Support link clickable
- [ ] Timestamp displayed

### 3. Quota Warning Email

**Subject:** `⚠️ Quota Warning - [XX]% Used`

**Visual checks:**
- [ ] Amber warning header (#f59e0b)
- [ ] Usage stats clearly visible:
  - Current Usage
  - Quota Limit
  - Remaining
  - % Used
- [ ] "Upgrade Plan" button prominent
- [ ] Progress bar or percentage clear
- [ ] Footer shows account settings link

### 4. Welcome Email

**Subject:** `Welcome to SCAILE! 🚀`

**Visual checks:**
- [ ] Dark primary header (#282936)
- [ ] Welcome message friendly and clear
- [ ] 4-step getting started list readable:
  1. Verify email
  2. Upload data
  3. Run enrichment
  4. Get results
- [ ] "Launch SCAILE" button prominent
- [ ] Feature list shows all capabilities:
  - Company Discovery
  - Bulk Processing
  - AI Research
  - Web Intelligence
  - Lead Scoring
  - GTM Intelligence
- [ ] Footer has docs and settings links

---

## 📱 Email Client Testing

### Gmail

**Web (gmail.com):**
- [ ] Desktop view renders correctly
- [ ] Mobile-responsive view works
- [ ] Images load (if any)
- [ ] Links are clickable
- [ ] Buttons have hover states (desktop only)

**Mobile App:**
- [ ] Email fits screen width
- [ ] Text is readable without zooming
- [ ] Buttons are tappable
- [ ] Links work

**Dark Mode:**
- [ ] Text is still readable
- [ ] Colors don't invert poorly
- [ ] Buttons remain visible

### Outlook

**Web (outlook.com):**
- [ ] Layout doesn't break
- [ ] Colors render correctly
- [ ] Fonts load properly

**Desktop App (Windows/Mac):**
- [ ] Email renders without errors
- [ ] Stats grid displays correctly
- [ ] Buttons clickable

### Apple Mail

**macOS:**
- [ ] Clean rendering
- [ ] Colors accurate
- [ ] Layout intact

**iOS/iPadOS:**
- [ ] Mobile view works
- [ ] Tappable buttons
- [ ] Readable text

### Other Clients

**ProtonMail:**
- [ ] Loads correctly
- [ ] Privacy-friendly rendering

**Thunderbird:**
- [ ] No layout issues

**Mobile Gmail (Android):**
- [ ] Renders on small screens

---

## 🌐 Cross-Browser/Device Testing

### Desktop Browsers (via webmail)

- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari
- [ ] Opera

### Mobile Devices

- [ ] iPhone (iOS Mail + Gmail app)
- [ ] Android (Gmail app)
- [ ] Tablet (iPad/Android)

### Screen Sizes

- [ ] Large desktop (1920px+)
- [ ] Laptop (1366px-1920px)
- [ ] Tablet (768px-1024px)
- [ ] Mobile (375px-414px)

---

## 🔍 Technical Checks

### HTML/CSS Validation

- [ ] Inline CSS only (no external stylesheets)
- [ ] No JavaScript (email clients strip it)
- [ ] Table-based layout (for compatibility)
- [ ] All images have alt text
- [ ] Links have descriptive text

### Accessibility

- [ ] Sufficient color contrast (text vs background)
- [ ] Readable without images
- [ ] Semantic HTML structure
- [ ] Alt text for all images
- [ ] Links describe destination

### Deliverability

- [ ] Not flagged as spam
- [ ] From address whitelisted
- [ ] SPF/DKIM/DMARC configured (Resend handles this)
- [ ] Unsubscribe link present (if required)

---

## 🐛 Common Issues to Watch For

### Layout Breaks

- [ ] Stats grid collapses incorrectly on mobile
- [ ] Buttons overflow container
- [ ] Text wraps awkwardly
- [ ] Headers have wrong height

### Color Problems

- [ ] Colors look washed out
- [ ] Dark mode makes text unreadable
- [ ] Buttons blend with background
- [ ] Links not distinct from text

### Typography Issues

- [ ] Font doesn't load, fallback looks bad
- [ ] Text too small on mobile
- [ ] Headers too large
- [ ] Line height causes overlap

### Functionality Issues

- [ ] Links broken or point to wrong URL
- [ ] Buttons not clickable
- [ ] Job ID/data incorrect
- [ ] Timestamp wrong

---

## 📊 Testing Workflow

### Initial Send

1. Run `python scripts/send_test_emails.py`
2. Receive 3 test emails (Job Complete, Job Failed, Quota Warning)
3. Check inbox immediately

### Visual Review

1. Open each email in primary email client
2. Check against this list
3. Take screenshots for documentation
4. Note any issues

### Cross-Client Testing

1. Forward emails to test accounts in other clients
2. Check rendering in each
3. Document client-specific issues
4. Fix critical issues, document minor ones

### Mobile Testing

1. Forward to mobile device
2. Check in native mail app
3. Check in Gmail/Outlook mobile apps
4. Test landscape and portrait

### Final Approval

- [ ] All critical issues resolved
- [ ] Documented known minor issues
- [ ] Screenshots taken for future reference
- [ ] Ready for production deployment

---

## 📝 Issue Reporting Template

If you find issues, document them like this:

```
**Issue:** Button text not visible in Outlook dark mode
**Severity:** Medium
**Email:** Job Complete
**Client:** Outlook Desktop (Windows)
**Steps to reproduce:**
  1. Enable dark mode in Outlook
  2. Open Job Complete email
  3. Observe button text

**Expected:** White text on dark button
**Actual:** Dark text on dark button (unreadable)

**Fix:** Add explicit color: white !important to button text
```

---

## ✅ Sign-Off Checklist

Before deploying to production:

- [ ] All emails tested in Gmail (web + mobile)
- [ ] All emails tested in Outlook (web + desktop)
- [ ] All emails tested in Apple Mail
- [ ] No critical issues found
- [ ] Minor issues documented
- [ ] Screenshots captured
- [ ] Design system matches zola-aisdkv5
- [ ] Branding 100% SCAILE (no old references)
- [ ] Links all point to correct URLs
- [ ] Team has reviewed and approved

---

**Last Updated:** 2025-01-29
**Verified By:** _________________
**Date:** _________________
**Production-Ready:** ☐ Yes ☐ No ☐ With Notes

---

**For questions or issues, see:** `QUICKSTART.md` or `docs/INTEGRATION_GUIDE.md`
