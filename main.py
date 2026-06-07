import io, os, math
from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Flowable,
    Paragraph, Spacer, Table, TableStyle,
    NextPageTemplate, PageBreak, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from PIL import Image as PILImage

app = FastAPI()

# ── Brand Colors ──
PURPLE_DARK  = colors.HexColor('#1a1040')
PURPLE       = colors.HexColor('#8b7fcf')
PURPLE_MID   = colors.HexColor('#4a3d99')
PURPLE_LIGHT = colors.HexColor('#a99de0')
GOLD         = colors.HexColor('#c9a84c')
GOLD_PALE    = colors.HexColor('#faf6ec')
CREAM        = colors.HexColor('#faf5ef')
WHITE        = colors.white
BLACK        = colors.HexColor('#0a0a0a')
GREY_700     = colors.HexColor('#3d3d3d')
GREY_500     = colors.HexColor('#6b6b6b')
GREY_300     = colors.HexColor('#c8c8c8')
GREY_100     = colors.HexColor('#f6f6f4')

PAGE_W, PAGE_H = A4
ML = 20*mm; MR = 20*mm; MT = 14*mm; MB = 16*mm
CW = PAGE_W - ML - MR

LOGO_WHITE = os.path.join(os.path.dirname(__file__), 'assets', 'logo-white.png')
LOGO_COLOR = os.path.join(os.path.dirname(__file__), 'assets', 'logo-color.png')

def st(name, **kw):
    d = dict(fontName='Helvetica', fontSize=9, leading=14,
             textColor=GREY_700, spaceAfter=0, spaceBefore=0)
    d.update(kw)
    return ParagraphStyle(name, **d)

S = {
    'cover_eyebrow': st('ce', fontName='Helvetica-Bold', fontSize=8,
                        textColor=PURPLE_LIGHT, leading=11, letterSpacing=2),
    'cover_name':    st('cn', fontName='Helvetica-Bold', fontSize=42,
                        textColor=WHITE, leading=48),
    'cover_sub':     st('cs', fontName='Helvetica-BoldOblique', fontSize=52,
                        textColor=GOLD, leading=58),
    'cover_body':    st('cb', fontName='Helvetica', fontSize=16,
                        textColor=WHITE, leading=22, alignment=TA_CENTER),
    'sec_num':       st('sn', fontName='Helvetica-Bold', fontSize=16,
                        textColor=WHITE, leading=20, alignment=TA_CENTER),
    'sec_title':     st('stl', fontName='Helvetica-Bold', fontSize=15,
                        textColor=PURPLE, leading=20),
    'sec_label':     st('sl', fontName='Helvetica-Bold', fontSize=7,
                        textColor=PURPLE, leading=10, letterSpacing=1.8),
    'body':          st('body', fontSize=11, textColor=BLACK, leading=17),
    'body_sm':       st('bsm', fontSize=10, textColor=BLACK, leading=16),
    'bold':          st('bold', fontName='Helvetica-Bold', fontSize=11,
                        textColor=BLACK, leading=17),
    'subhead':       st('sh', fontName='Helvetica-Bold', fontSize=12,
                        textColor=PURPLE_DARK, leading=17),
    'bullet':        st('bul', fontSize=11, textColor=BLACK, leading=17, leftIndent=8),
    'quote':         st('q', fontName='Helvetica-Oblique', fontSize=11,
                        textColor=GREY_700, leading=17),
    'tname':         st('tn', fontName='Helvetica-Bold', fontSize=11,
                        textColor=PURPLE, leading=15),
    'trole':         st('tr', fontSize=9, textColor=GREY_500, leading=13),
    'tbadge':        st('tb', fontName='Helvetica-Bold', fontSize=9,
                        textColor=WHITE, leading=13),
    'cta_h':         st('ch', fontName='Helvetica-Bold', fontSize=26,
                        textColor=WHITE, leading=32, alignment=TA_CENTER),
    'cta_body':      st('cb2', fontSize=12, textColor=WHITE,
                        leading=18, alignment=TA_CENTER),
    'cta_gold':      st('cg', fontName='Helvetica-Bold', fontSize=13,
                        textColor=GOLD, leading=18, alignment=TA_CENTER),
    'cta_link':      st('clink', fontName='Helvetica-Bold', fontSize=11,
                        textColor=PURPLE, leading=16, alignment=TA_CENTER),
    'footer_txt':    st('ft', fontSize=7, textColor=GREY_500, leading=10,
                        alignment=TA_CENTER),
    'cta_label':     st('cl', fontName='Helvetica-Bold', fontSize=10,
                        textColor=PURPLE, leading=14, letterSpacing=2,
                        alignment=TA_CENTER),
    'dark_body':     st('db', fontSize=11, textColor=WHITE, leading=17,
                        alignment=TA_CENTER),
    'dark_gold':     st('dg', fontName='Helvetica-Bold', fontSize=11,
                        textColor=GOLD, leading=16),
    'dark_purple':   st('dp', fontSize=11, textColor=PURPLE_LIGHT, leading=16),
    'book_h':        st('bh', fontName='Helvetica-Bold', fontSize=24,
                        textColor=BLACK, leading=30, alignment=TA_CENTER),
    'book_sub':      st('bs', fontSize=12, textColor=GREY_700, leading=18,
                        alignment=TA_CENTER),
    'book_check':    st('bc', fontSize=12, textColor=GREY_700, leading=20,
                        leftIndent=20),
}

def sp(h): return Spacer(1, h*mm)
def P(txt, s='body'): return Paragraph(txt, S[s])

def gbullet(txt):
    return Paragraph(f'<font color="#c9a84c">&#8212;</font>  {txt}', S['bullet'])

class HLine(Flowable):
    def __init__(self, w=None, color=GOLD, thickness=0.5):
        super().__init__()
        self.width = w or CW
        self.height = thickness
        self.color = color
        self.thickness = thickness
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

class CirclePhoto(Flowable):
    def __init__(self, img_bytes, size=11*mm):
        super().__init__()
        self.img_bytes = img_bytes
        self.size = size
        self.width = size
        self.height = size
    def draw(self):
        c = self.canv
        r = self.size / 2
        c.setFillColor(GREY_100)
        c.circle(r, r, r, fill=1, stroke=0)
        try:
            img = PILImage.open(io.BytesIO(self.img_bytes)).convert('RGB')
            w, h = img.size
            side = min(w, h)
            img = img.crop(((w-side)//2, (h-side)//2,
                             (w+side)//2, (h+side)//2))
            img = img.resize((120, 120), PILImage.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, 'JPEG', quality=92)
            buf.seek(0)
            p = c.beginPath()
            p.circle(r, r, r)
            c.clipPath(p, stroke=0)
            c.drawImage(buf, 0, 0, self.size, self.size,
                        preserveAspectRatio=True, anchor='c')
        except:
            c.setFillColor(GOLD_PALE)
            c.circle(r, r, r, fill=1, stroke=0)

class LeftAccentBox(Flowable):
    def __init__(self, content_list, width, bg, accent_color, pad=4*mm):
        super().__init__()
        self._content = content_list
        self.width = width
        self.bg = bg
        self.accent_color = accent_color
        self.pad = pad
        self.height = 0
        self._table = None
    def wrap(self, avail_w, avail_h):
        t = Table([[self._content]], colWidths=[self.width - 3*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), self.bg),
            ('LEFTPADDING', (0,0), (-1,-1), self.pad + 2*mm),
            ('RIGHTPADDING', (0,0), (-1,-1), self.pad),
            ('TOPPADDING', (0,0), (-1,-1), self.pad),
            ('BOTTOMPADDING', (0,0), (-1,-1), self.pad),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        self._table = t
        w, h = t.wrap(self.width - 3*mm, avail_h)
        self.height = h
        return self.width, self.height
    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.roundRect(3*mm, 0, self.width - 3*mm, self.height, 3, fill=1, stroke=0)
        c.setFillColor(self.accent_color)
        c.roundRect(0, 0, 3*mm, self.height, 2, fill=1, stroke=0)
        if self._table:
            self._table.drawOn(c, 3*mm, 0)

# ── Cover Page ──
def draw_cover(canv, page_w, page_h, name, archetype, personality, stage, goal):
    canv.saveState()

    # Full dark background
    canv.setFillColor(PURPLE_DARK)
    canv.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    top_pad = 60
    y = page_h - top_pad

    # White logo centered
    logo_w, logo_h = 200, 56
    logo_x = (page_w - logo_w) / 2
    try:
        canv.drawImage(LOGO_WHITE, logo_x, y - logo_h,
                       width=logo_w, height=logo_h,
                       preserveAspectRatio=True, mask='auto')
    except:
        canv.setFillColor(WHITE)
        canv.setFont('Helvetica-Bold', 14)
        canv.drawCentredString(page_w / 2, y - 30, 'THE5TH CONSULTING')
    y -= logo_h + 50

    # Eyebrow label
    canv.setFillColor(PURPLE_LIGHT)
    canv.setFont('Helvetica', 10)
    canv.drawCentredString(page_w / 2, y, 'YOUR PERSONALISED GROWTH BLUEPRINT')
    y -= 20

    # Gold rule
    rule_x = 40
    rule_w = page_w - 80
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(1)
    canv.line(rule_x, y, rule_x + rule_w, y)
    y -= 30

    # "Prepared exclusively for"
    canv.setFillColor(WHITE)
    canv.setFont('Helvetica', 16)
    canv.drawCentredString(page_w / 2, y, 'Prepared exclusively for')
    y -= 8

    # Name
    canv.setFillColor(WHITE)
    canv.setFont('Helvetica-Bold', 42)
    canv.drawCentredString(page_w / 2, y - 36, name)
    y -= 36 + 16

    # Archetype italic gold
    canv.setFillColor(GOLD)
    canv.setFont('Helvetica-BoldOblique', 52)
    canv.drawCentredString(page_w / 2, y - 46, f'{archetype}.')
    y -= 46 + 20

    # Gold rule
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(1)
    canv.line(rule_x, y, rule_x + rule_w, y)
    y -= 24

    # Personality type
    canv.setFillColor(PURPLE_LIGHT)
    canv.setFont('Helvetica', 11)
    canv.drawCentredString(page_w / 2, y, f'Personality Type: {personality}')
    y -= 60

    # Stats row — 3 columns, total width 400, centered
    block_w = 400
    col_w = block_w / 3
    block_x = (page_w - block_w) / 2
    stats = [('ARCHETYPE', archetype), ('GOAL', goal), ('STAGE', stage)]
    for i, (lbl, val) in enumerate(stats):
        col_x = block_x + i * col_w + col_w / 2
        # Vertical separator
        if i > 0:
            sep_x = block_x + i * col_w
            canv.setStrokeColor(PURPLE_MID)
            canv.setLineWidth(0.6)
            canv.line(sep_x, y - 4, sep_x, y + 20)
        canv.setFillColor(PURPLE_LIGHT)
        canv.setFont('Helvetica-Bold', 8)
        canv.drawCentredString(col_x, y + 14, lbl)
        canv.setFillColor(WHITE)
        canv.setFont('Helvetica-Bold', 11)
        canv.drawCentredString(col_x, y, val)

    # Confidential footer
    canv.setFillColor(PURPLE_MID)
    canv.setFont('Helvetica', 8)
    canv.drawCentredString(page_w / 2, 22,
                           'Confidential \xb7 Created exclusively for you \xb7 Do not distribute')

    canv.setFillColor(PURPLE_LIGHT)
    canv.setFont('Helvetica', 8)
    canv.drawCentredString(page_w / 2, 12, 'quiz.the5th.consulting')

    canv.restoreState()

# ── Interior Page Template ──
def page_later(canv, doc):
    canv.saveState()

    # Header logo
    try:
        canv.drawImage(LOGO_COLOR, 40, PAGE_H - 52,
                       width=90, height=25,
                       preserveAspectRatio=True, mask='auto')
    except:
        canv.setFillColor(PURPLE)
        canv.setFont('Helvetica-Bold', 8)
        canv.drawString(40, PAGE_H - 45, 'THE5TH CONSULTING')

    canv.setFillColor(GREY_500)
    canv.setFont('Helvetica', 8)
    canv.drawRightString(PAGE_W - MR, PAGE_H - 45, 'Your Personalised Blueprint')

    # Gold rule below header
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(0.5)
    canv.line(ML, PAGE_H - 58, PAGE_W - MR, PAGE_H - 58)

    # Gold rule above footer
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(0.5)
    canv.line(ML, MB - 2*mm, PAGE_W - MR, MB - 2*mm)

    # Footer
    canv.setFillColor(GREY_500)
    canv.setFont('Helvetica', 8)
    canv.drawString(ML, MB - 7*mm, 'support@10kroadmap.org')
    canv.drawCentredString(PAGE_W / 2, MB - 7*mm, str(doc.page - 1))
    canv.drawRightString(PAGE_W - MR, MB - 7*mm, 'quiz.the5th.consulting')

    canv.restoreState()

# ── Section Header ──
def sec_head(num, title):
    circle_size = 24
    items = [
        Paragraph(f'<font color="#ffffff"><b>{num:02d}</b></font>',
                  ParagraphStyle('sn2', fontName='Helvetica-Bold', fontSize=16,
                                 textColor=WHITE, leading=20, alignment=TA_CENTER)),
    ]

    class CircleNum(Flowable):
        def __init__(self, n):
            super().__init__()
            self.n = n
            self.width = circle_size
            self.height = circle_size
        def draw(self):
            c = self.canv
            r = self.width / 2
            c.setFillColor(PURPLE)
            c.circle(r, r, r, fill=1, stroke=0)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 12)
            c.drawCentredString(r, r - 4, f'{self.n:02d}')

    data = [[CircleNum(num), [sp(1), P(title, 'sec_title')]]]
    t = Table(data, colWidths=[10*mm, CW - 10*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    return t

def parse_sections(text):
    sections = {}
    current_key = None
    current_lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('## '):
            if current_key:
                sections[current_key] = '\n'.join(current_lines).strip()
            current_key = stripped[3:].strip().upper()
            current_lines = []
        elif stripped.startswith('# '):
            pass
        else:
            current_lines.append(stripped)
    if current_key:
        sections[current_key] = '\n'.join(current_lines).strip()
    return sections

def render_text_block(text, default_style='body'):
    items = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            items.append(sp(1.5))
            continue
        if line.startswith('- ') or line.startswith('* '):
            items.append(gbullet(line[2:]))
        elif line.startswith('**') and line.endswith('**'):
            items.append(P(line[2:-2], 'bold'))
        elif '**' in line:
            parts = line.split('**')
            result = ''
            for i, part in enumerate(parts):
                result += f'<b>{part}</b>' if i % 2 == 1 else part
            items.append(Paragraph(result, S[default_style]))
        else:
            items.append(P(line, default_style))
    return items

# ── Archetype Content ──
ARCHETYPE_CONTENT = {
    "The Pioneer": {
        "who": """You are wired for momentum. You see opportunities before others do, move fast, and naturally attract attention through energy and ideas. You think in possibilities. You get excited quickly and you execute quickly.

This is your greatest strength — and your greatest vulnerability.

Pioneers build fast. They also lose focus just as fast. The coaches who plateau at $3K–5K months are almost always Pioneers who never installed the systems to hold their own momentum in place.

Your growth does not require more ideas. It requires one idea executed with relentless consistency over 90 days.""",
        "why_not": [
            ("Authority-first strategies fail Pioneers.", "Building thought leadership through long-form content requires patience and delayed gratification over months. Pioneers abandon this before it compounds. You will start strong, produce excellent content for 2–3 weeks, then disappear when something more exciting appears."),
            ("Relationship-only strategies fail Pioneers.", "Deep 1:1 nurturing and community-led growth feels painfully slow to a Pioneer. You need volume, variety, and visible progress to stay motivated. A strategy that requires 90 days of quiet relationship building before a single sale will drain you."),
            ("Systems-first strategies fail Pioneers.", "Starting with funnels, automations, and SOPs before you have consistent revenue kills a Pioneer’s momentum before it starts. You will spend 6 weeks building infrastructure for a business that does not yet exist."),
        ],
        "what_works": "Fast outreach. Fast offers. Fast feedback loops. You need to be in conversation with new people every single day, making offers consistently, and closing weekly. Revenue first. Systems second. The infrastructure gets built after the cash is flowing — not before."
    },
    "The Pathfinder": {
        "who": """You are a natural transformer. People trust you quickly and deeply. You have an extraordinary ability to meet people where they are, understand their struggles at a level most coaches never reach, and guide them through genuine change. Your clients get results. This is not in question.

What is in question is whether your business reflects the value you actually deliver.

Pathfinders almost always undercharge. Not because they lack confidence — but because charging what they are worth feels like it conflicts with why they do the work. This belief is keeping you small.""",
        "why_not": [
            ("High-volume content strategies fail Pathfinders.", "Posting 30 times a month and chasing viral reach feels performative and hollow to you. You did not become a coach to become a content machine. Strategies that require constant visibility exhaust Pathfinders quickly."),
            ("Aggressive sales frameworks fail Pathfinders.", "High-pressure closing techniques feel manipulative to you. If a sales method requires you to override someone’s hesitation rather than address it honestly, you will abandon the method — not the prospect."),
            ("Volume-based offers fail Pathfinders.", "Selling low-ticket products to large audiences contradicts the depth of transformation you deliver. Every time you discount your work, you erode the premium positioning your expertise deserves."),
        ],
        "what_works": "Deep trust, clear positioning, and premium pricing. You need a small number of ideal clients paying high-ticket rates. Your model is not volume — it is depth. One perfectly positioned offer, sold through honest conversation, to the right person at the right time."
    },
    "The Builder": {
        "who": """You are an exceptional problem solver. Where others see complexity, you see architecture. You can take a messy, unclear situation and build a structured, logical path through it. Your clients do not just feel better — they have better systems, better processes, and better results because of you.

Your challenge is not capability. It is visibility. Builders are often the most qualified coaches in the room — and the least known.""",
        "why_not": [
            ("Personality-driven content fails Builders.", "Strategies that require you to be vulnerable, emotional, or entertainment-focused on social media feel deeply uncomfortable. You are not a performer. Trying to grow through personal brand storytelling will feel inauthentic and you will stop."),
            ("Referral-only growth fails Builders.", "Waiting for word of mouth to fill your pipeline is too passive and too slow. Builders need a systematic, controllable lead generation method — not one that depends entirely on other people’s behaviour."),
            ("Inspiration-led marketing fails Builders.", "Your audience does not just want to feel motivated. They want proof that your method works. Vague motivational content does not convert for Builders — results, frameworks, and case studies do."),
        ],
        "what_works": "Structured lead generation with a clear, results-focused offer. Case studies, frameworks, and demonstrated outcomes. Your marketing should show your thinking, not your personality. Teach your methodology publicly. Let the rigour of your approach speak for itself."
    },
    "The Luminary": {
        "who": """You carry authority naturally. When you speak, people listen. When you share a perspective, people trust it. You have accumulated wisdom, experience, and insight that others simply do not have access to — and people sense that the moment they encounter you.

Your challenge is not credibility. You have more credibility than most coaches will ever build. Your challenge is converting that credibility into a consistent, reliable flow of paying clients.""",
        "why_not": [
            ("High-frequency content strategies fail Luminaries.", "Posting daily content to chase algorithm reach feels beneath the level of authority you have built. Luminaries who try to compete on content volume dilute their positioning and confuse their audience."),
            ("Discount or volume-based offers fail Luminaries.", "Selling low-ticket products to large audiences contradicts the premium positioning your presence naturally creates. Every time you discount, you erode the authority you have spent years building."),
            ("Copying other coaches’ growth models fails Luminaries.", "You are not an emerging coach trying to get noticed. You are an established voice trying to monetise influence. The strategies built for coaches starting from zero will actively harm your positioning."),
        ],
        "what_works": "Selective visibility with premium positioning. You do not need a large audience. You need the right audience seeing the right message. One high-ticket offer, a clear point of view, and a simple conversion system built around your existing authority."
    }
}

# ── Dark Page: Archetype Deep Dive ──
def draw_archetype_page(canv, page_w, page_h, archetype, personality, content):
    canv.saveState()
    canv.setFillColor(PURPLE_DARK)
    canv.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    cx = page_w / 2
    y = page_h - 60

    # Section label
    canv.setFillColor(GOLD)
    canv.setFont('Helvetica-Bold', 10)
    canv.drawCentredString(cx, y, 'UNDERSTANDING YOUR ARCHETYPE')
    y -= 16

    # Gold rule
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(1)
    canv.line(40, y, page_w - 40, y)
    y -= 36

    # Archetype name
    canv.setFillColor(WHITE)
    canv.setFont('Helvetica-Bold', 28)
    canv.drawCentredString(cx, y, archetype)
    y -= 22

    # Personality subheading
    canv.setFillColor(PURPLE_LIGHT)
    canv.setFont('Helvetica', 13)
    canv.drawCentredString(cx, y, f'Personality Type: {personality}')
    y -= 18

    # Gold rule
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(1)
    canv.line(40, y, page_w - 40, y)
    y -= 28

    margin_x = 40
    text_w = page_w - margin_x * 2
    line_h_body = 15
    line_h_sub = 16

    def draw_wrapped(text, font, size, color, y_pos, line_h, align='left'):
        canv.setFillColor(color)
        canv.setFont(font, size)
        words = text.split(' ')
        lines = []
        cur = ''
        for w in words:
            test = (cur + ' ' + w).strip()
            if canv.stringWidth(test, font, size) <= text_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        for ln in lines:
            if y_pos < 30:
                break
            if align == 'center':
                canv.drawCentredString(cx, y_pos, ln)
            else:
                canv.drawString(margin_x, y_pos, ln)
            y_pos -= line_h
        return y_pos - 4

    # WHO YOU ARE
    y = draw_wrapped('WHO YOU ARE', 'Helvetica-Bold', 11, GOLD, y, line_h_sub)
    for para in content['who'].split('\n\n'):
        para = para.strip()
        if para:
            y = draw_wrapped(para, 'Helvetica', 10, WHITE, y, line_h_body)
            y -= 6

    y -= 4
    # WHY OTHER GROWTH MODELS WILL NOT WORK
    y = draw_wrapped('WHY OTHER GROWTH MODELS WILL NOT WORK FOR YOU',
                     'Helvetica-Bold', 11, GOLD, y, line_h_sub)
    for subhead, body in content['why_not']:
        y = draw_wrapped(subhead, 'Helvetica-Bold', 10, PURPLE_LIGHT, y, line_h_sub)
        y = draw_wrapped(body, 'Helvetica', 10, WHITE, y, line_h_body)
        y -= 6

    y -= 4
    # WHAT ACTUALLY WORKS
    y = draw_wrapped('WHAT ACTUALLY WORKS FOR YOU',
                     'Helvetica-Bold', 11, GOLD, y, line_h_sub)
    draw_wrapped(content['what_works'], 'Helvetica', 10, WHITE, y, line_h_body)

    canv.restoreState()

# ── Dark Canvas Page via Flowable wrapper ──
class CanvasPage(Flowable):
    """Renders a full-page canvas callback as a flowable that forces a page break."""
    def __init__(self, draw_fn, *args, **kwargs):
        super().__init__()
        self._draw_fn = draw_fn
        self._args = args
        self._kwargs = kwargs
        self.width = PAGE_W
        self.height = PAGE_H
    def wrap(self, aw, ah):
        return (PAGE_W, PAGE_H)
    def draw(self):
        self._draw_fn(self.canv, PAGE_W, PAGE_H, *self._args, **self._kwargs)

# ── Activation Page (dark, canvas drawn) ──
def draw_activation_page(canv, page_w, page_h):
    canv.saveState()
    canv.setFillColor(PURPLE_DARK)
    canv.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    cx = page_w / 2
    y = page_h - 55

    def cstr(text, font, size, color, y_pos, gap=14):
        canv.setFillColor(color)
        canv.setFont(font, size)
        canv.drawCentredString(cx, y_pos, text)
        return y_pos - gap

    def rule(y_pos, gap=16):
        canv.setStrokeColor(GOLD)
        canv.setLineWidth(1)
        canv.line(40, y_pos, page_w - 40, y_pos)
        return y_pos - gap

    def wrapped_center(text, font, size, color, y_pos, line_h=16, max_w=None):
        mw = max_w or (page_w - 100)
        canv.setFillColor(color)
        canv.setFont(font, size)
        words = text.split(' ')
        lines = []
        cur = ''
        for w in words:
            test = (cur + ' ' + w).strip()
            if canv.stringWidth(test, font, size) <= mw:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        for ln in lines:
            if y_pos < 20: break
            canv.drawCentredString(cx, y_pos, ln)
            y_pos -= line_h
        return y_pos - 4

    y = cstr('YOUR ACTION STARTS NOW', 'Helvetica-Bold', 10, GOLD, y, 14)
    y = rule(y, 18)
    y = wrapped_center('This Blueprint Only Works If You Do.',
                       'Helvetica-Bold', 26, WHITE, y, 32)
    y = rule(y, 18)

    body1 = (
        "You now have something most coaches spend years searching for. "
        "A personalised roadmap built around exactly how you think, "
        "how you operate, and where you are right now."
    )
    y = wrapped_center(body1, 'Helvetica', 12, WHITE, y, 18)
    y -= 6

    body2 = (
        "Most people will read this once, feel inspired for 48 hours, "
        "and go back to doing exactly what they were doing before."
    )
    y = wrapped_center(body2, 'Helvetica', 12, WHITE, y, 18)
    y -= 6

    y = wrapped_center("Do not be that person.", 'Helvetica-Bold', 12, WHITE, y, 18)
    y -= 6
    y = wrapped_center("Print this out. Right now.", 'Helvetica-Bold', 12, WHITE, y, 18)
    y = wrapped_center("Put it somewhere you see it every single morning.",
                       'Helvetica', 12, WHITE, y, 18)
    y -= 14

    y = wrapped_center('STARTING TOMORROW — HERE IS WHAT HAPPENS:',
                       'Helvetica-Bold', 13, GOLD, y, 20)
    y -= 4

    body3 = (
        "You will receive a daily coaching email for 7 days. "
        "Each email contains one task. One action. "
        "One move that builds on the last. "
        "Every email is written specifically for your archetype, "
        "your stage, and your income goal. These are not generic tips."
    )
    y = wrapped_center(body3, 'Helvetica', 12, WHITE, y, 18)
    y -= 14

    y = wrapped_center('WHAT WE NEED FROM YOU:',
                       'Helvetica-Bold', 13, GOLD, y, 20)
    y -= 4

    for line in ['Reply to every email.', 'Ask questions.',
                 'Tell us what happened.', 'Tell us what blocked you.',
                 'Tell us what worked.']:
        y = cstr(line, 'Helvetica-Bold', 13, GOLD, y, 20)
    y -= 6

    body4 = (
        "The real coaching happens in the replies. "
        "Every question you ask sharpens your next email. "
        "This is a live two-way coaching experience. But only if you show up."
    )
    y = wrapped_center(body4, 'Helvetica', 11, WHITE, y, 17)
    y -= 12

    y = wrapped_center(
        "If you follow this blueprint and engage with every email — "
        "your business will look measurably different in 30 days.",
        'Helvetica-Bold', 16, WHITE, y, 22)
    y -= 14

    y = cstr('This is your moment.', 'Helvetica-Bold', 18, GOLD, y, 26)
    cstr('Do not waste it.', 'Helvetica-Bold', 18, GOLD, y, 26)

    canv.restoreState()

# ── Book Your Call Page (light background) ──
def draw_book_page(canv, page_w, page_h):
    canv.saveState()
    canv.setFillColor(GOLD_PALE)
    canv.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    cx = page_w / 2
    y = page_h - 60

    def cstr(text, font, size, color, y_pos, gap=14):
        canv.setFillColor(color)
        canv.setFont(font, size)
        canv.drawCentredString(cx, y_pos, text)
        return y_pos - gap

    def rule(y_pos, gap=16):
        canv.setStrokeColor(GOLD)
        canv.setLineWidth(1)
        canv.line(40, y_pos, page_w - 40, y_pos)
        return y_pos - gap

    def wrapped_center(text, font, size, color, y_pos, line_h=17, max_w=None):
        mw = max_w or (page_w - 100)
        canv.setFillColor(color)
        canv.setFont(font, size)
        words = text.split(' ')
        lines = []
        cur = ''
        for w in words:
            test = (cur + ' ' + w).strip()
            if canv.stringWidth(test, font, size) <= mw:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        for ln in lines:
            if y_pos < 40: break
            canv.drawCentredString(cx, y_pos, ln)
            y_pos -= line_h
        return y_pos - 4

    y = cstr('ONE MORE THING', 'Helvetica-Bold', 10, PURPLE, y, 14)
    y = rule(y, 20)

    y = wrapped_center('Want To Map Your Entire Business In 60 Minutes?',
                       'Helvetica-Bold', 24, BLACK, y, 30)
    y -= 8

    y = wrapped_center(
        'Your blueprint gives you the roadmap. A strategy call gives you the shortcut.',
        'Helvetica', 12, GREY_700, y, 18)
    y -= 8

    y = wrapped_center(
        'In one 60-minute session with Indrodip, you will walk away with:',
        'Helvetica', 12, GREY_700, y, 18)
    y -= 10

    checks = [
        '✓  Your offer completely defined and priced',
        '✓  Your exact sales conversation mapped out',
        '✓  Your 30-day revenue plan ready to execute',
        '✓  Every question blocking you — answered',
    ]
    check_x = cx - 160
    for line in checks:
        canv.setFillColor(GREY_700)
        canv.setFont('Helvetica', 12)
        canv.drawString(check_x, y, line)
        y -= 20
    y -= 8

    body = (
        "No fluff. No theory. Just a precise, executable plan built around your specific situation. "
        "Spaces are limited. This call is for coaches who are ready to move fast."
    )
    y = wrapped_center(body, 'Helvetica', 11, GREY_700, y, 17)
    y -= 20

    # CTA button rectangle
    btn_h = 50
    btn_x = 40
    btn_w = page_w - 80
    canv.setFillColor(PURPLE_DARK)
    canv.roundRect(btn_x, y - btn_h, btn_w, btn_h, 4, fill=1, stroke=0)
    canv.setFillColor(WHITE)
    canv.setFont('Helvetica-Bold', 16)
    canv.drawCentredString(cx, y - btn_h / 2 - 6, 'BOOK YOUR 60-MINUTE STRATEGY CALL')
    y -= btn_h + 16

    y = cstr('https://cal.com/indrodip-ghosh-ut1vxh/60min',
             'Helvetica-Bold', 11, PURPLE, y, 16)
    cstr('Click the link above or copy it into your browser',
         'Helvetica', 9, GREY_500, y, 14)

    canv.restoreState()

# ── Request Model ──
class PDFRequest(BaseModel):
    name: str
    stage: Optional[str] = 'launched'
    goal: Optional[str] = '$5K-$10K / month'
    hours: Optional[str] = '10-20'
    video_url: Optional[str] = 'https://quiz.the5th.consulting/video/v1'
    roadmap: str
    archetype: Optional[str] = 'The Pioneer'
    personality: Optional[str] = 'The Driver'

TESTIMONIALS = [
    dict(
        name='Laurie Gerber',
        role='Online Course Creator',
        result='$26,000 in 3 months',
        quote='After a failed launch I had lost confidence completely. We rebuilt the strategy, repositioned my pricing from $79 to $225, and within three months generated $26,000 in revenue. I still find that number hard to believe.',
    ),
    dict(
        name='Abbas Jamie',
        role='Author and Speaker',
        result='Amazon Bestseller in 1 month',
        quote='I had spoken to multiple agencies before finding Indrodip. None delivered. Within one month I became an Amazon bestselling author. The result spoke for itself.',
    ),
    dict(
        name='Jeanne Tomasak',
        role='Business Coach',
        result='First client in 6 weeks',
        quote='I had spent over $10,000 on coaches before working with Indrodip. None gave me the clarity he did. He rebuilt how I saw my business from niche to offer to sales conversation. Six weeks later I closed my first client.',
    ),
    dict(
        name='Angela Gregg',
        role='Education Program Director',
        result='First $2,500 sale',
        quote='After burning through $25,000 on coaches who did not understand my context, two months with Indrodip and I closed my first $2,500 sale. For someone who had nearly given up, that meant everything.',
    ),
]

@app.post('/generate-pdf')
async def generate_pdf(req: PDFRequest):
    buf = io.BytesIO()
    sections = parse_sections(req.roadmap)

    archetype = req.archetype or 'The Pioneer'
    personality = req.personality or 'The Driver'
    archetype_content = ARCHETYPE_CONTENT.get(archetype, ARCHETYPE_CONTENT['The Pioneer'])

    story = []
    story.append(sp(4))

    section_defs = [
        ('YOUR SITUATION RIGHT NOW',  1, 'body',    None,       None),
        ('YOUR SIGNATURE OFFER',       2, 'body',    GOLD_PALE,  PURPLE),
        ('YOUR LEAD MAGNET IDEA',      3, 'body_sm', GOLD_PALE,  GOLD),
        ('YOUR DIGITAL PRODUCT IDEA',  4, 'body_sm', GREY_100,   GREY_300),
        ('7-DAY CONTENT PLAN',         5, 'body_sm', None,       None),
        ('30-DAY ACTION PLAN',         6, 'body_sm', None,       None),
        ('YOUR PRICING STRATEGY',      7, 'body',    GOLD_PALE,  GOLD),
        ('YOUR BIGGEST OPPORTUNITY',   8, 'body',    GOLD_PALE,  PURPLE),
    ]

    for sec_key, num, text_style, bg, accent in section_defs:
        text = sections.get(sec_key, '')
        if not text:
            continue
        story.append(KeepTogether([sec_head(num, sec_key), sp(1)]))
        story.append(HLine(color=GOLD, thickness=0.5))
        story.append(sp(3))

        if sec_key == '7-DAY CONTENT PLAN':
            day_rows = []
            for line in text.split('\n'):
                line = line.strip()
                if not line: continue
                if '**Day' in line or line.lower().startswith('day '):
                    parts = line.replace('**','').split(':', 1)
                    day_rows.append((parts[0].strip(), parts[1].strip() if len(parts)>1 else ''))
            if day_rows:
                tdata = [
                    [
                        Paragraph(d.upper(), ParagraphStyle('dl2', fontName='Helvetica-Bold',
                            fontSize=9, textColor=WHITE, leading=13,
                            backColor=PURPLE_DARK)),
                        Paragraph(c, S['body_sm'])
                    ] for d, c in day_rows
                ]
                rt = Table(tdata, colWidths=[28*mm, CW - 28*mm])
                rt.setStyle(TableStyle([
                    ('ROWBACKGROUNDS', (0,0), (-1,-1), [GOLD_PALE, WHITE]),
                    ('BACKGROUND', (0,0), (0,-1), PURPLE_DARK),
                    ('LEFTPADDING', (0,0), (-1,-1), 4*mm),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4*mm),
                    ('TOPPADDING', (0,0), (-1,-1), 3.5*mm),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3.5*mm),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LINEBELOW', (0,0), (-1,-1), 0.3, GREY_300),
                    ('LINEBEFORE', (1,0), (1,-1), 0.3, GREY_300),
                ]))
                story.append(rt)

        elif sec_key == '30-DAY ACTION PLAN':
            week_rows = []
            cur_wk = None; cur_items = []
            for line in text.split('\n'):
                line = line.strip()
                if not line: continue
                if 'Week' in line:
                    if cur_wk: week_rows.append((cur_wk, cur_items[:]))
                    parts = line.replace('**','').split(':', 1)
                    cur_wk = parts[0].strip()
                    cur_items = [parts[1].strip()] if len(parts)>1 else []
                else:
                    cur_items.append(line.replace('**',''))
            if cur_wk: week_rows.append((cur_wk, cur_items))
            wk_colors = [
                (GOLD_PALE, PURPLE), (GREY_100, PURPLE_MID),
                (GOLD_PALE, GOLD), (GREY_100, PURPLE),
            ]
            for i, (wk, actions) in enumerate(week_rows):
                wbg, wacc = wk_colors[i % 4]
                items = []
                for j, act in enumerate([a for a in actions if a.strip()]):
                    items.append(Paragraph(
                        f'<font color="#8b7fcf"><b>{j+1}</b></font>  {act}',
                        S['body_sm']))
                    items.append(sp(1.5))
                wdata = [[
                    Paragraph(wk, ParagraphStyle('wkl', fontName='Helvetica-Bold',
                        fontSize=10, textColor=wacc, leading=14)),
                    items
                ]]
                wt = Table(wdata, colWidths=[28*mm, CW - 28*mm])
                wt.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), wbg),
                    ('LEFTPADDING', (0,0), (-1,-1), 4*mm),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4*mm),
                    ('TOPPADDING', (0,0), (-1,-1), 4*mm),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4*mm),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LINEBEFORE', (1,0), (1,-1), 0.3, GREY_300),
                    ('LINEBELOW', (0,0), (-1,-1), 0.3, GREY_300),
                ]))
                story.append(wt)
                story.append(sp(2))
        else:
            content_items = render_text_block(text, text_style)
            if bg and accent:
                story.append(LeftAccentBox(content_items, CW, bg, accent))
            else:
                for item in content_items:
                    story.append(item)

        story.append(sp(6))
        story.append(HLine(color=GOLD, thickness=0.5))
        story.append(sp(6))

    # ── Testimonials ──
    story.append(P('WHAT OUR CLIENTS SAY', 'sec_label'))
    story.append(sp(4))
    half = (CW - 3*mm) / 2

    for i in range(0, len(TESTIMONIALS), 2):
        row = []
        for j in range(2):
            idx = i + j
            if idx >= len(TESTIMONIALS):
                row.append('')
                continue
            t = TESTIMONIALS[idx]
            cell = []
            cell.append(Paragraph(
                f'<font color="#c9a84c" size="18"><b>&#8220;</b></font>',
                S['body']))
            cell.append(sp(2))
            cell.append(Paragraph(t['quote'], S['quote']))
            cell.append(sp(4))
            name_data = [[
                [
                    Paragraph(t['name'], S['tname']),
                    Paragraph(t['role'], S['trole']),
                ],
                Paragraph(t['result'], ParagraphStyle(
                    'res', fontName='Helvetica-Bold', fontSize=9,
                    textColor=WHITE, leading=13,
                    backColor=PURPLE_DARK,
                    borderPadding=(3, 6, 3, 6)
                )),
            ]]
            name_t = Table(name_data, colWidths=[half*0.6, half*0.35])
            name_t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ]))
            cell.append(name_t)
            row.append(cell)

        rt = Table([row], colWidths=[half, half])
        rt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), GOLD_PALE),
            ('BOX', (0,0), (0,0), 4, PURPLE),
            ('BOX', (1,0), (1,0), 4, PURPLE),
            ('LEFTPADDING', (0,0), (-1,-1), 5*mm),
            ('RIGHTPADDING', (0,0), (-1,-1), 5*mm),
            ('TOPPADDING', (0,0), (-1,-1), 5*mm),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5*mm),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEBEFORE', (1,0), (1,-1), 0.4, GREY_300),
        ]))
        story.append(rt)
        story.append(sp(3))

    story.append(sp(6))

    # ── About Indrodip ──
    about_content = [
        sp(2),
        Paragraph('ABOUT INDRODIP GHOSH', S['sec_label']),
        sp(4),
        Paragraph('Founder, The5th Consulting', ParagraphStyle(
            'about_role', fontName='Helvetica-Bold', fontSize=11,
            textColor=WHITE, leading=16)),
        sp(3),
        Paragraph(
            'Indrodip Ghosh is the founder of The5th Consulting, a digital coaching business '
            'helping women over 40 monetize their life experience and expertise into consistent '
            'digital income. His flagship methodology, the Client-To-Cash Method, has helped '
            'hundreds of coaches, consultants, and experts package their knowledge into '
            'high-ticket offers and build predictable revenue.',
            ParagraphStyle('ab', fontSize=11, textColor=WHITE, leading=17)
        ),
        sp(3),
        Paragraph(
            'Before founding The5th, Indrodip spent years in the coaching and consulting industry, '
            'studying what separates coaches who struggle from those who build sustainable businesses. '
            'The answer was never about talent. It was always about positioning, offer clarity, '
            'and the courage to charge what their expertise is worth.',
            ParagraphStyle('ab2', fontSize=11, textColor=WHITE, leading=17)
        ),
        sp(4),
        HLine(color=GOLD, thickness=0.5),
        sp(4),
        Paragraph('THE5TH CONSULTING', S['sec_label']),
        sp(3),
    ]

    about_t = Table([[about_content]], colWidths=[CW])
    about_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PURPLE_DARK),
        ('LEFTPADDING', (0,0), (-1,-1), 8*mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 8*mm),
        ('TOPPADDING', (0,0), (-1,-1), 8*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8*mm),
        ('LINEABOVE', (0,0), (-1,0), 2, GOLD),
    ]))
    story.append(about_t)

    # Offer stack
    offer_w = (CW - 4*mm) / 2
    offer_data = [[
        [
            Paragraph('10K Roadmap Accelerator', ParagraphStyle(
                'prod', fontName='Helvetica-Bold', fontSize=11,
                textColor=PURPLE, leading=15)),
            sp(1),
            Paragraph('Flagship 1:1 high-ticket coaching program for coaches and consultants ready to build a $10K/month business.', S['body_sm']),
        ],
        [
            Paragraph('The5th Community', ParagraphStyle(
                'prod2', fontName='Helvetica-Bold', fontSize=11,
                textColor=PURPLE, leading=15)),
            sp(1),
            Paragraph('Monthly membership with live coaching calls, resources, and a community of women building digital income.', S['body_sm']),
        ],
    ]]
    offer_t = Table(offer_data, colWidths=[offer_w, offer_w])
    offer_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GOLD_PALE),
        ('LEFTPADDING', (0,0), (-1,-1), 5*mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 5*mm),
        ('TOPPADDING', (0,0), (-1,-1), 5*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5*mm),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBEFORE', (1,0), (1,-1), 0.4, GREY_300),
    ]))
    story.append(offer_t)
    story.append(sp(4))
    story.append(Paragraph(
        'quiz.the5th.consulting  |  support@10kroadmap.org  |  whop.com/joined/10kroadmap-org/',
        S['footer_txt']
    ))

    # ── Build Doc ──
    first_name = req.name.split()[0] if req.name else 'there'

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT, bottomMargin=MB + 10*mm,
    )

    cover_frame   = Frame(0, 0, PAGE_W, PAGE_H, id='cover',
                          leftPadding=0, rightPadding=0,
                          topPadding=0, bottomPadding=0)
    archetype_frame = Frame(0, 0, PAGE_W, PAGE_H, id='archetype',
                            leftPadding=0, rightPadding=0,
                            topPadding=0, bottomPadding=0)
    activation_frame = Frame(0, 0, PAGE_W, PAGE_H, id='activation',
                             leftPadding=0, rightPadding=0,
                             topPadding=0, bottomPadding=0)
    book_frame    = Frame(0, 0, PAGE_W, PAGE_H, id='book',
                          leftPadding=0, rightPadding=0,
                          topPadding=0, bottomPadding=0)
    content_frame = Frame(ML, MB + 10*mm, CW, PAGE_H - 10*mm - MB - 10*mm, id='content')

    def make_cover_cb(name, arch, pers, stg, gl):
        def cb(canv, doc):
            draw_cover(canv, PAGE_W, PAGE_H, name, arch, pers, stg, gl)
        return cb

    def make_archetype_cb(arch, pers, content):
        def cb(canv, doc):
            draw_archetype_page(canv, PAGE_W, PAGE_H, arch, pers, content)
            page_later(canv, doc)
        return cb

    def make_activation_cb():
        def cb(canv, doc):
            draw_activation_page(canv, PAGE_W, PAGE_H)
            page_later(canv, doc)
        return cb

    def make_book_cb():
        def cb(canv, doc):
            draw_book_page(canv, PAGE_W, PAGE_H)
            page_later(canv, doc)
        return cb

    doc.addPageTemplates([
        PageTemplate(id='Cover',
                     frames=[cover_frame],
                     onPage=make_cover_cb(req.name, archetype, personality,
                                          req.stage, req.goal)),
        PageTemplate(id='Archetype',
                     frames=[archetype_frame],
                     onPage=make_archetype_cb(archetype, personality, archetype_content)),
        PageTemplate(id='Activation',
                     frames=[activation_frame],
                     onPage=make_activation_cb()),
        PageTemplate(id='Book',
                     frames=[book_frame],
                     onPage=make_book_cb()),
        PageTemplate(id='Content',
                     frames=[content_frame],
                     onPage=page_later),
    ])

    full_story = (
        [NextPageTemplate('Archetype'), PageBreak()]
        + [NextPageTemplate('Content'), PageBreak()]
        + story
        + [NextPageTemplate('Activation'), PageBreak()]
        + [NextPageTemplate('Book'), PageBreak()]
        + []
    )

    doc.build(full_story)
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{first_name}-blueprint.pdf"'}
    )

@app.get('/health')
def health():
    return {'status': 'ok'}
