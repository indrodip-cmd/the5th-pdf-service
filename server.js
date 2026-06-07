'use strict'

const express = require('express')
const puppeteer = require('puppeteer')
const { Resend } = require('resend')
const fs = require('fs')
const path = require('path')

const app = express()
app.use(express.json({ limit: '10mb' }))

let resend = null
if (process.env.RESEND_API_KEY) {
  resend = new Resend(process.env.RESEND_API_KEY)
} else {
  console.warn('WARNING: RESEND_API_KEY not set — emails will be skipped')
}
const FROM_EMAIL = process.env.PDF_FROM_EMAIL || 'Indrodip at The5th <Indrodip@10kroadmap.org>'
const PORT = process.env.PORT || 3000

// ── Logo loading ────────────────────────────────────────────────
function loadLogoB64 (filename) {
  try {
    const data = fs.readFileSync(path.join(__dirname, 'assets', filename)).toString('base64')
    console.log(`${filename} loaded (${Math.round(data.length / 1024)} KB)`)
    return `data:image/png;base64,${data}`
  } catch (e) {
    console.warn(`WARNING: ${filename} not found:`, e.message)
    return ''
  }
}

const LOGO_WHITE = loadLogoB64('logo-white.png')
const LOGO_COLOR = loadLogoB64('logo-color.png')

// ── Archetype content ────────────────────────────────────────────
const ARCHETYPE_CONTENT = {
  'The Pioneer': {
    who: 'You are wired for momentum. You see opportunities before others do, move fast, and naturally attract attention through energy and ideas. You think in possibilities.\n\nThis is your greatest strength — and your greatest vulnerability. Pioneers build fast. They also lose focus just as fast. The coaches who plateau at $3K–5K months are almost always Pioneers who never installed the systems to hold their own momentum in place.\n\nYour growth does not require more ideas. It requires one idea executed with relentless consistency over 90 days.',
    whyNot: [
      ['Authority-first strategies fail Pioneers.', 'Building thought leadership through long-form content requires patience over months. Pioneers abandon this before it compounds. You start strong, produce excellent content for 2–3 weeks, then disappear when something more exciting appears.'],
      ['Relationship-only strategies fail Pioneers.', 'Deep 1:1 nurturing and community-led growth feels painfully slow. You need volume, variety, and visible progress to stay motivated. A strategy that requires 90 days of quiet relationship building before a single sale will drain you.'],
      ['Systems-first strategies fail Pioneers.', 'Starting with funnels, automations, and SOPs before you have consistent revenue kills momentum before it starts. You will spend 6 weeks building infrastructure for a business that does not yet exist.'],
    ],
    whatWorks: 'Fast outreach. Fast offers. Fast feedback loops. You need to be in conversation with new people every single day, making offers consistently, and closing weekly. Revenue first. Systems second. The infrastructure gets built after the cash is flowing — not before.',
  },
  'The Pathfinder': {
    who: 'You are a natural transformer. People trust you quickly and deeply. You have an extraordinary ability to meet people where they are, understand their struggles at a level most coaches never reach, and guide them through genuine change.\n\nWhat is in question is whether your business reflects the value you actually deliver. Pathfinders almost always undercharge — not because they lack confidence, but because charging what they are worth feels like it conflicts with why they do the work. This belief is keeping you small.',
    whyNot: [
      ['High-volume content strategies fail Pathfinders.', 'Posting 30 times a month and chasing viral reach feels performative and hollow to you. You did not become a coach to become a content machine. Strategies that require constant visibility exhaust Pathfinders quickly.'],
      ['Aggressive sales frameworks fail Pathfinders.', 'High-pressure closing techniques feel manipulative to you. If a sales method requires you to override hesitation rather than address it honestly, you will abandon the method — not the prospect.'],
      ['Volume-based offers fail Pathfinders.', 'Selling low-ticket products to large audiences contradicts the depth of transformation you deliver. Every time you discount your work, you erode the premium positioning your expertise deserves.'],
    ],
    whatWorks: 'Deep trust, clear positioning, and premium pricing. You need a small number of ideal clients paying high-ticket rates. Your model is not volume — it is depth. One perfectly positioned offer, sold through honest conversation, to the right person at the right time.',
  },
  'The Builder': {
    who: 'You are an exceptional problem solver. Where others see complexity, you see architecture. You can take a messy, unclear situation and build a structured, logical path through it.\n\nYour challenge is not capability. It is visibility. Builders are often the most qualified coaches in the room — and the least known. The gap between your expertise and your income is a marketing problem, not a skills problem.',
    whyNot: [
      ['Personality-driven content fails Builders.', 'Strategies that require you to be vulnerable or entertainment-focused on social media feel deeply uncomfortable. You are not a performer. Trying to grow through personal brand storytelling will feel inauthentic and you will stop.'],
      ['Referral-only growth fails Builders.', 'Waiting for word of mouth to fill your pipeline is too passive and too slow. Builders need a systematic, controllable lead generation method — not one that depends entirely on other people\'s behaviour.'],
      ['Inspiration-led marketing fails Builders.', 'Your audience does not just want to feel motivated. They want proof that your method works. Vague motivational content does not convert for Builders — results, frameworks, and case studies do.'],
    ],
    whatWorks: 'Structured lead generation with a clear, results-focused offer. Case studies, frameworks, and demonstrated outcomes. Your marketing should show your thinking, not your personality. Teach your methodology publicly. Let the rigour of your approach speak for itself.',
  },
  'The Luminary': {
    who: 'You carry authority naturally. When you speak, people listen. When you share a perspective, people trust it. You have accumulated wisdom, experience, and insight that others simply do not have access to.\n\nYour challenge is not credibility. You have more credibility than most coaches will ever build. Your challenge is converting that credibility into a consistent, reliable flow of paying clients without diluting the authority you have spent years building.',
    whyNot: [
      ['High-frequency content strategies fail Luminaries.', 'Posting daily content to chase algorithm reach feels beneath the level of authority you have built. Luminaries who try to compete on content volume dilute their positioning and confuse their audience.'],
      ['Discount or volume-based offers fail Luminaries.', 'Selling low-ticket products to large audiences contradicts the premium positioning your presence naturally creates. Every time you discount, you erode the authority you have spent years building.'],
      ['Copying other coaches\' growth models fails Luminaries.', 'You are not an emerging coach trying to get noticed. You are an established voice trying to monetise influence. The strategies built for coaches starting from zero will actively harm your positioning.'],
    ],
    whatWorks: 'Selective visibility with premium positioning. You do not need a large audience. You need the right audience seeing the right message. One high-ticket offer, a clear point of view, and a simple conversion system built around your existing authority.',
  },
}

const TESTIMONIALS = [
  {
    name: 'Jeanne Tomasak',
    role: 'Business Coach',
    result: 'First client in 6 weeks',
    quote: 'I had spent over $10,000 on coaches before working with Indrodip. None gave me the clarity he did. He rebuilt how I saw my business from niche to offer to sales conversation. Six weeks later I closed my first client.',
  },
  {
    name: 'Angela Gregg',
    role: 'Education Program Director',
    result: 'First $2,500 sale',
    quote: 'After burning through $25,000 on coaches who did not understand my context, two months with Indrodip and I closed my first $2,500 sale. For someone who had nearly given up, that meant everything.',
  },
  {
    name: 'Laurie Gerber',
    role: 'Online Course Creator',
    result: '$26,000 in 3 months',
    quote: 'After a failed launch I had lost confidence completely. We rebuilt the strategy, repositioned my pricing from $79 to $225, and within three months generated $26,000 in revenue. I still find that number hard to believe.',
  },
  {
    name: 'Jennifer',
    role: 'Educator turned Coach',
    result: '$4K/month consistently',
    quote: 'Indrodip helped me go from zero to $4,000 every single month. The clarity I got in one call changed everything I thought I knew about building a coaching business.',
  },
]

// ── Utilities ────────────────────────────────────────────────────
function esc (str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function formatInline (text) {
  return esc(text).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
}

function renderContent (text) {
  if (!text) return ''
  const lines = text.split('\n')
  let html = ''
  let inList = false

  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line) {
      if (inList) { html += '</ul>'; inList = false }
      html += '<div style="height:9px"></div>'
      continue
    }
    if (line.startsWith('- ') || line.startsWith('* ')) {
      if (!inList) {
        html += '<ul style="margin:6px 0;padding:0;list-style:none;">'
        inList = true
      }
      html += `<li style="display:flex;gap:10px;margin-bottom:7px;font-family:'DM Sans',Helvetica,sans-serif;font-size:14px;color:#444;line-height:1.75;"><span style="color:#c9a84c;font-weight:700;flex-shrink:0;margin-top:1px;">—</span><span>${formatInline(line.slice(2))}</span></li>`
    } else {
      if (inList) { html += '</ul>'; inList = false }
      if ((line.startsWith('**') && line.endsWith('**')) || (line.startsWith('### '))) {
        const label = line.replace(/^#+\s*/, '').replace(/^\*\*/, '').replace(/\*\*$/, '')
        html += `<p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:11px;font-weight:700;color:#1a1040;letter-spacing:0.1em;text-transform:uppercase;margin:14px 0 6px;">${formatInline(label)}</p>`
      } else {
        html += `<p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:14px;color:#444;line-height:1.85;margin:0 0 9px;">${formatInline(line)}</p>`
      }
    }
  }
  if (inList) html += '</ul>'
  return html
}

// ── Roadmap parser ───────────────────────────────────────────────
function parseRoadmap (text) {
  const sections = {}
  let currentKey = null
  const currentLines = []

  function flush () {
    if (currentKey) {
      sections[currentKey] = currentLines.join('\n').trim()
      currentLines.length = 0
    }
  }

  for (const rawLine of (text || '').split('\n')) {
    const line = rawLine.trim()
    if (line.startsWith('## ')) {
      flush()
      currentKey = line.slice(3).trim().toUpperCase()
    } else if (line === '---' || line === '***' || line.startsWith('# ')) {
      // strip separators and top-level headings
    } else {
      if (currentKey !== null) currentLines.push(rawLine)
    }
  }
  flush()

  // Return proxy so missing keys return '' instead of undefined
  return new Proxy(sections, {
    get (target, prop) { return prop in target ? target[prop] : '' },
  })
}

// ── Footer bar (interior pages) ──────────────────────────────────
function footerBar (logoSrc, title, pageNum) {
  const logoHtml = logoSrc
    ? `<img src="${logoSrc}" style="height:18px;width:auto;opacity:0.85;display:block;">`
    : `<span style="font-family:'DM Sans',sans-serif;font-size:9px;color:#fff;letter-spacing:0.1em;font-weight:600;">THE5TH</span>`
  return `<div style="position:absolute;bottom:0;left:0;right:0;height:44px;background:#111111;display:flex;align-items:center;padding:0 32px;gap:16px;">
    ${logoHtml}
    <span style="flex:1;font-family:'DM Sans',Helvetica,sans-serif;font-size:10px;color:rgba(255,255,255,0.55);text-align:center;letter-spacing:0.03em;">${esc(title)}</span>
    <span style="font-family:'DM Sans',Helvetica,sans-serif;font-size:11px;color:#c9a84c;font-weight:600;">${pageNum}</span>
  </div>`
}

// ── Section aliases ──────────────────────────────────────────────
const SECTION_ALIASES = {
  'YOUR SITUATION RIGHT NOW':  ['YOUR SITUATION RIGHT NOW', 'YOUR SITUATION', 'SITUATION'],
  'YOUR SIGNATURE OFFER':      ['YOUR SIGNATURE OFFER', 'SIGNATURE OFFER', 'YOUR OFFER'],
  'YOUR LEAD MAGNET IDEA':     ['YOUR LEAD MAGNET IDEA', 'LEAD MAGNET IDEA', 'LEAD MAGNET'],
  'YOUR DIGITAL PRODUCT IDEA': ['YOUR DIGITAL PRODUCT IDEA', 'DIGITAL PRODUCT IDEA', 'DIGITAL PRODUCT'],
  '7-DAY CONTENT PLAN':        ['7-DAY CONTENT PLAN', 'YOUR 7-DAY CONTENT PLAN', 'CONTENT PLAN', '7 DAY CONTENT PLAN'],
  '30-DAY ACTION PLAN':        ['30-DAY ACTION PLAN', 'YOUR 30-DAY ACTION PLAN', 'ACTION PLAN', '30 DAY ACTION PLAN'],
  'YOUR PRICING STRATEGY':     ['YOUR PRICING STRATEGY', 'PRICING STRATEGY', 'PRICING'],
  'YOUR BIGGEST OPPORTUNITY':  ['YOUR BIGGEST OPPORTUNITY', 'BIGGEST OPPORTUNITY'],
}

function getSection (sections, primaryKey) {
  for (const alias of (SECTION_ALIASES[primaryKey] || [primaryKey])) {
    if (sections[alias]) return sections[alias]
  }
  return ''
}

// ── HTML Generator ───────────────────────────────────────────────
function generateHTML (data) {
  const sections = parseRoadmap(data.roadmap)
  const archContent = ARCHETYPE_CONTENT[data.archetype] || ARCHETYPE_CONTENT['The Pioneer']

  const SECTION_DEFS = [
    { key: 'YOUR SITUATION RIGHT NOW',  num: 1, title: 'Your Situation Right Now' },
    { key: 'YOUR SIGNATURE OFFER',      num: 2, title: 'Your Signature Offer' },
    { key: 'YOUR LEAD MAGNET IDEA',     num: 3, title: 'Your Lead Magnet Idea' },
    { key: 'YOUR DIGITAL PRODUCT IDEA', num: 4, title: 'Your Digital Product Idea' },
    { key: '7-DAY CONTENT PLAN',        num: 5, title: 'Your 7-Day Content Plan' },
    { key: '30-DAY ACTION PLAN',        num: 6, title: 'Your 30-Day Action Plan' },
    { key: 'YOUR PRICING STRATEGY',     num: 7, title: 'Your Pricing Strategy' },
    { key: 'YOUR BIGGEST OPPORTUNITY',  num: 8, title: 'Your Biggest Opportunity' },
  ]

  const logoW = LOGO_WHITE ? `<img src="${LOGO_WHITE}" style="display:block;">` : ''
  const logoC = LOGO_COLOR ? `<img src="${LOGO_COLOR}" style="display:block;">` : ''

  let pages = ''
  let pageCounter = 1

  // ── PAGE 1: COVER ────────────────────────────────────────────────
  pageCounter++ // archetype will be 2
  pages += `
<div class="page" style="background:#1a1040;display:flex;flex-direction:column;">
  <!-- Top bar -->
  <div style="height:48px;background:#111111;flex-shrink:0;display:flex;align-items:center;justify-content:center;">
    <span style="font-family:'DM Sans',Helvetica,sans-serif;font-size:10px;color:rgba(255,255,255,0.75);letter-spacing:0.18em;text-transform:uppercase;">Personalised Growth Blueprint &nbsp;&middot;&nbsp; The5th Consulting</span>
  </div>

  <!-- Hero -->
  <div style="flex:1;display:flex;flex-direction:column;align-items:center;text-align:center;padding:44px 60px 0;overflow:hidden;">
    ${LOGO_WHITE ? `<img src="${LOGO_WHITE}" style="width:200px;height:auto;display:block;margin:0 auto 28px;">` : `<div style="font-family:'DM Sans',sans-serif;font-size:20px;font-weight:700;color:#fff;margin-bottom:28px;">THE5TH CONSULTING</div>`}

    <div style="width:120px;height:1px;background:#c9a84c;margin:0 auto;"></div>
    <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:10px;color:#c9a84c;letter-spacing:0.2em;text-transform:uppercase;margin:16px 0;">Your Personalised Growth Blueprint</p>
    <div style="width:120px;height:1px;background:#c9a84c;margin:0 auto 32px;"></div>

    <p style="font-family:'Cormorant Garant',Georgia,serif;font-size:21px;font-style:italic;color:rgba(255,255,255,0.72);margin-bottom:10px;">Prepared exclusively for</p>
    <h1 style="font-family:'Cormorant Garant',Georgia,serif;font-size:66px;font-weight:700;color:#ffffff;line-height:1.05;margin-bottom:14px;">${esc(data.name)}</h1>
    <h2 style="font-family:'Cormorant Garant',Georgia,serif;font-size:48px;font-weight:700;font-style:italic;color:#c9a84c;line-height:1.1;margin-bottom:28px;">${esc(data.archetype)}</h2>

    <div style="width:200px;height:1px;background:#c9a84c;margin:0 auto 36px;"></div>

    <!-- Stats row -->
    <div style="display:flex;width:420px;border:1px solid rgba(201,168,76,0.35);border-radius:4px;overflow:hidden;margin-bottom:28px;">
      <div style="flex:1;padding:16px 8px;text-align:center;border-right:1px solid rgba(201,168,76,0.25);">
        <div style="font-family:'DM Sans',Helvetica,sans-serif;font-size:8px;color:#c9a84c;letter-spacing:0.18em;text-transform:uppercase;margin-bottom:6px;">Archetype</div>
        <div style="font-family:'DM Sans',Helvetica,sans-serif;font-size:12px;font-weight:600;color:#ffffff;">${esc(data.archetype)}</div>
      </div>
      <div style="flex:1;padding:16px 8px;text-align:center;border-right:1px solid rgba(201,168,76,0.25);">
        <div style="font-family:'DM Sans',Helvetica,sans-serif;font-size:8px;color:#c9a84c;letter-spacing:0.18em;text-transform:uppercase;margin-bottom:6px;">Income Goal</div>
        <div style="font-family:'DM Sans',Helvetica,sans-serif;font-size:12px;font-weight:600;color:#ffffff;">${esc(data.goal)}</div>
      </div>
      <div style="flex:1;padding:16px 8px;text-align:center;">
        <div style="font-family:'DM Sans',Helvetica,sans-serif;font-size:8px;color:#c9a84c;letter-spacing:0.18em;text-transform:uppercase;margin-bottom:6px;">Business Stage</div>
        <div style="font-family:'DM Sans',Helvetica,sans-serif;font-size:12px;font-weight:600;color:#ffffff;">${esc(data.stage)}</div>
      </div>
    </div>

    <p style="font-family:'Cormorant Garant',Georgia,serif;font-size:14px;font-style:italic;color:rgba(201,168,76,0.75);">Confidential &nbsp;&middot;&nbsp; Built exclusively for you &nbsp;&middot;&nbsp; Do not distribute</p>
  </div>

  <!-- Bottom bar -->
  <div style="height:60px;background:#111111;flex-shrink:0;display:flex;align-items:center;padding:0 32px;">
    ${LOGO_WHITE ? `<img src="${LOGO_WHITE}" style="height:22px;width:auto;display:block;opacity:0.85;">` : ''}
    <span style="flex:1;font-family:'DM Sans',Helvetica,sans-serif;font-size:12px;color:#c9a84c;text-align:center;letter-spacing:0.05em;">quiz.the5th.consulting</span>
  </div>
</div>`

  // ── PAGE 2: ARCHETYPE DEEP DIVE ───────────────────────────────────
  pages += `
<div class="page" style="display:flex;position:relative;">
  <!-- Left column: dark -->
  <div style="width:38%;background:#1a1040;position:relative;overflow:hidden;padding:40px 28px 60px;">
    <!-- Decorative large number -->
    <div style="position:absolute;top:-8px;left:-16px;font-family:'Cormorant Garant',Georgia,serif;font-size:170px;font-weight:700;color:rgba(255,255,255,0.05);line-height:1;user-select:none;pointer-events:none;z-index:0;">01</div>
    <div style="position:relative;z-index:1;">
      ${LOGO_WHITE ? `<img src="${LOGO_WHITE}" style="width:130px;height:auto;display:block;margin-bottom:20px;">` : ''}
      <div style="width:56px;height:1px;background:#c9a84c;margin-bottom:18px;"></div>
      <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:9px;color:#c9a84c;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:14px;">Understanding Your Archetype</p>
      <h2 style="font-family:'Cormorant Garant',Georgia,serif;font-size:36px;font-weight:700;color:#ffffff;line-height:1.15;margin-bottom:10px;">${esc(data.archetype)}</h2>
      <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:13px;color:#8b7fcf;margin-bottom:22px;">Personality: ${esc(data.personality || '')}</p>
      <div style="width:56px;height:1px;background:#c9a84c;margin-bottom:24px;"></div>
      <p style="font-family:'Cormorant Garant',Georgia,serif;font-size:15px;font-style:italic;color:rgba(255,255,255,0.6);line-height:1.65;">Your path to $10K months is already clear — this document shows you exactly how to walk it.</p>
    </div>
  </div>

  <!-- Right column: white -->
  <div style="width:62%;background:#ffffff;padding:38px 40px 56px;overflow:hidden;max-height:1123px;">
    <div style="margin-bottom:18px;">
      <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:9px;font-weight:700;color:#c9a84c;letter-spacing:0.16em;text-transform:uppercase;margin-bottom:10px;">Who You Are</p>
      ${archContent.who.split('\n\n').map(p => `<p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:13.5px;color:#333333;line-height:1.8;margin-bottom:11px;">${esc(p.trim())}</p>`).join('')}
    </div>
    <div style="margin-bottom:18px;">
      <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:9px;font-weight:700;color:#c9a84c;letter-spacing:0.16em;text-transform:uppercase;margin-bottom:10px;">Why Other Growth Models Fail You</p>
      ${archContent.whyNot.map(([sub, body]) => `
        <div style="margin-bottom:11px;">
          <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:12.5px;font-weight:600;color:#1a1040;margin-bottom:3px;">${esc(sub)}</p>
          <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:12.5px;color:#555555;line-height:1.7;">${esc(body)}</p>
        </div>`).join('')}
    </div>
    <div style="background:#f5f0e0;border-left:4px solid #c9a84c;padding:16px 20px;border-radius:0 4px 4px 0;">
      <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:9px;font-weight:700;color:#c9a84c;letter-spacing:0.16em;text-transform:uppercase;margin-bottom:8px;">What Actually Works For You</p>
      <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:13.5px;color:#333333;line-height:1.8;">${esc(archContent.whatWorks)}</p>
    </div>
  </div>

  ${footerBar(LOGO_WHITE, data.archetype || 'Your Archetype', 2)}
</div>`

  // ── PAGES 3–10: CONTENT SECTIONS ─────────────────────────────────
  let contentPageCounter = 3
  for (const def of SECTION_DEFS) {
    const content = getSection(sections, def.key)
    if (!content) continue

    const isOdd = def.num % 2 === 1
    const pageBg    = isOdd ? '#ffffff' : '#faf5ef'
    const headerBg  = isOdd ? '#faf5ef' : '#f0ead8'
    const accentBar = isOdd ? '#c9a84c' : '#1a1040'
    const circleBg  = isOdd ? '#1a1040' : '#c9a84c'
    const circleClr = isOdd ? '#ffffff' : '#1a1040'

    pages += `
<div class="page" style="background:${pageBg};position:relative;">
  <!-- Accent bar -->
  <div style="height:6px;background:${accentBar};"></div>

  <!-- Header row -->
  <div style="background:${headerBg};padding:24px 44px;display:flex;align-items:center;gap:18px;border-bottom:1px solid rgba(0,0,0,0.06);">
    <div style="width:46px;height:46px;border-radius:50%;background:${circleBg};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
      <span style="font-family:'Cormorant Garant',Georgia,serif;font-size:20px;font-weight:700;color:${circleClr};line-height:1;">${String(def.num).padStart(2, '0')}</span>
    </div>
    <div>
      <div style="font-family:'DM Sans',Helvetica,sans-serif;font-size:9px;font-weight:600;color:#c9a84c;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:3px;">Section ${String(def.num).padStart(2, '0')}</div>
      <h2 style="font-family:'Cormorant Garant',Georgia,serif;font-size:28px;font-weight:700;color:#1a1040;line-height:1.1;margin:0;">${esc(def.title)}</h2>
    </div>
  </div>

  <!-- Content -->
  <div style="padding:28px 44px 56px;overflow:hidden;max-height:940px;">
    ${renderContent(content)}
  </div>

  ${footerBar(LOGO_COLOR || LOGO_WHITE, def.title, contentPageCounter)}
</div>`
    contentPageCounter++
  }

  // ── TESTIMONIALS ──────────────────────────────────────────────────
  pages += `
<div class="page" style="background:#1a1a1a;position:relative;">
  <div style="padding:44px 44px 56px;text-align:center;">
    ${LOGO_WHITE ? `<img src="${LOGO_WHITE}" style="width:148px;height:auto;display:block;margin:0 auto 22px;">` : ''}
    <div style="width:100px;height:1px;background:#c9a84c;margin:0 auto 18px;"></div>
    <h2 style="font-family:'Cormorant Garant',Georgia,serif;font-size:32px;font-weight:700;font-style:italic;color:#ffffff;margin-bottom:4px;">What Our Clients Say</h2>
    <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:10px;color:rgba(201,168,76,0.65);letter-spacing:0.14em;text-transform:uppercase;margin-bottom:20px;">Real results from real coaches</p>
    <div style="width:100px;height:1px;background:#c9a84c;margin:0 auto 30px;"></div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;text-align:left;">
      ${TESTIMONIALS.map(t => `
      <div style="background:rgba(255,255,255,0.055);border:1px solid rgba(201,168,76,0.22);border-radius:8px;padding:22px;">
        <div style="font-family:'Cormorant Garant',Georgia,serif;font-size:52px;color:#c9a84c;line-height:0.75;margin-bottom:10px;opacity:0.8;">&ldquo;</div>
        <p style="font-family:'Cormorant Garant',Georgia,serif;font-size:14.5px;font-style:italic;color:rgba(255,255,255,0.87);line-height:1.7;margin-bottom:14px;">${esc(t.quote)}</p>
        <div style="border-top:1px solid rgba(201,168,76,0.18);padding-top:10px;">
          <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:12px;font-weight:700;color:#c9a84c;margin-bottom:2px;">${esc(t.name)}</p>
          <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:11px;color:rgba(255,255,255,0.45);">${esc(t.role)} &middot; ${esc(t.result)}</p>
        </div>
      </div>`).join('')}
    </div>
  </div>
  ${footerBar(LOGO_WHITE, 'Client Results', contentPageCounter)}
</div>`

  // ── CTA PAGE ──────────────────────────────────────────────────────
  const ctaItems = [
    'Your offer completely defined and priced',
    'Your exact sales conversation mapped out',
    'Your 30-day revenue plan ready to execute',
    'Your biggest growth block identified and removed',
    'Your exact next 3 steps starting tomorrow',
  ]

  pages += `
<div class="page" style="background:#1a1040;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;">
  <div style="max-width:560px;text-align:center;padding:0 32px;">
    ${LOGO_WHITE ? `<img src="${LOGO_WHITE}" style="width:170px;height:auto;display:block;margin:0 auto 24px;">` : ''}
    <div style="width:80px;height:1px;background:#c9a84c;margin:0 auto 18px;"></div>

    <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:10px;color:#c9a84c;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:18px;">Your Next Step</p>
    <h2 style="font-family:'Cormorant Garant',Georgia,serif;font-size:42px;font-weight:700;color:#ffffff;line-height:1.2;margin-bottom:18px;">Want To Map Your Entire Business In 60 Minutes?</h2>

    <div style="width:120px;height:1px;background:#c9a84c;margin:0 auto 18px;"></div>

    <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:14px;color:rgba(255,255,255,0.78);line-height:1.75;margin-bottom:24px;max-width:460px;">Your blueprint is ready. One conversation with Indrodip will turn it into a precise, executable plan. No fluff. No theory. Just your exact next moves.</p>

    <!-- What you get grid -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 28px;margin-bottom:30px;text-align:left;">
      ${ctaItems.map(item => `
      <div style="display:flex;gap:10px;align-items:flex-start;">
        <span style="color:#c9a84c;font-weight:700;flex-shrink:0;font-size:15px;margin-top:1px;">&#10003;</span>
        <span style="font-family:'DM Sans',Helvetica,sans-serif;font-size:13.5px;color:rgba(255,255,255,0.83);line-height:1.55;">${esc(item)}</span>
      </div>`).join('')}
    </div>

    <!-- CTA box -->
    <div style="background:#c9a84c;border-radius:4px;padding:18px 40px;margin-bottom:16px;">
      <p style="font-family:'Cormorant Garant',Georgia,serif;font-size:20px;font-weight:700;color:#1a1040;margin-bottom:4px;">Book Your Free 60-Minute Strategy Call</p>
      <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:12px;color:#1a1040;opacity:0.75;">cal.com/indrodip-ghosh-ut1vxh/60min</p>
    </div>

    <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:11px;color:rgba(255,255,255,0.4);margin-bottom:24px;">10 spots available each month &nbsp;&middot;&nbsp; Free &nbsp;&middot;&nbsp; No obligation</p>

    <div style="width:100%;height:1px;background:rgba(201,168,76,0.25);margin-bottom:12px;"></div>
    <p style="font-family:'DM Sans',Helvetica,sans-serif;font-size:10px;color:rgba(255,255,255,0.32);">support@10kroadmap.org &nbsp;&middot;&nbsp; quiz.the5th.consulting</p>
  </div>
</div>`

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garant:ital,wght@0,400;0,600;0,700;1,400;1,600;1,700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
body { width:794px; background:#ffffff; }
.page { width:794px; height:1123px; position:relative; overflow:hidden; page-break-after:always; }
img { display:block; }
</style>
</head>
<body>
${pages}
</body>
</html>`
}

// ── Email template ───────────────────────────────────────────────
function generateEmailHTML (name) {
  const firstName = (name || 'there').split(' ')[0]
  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Your Growth Blueprint</title></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
<tr><td align="center">
<table width="540" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:6px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,0.09);">
  <tr><td style="background:#1a1040;padding:30px 36px;text-align:center;">
    <p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;font-weight:700;color:#ffffff;letter-spacing:0.15em;text-transform:uppercase;margin:0;">The5th Consulting</p>
  </td></tr>
  <tr><td style="height:4px;background:#c9a84c;"></td></tr>
  <tr><td style="padding:36px 40px 28px;">
    <p style="font-size:22px;font-weight:700;color:#1a1040;margin:0 0 14px;">${esc(firstName)}, your blueprint is ready.</p>
    <p style="font-size:15px;color:#444444;line-height:1.7;margin:0 0 14px;">Your personalised Growth Blueprint is attached to this email as a PDF.</p>
    <p style="font-size:15px;color:#444444;line-height:1.7;margin:0 0 22px;">This document contains your exact roadmap — built around your archetype, your goals, and where you are right now. Read it carefully. Act on it. And if you have any questions, reply to this email directly.</p>
    <div style="background:#faf5ef;border-left:4px solid #c9a84c;padding:16px 20px;margin-bottom:26px;border-radius:0 4px 4px 0;">
      <p style="font-size:14px;color:#333333;font-weight:600;margin:0 0 6px;">One more thing.</p>
      <p style="font-size:14px;color:#555555;line-height:1.65;margin:0;">If you want to turn this blueprint into a precise, executable plan in a single conversation — book a free 60-minute strategy call with Indrodip.</p>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
      <a href="https://cal.com/indrodip-ghosh-ut1vxh/60min" style="display:inline-block;background:#c9a84c;color:#1a1040;text-align:center;padding:15px 36px;text-decoration:none;font-weight:700;font-size:14px;border-radius:4px;letter-spacing:0.03em;">Book Your Free Strategy Call &rarr;</a>
    </td></tr></table>
    <p style="font-size:12px;color:#999999;line-height:1.6;margin:24px 0 0;">This email was sent because you completed The5th Consulting quiz. Reply to this email if you have any questions — we read every reply.</p>
  </td></tr>
  <tr><td style="background:#111111;padding:18px 32px;text-align:center;">
    <p style="font-size:11px;color:rgba(255,255,255,0.45);margin:0;">quiz.the5th.consulting &nbsp;&middot;&nbsp; support@10kroadmap.org</p>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>`
}

// ── POST /generate-pdf ───────────────────────────────────────────
app.post('/generate-pdf', async (req, res) => {
  const data = req.body
  if (!data || !data.name || !data.email || !data.roadmap) {
    return res.status(400).json({ error: 'name, email, and roadmap are required' })
  }

  console.log(`Generating PDF for ${data.email} (archetype: ${data.archetype})`)
  const firstName = data.name.split(' ')[0]

  let browser
  try {
    // Render HTML → PDF
    const html = generateHTML(data)
    browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-first-run',
        '--no-zygote',
        '--single-process',
      ],
    })
    const page = await browser.newPage()
    await page.setContent(html, { waitUntil: 'networkidle0', timeout: 45000 })
    const pdf = await page.pdf({
      format: 'A4',
      printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    })
    await browser.close()
    browser = null
    console.log(`PDF generated (${Math.round(pdf.length / 1024)} KB)`)

    // Send email via Resend
    try {
      if (!resend) {
        console.log('Email skipped: RESEND_API_KEY not configured')
      } else {
        await resend.emails.send({
          from: FROM_EMAIL,
          to: data.email,
          subject: `${firstName}, your personalised blueprint is ready`,
          html: generateEmailHTML(data.name),
          attachments: [
            { filename: 'your-growth-blueprint.pdf', content: Buffer.from(pdf).toString('base64') },
          ],
        })
        console.log(`Email sent to ${data.email}`)
      }
    } catch (emailErr) {
      console.error('Resend error (non-fatal):', emailErr.message)
    }

    return res.json({ success: true })
  } catch (err) {
    console.error('generate-pdf error:', err)
    return res.status(500).json({ error: err.message || 'PDF generation failed' })
  } finally {
    if (browser) {
      try { await browser.close() } catch (_) {}
    }
  }
})

// ── GET /health ──────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'the5th-pdf-service-v2' })
})

// ── Start ────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`The5th PDF Service v2 listening on port ${PORT}`)
})

module.exports = app
