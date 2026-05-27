from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import io, os, math
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

# ── Colors ──
BLACK      = colors.HexColor('#0a0a0a')
GREY_700   = colors.HexColor('#3d3d3d')
GREY_500   = colors.HexColor('#6b6b6b')
GREY_300   = colors.HexColor('#c8c8c8')
GREY_100   = colors.HexColor('#f6f6f4')
WHITE      = colors.white
GREEN      = colors.HexColor('#1d5c3a')
GREEN_MID  = colors.HexColor('#2d7a52')
GREEN_PALE = colors.HexColor('#eaf4ee')
GOLD       = colors.HexColor('#9a7a1a')
GOLD_PALE  = colors.HexColor('#faf6ec')

PAGE_W, PAGE_H = A4
ML = 20*mm; MR = 20*mm; MT = 14*mm; MB = 16*mm
CW = PAGE_W - ML - MR

def st(name, **kw):
    d = dict(fontName='Helvetica', fontSize=9, leading=14,
             textColor=GREY_700, spaceAfter=0, spaceBefore=0)
    d.update(kw)
    return ParagraphStyle(name, **d)

S = {
    'cover_eyebrow': st('ce', fontName='Helvetica-Bold', fontSize=8,
                        textColor=GREEN_MID, leading=11, letterSpacing=2),
    'cover_name':    st('cn', fontName='Helvetica-Bold', fontSize=28,
                        textColor=BLACK, leading=34),
    'cover_sub':     st('cs', fontName='Helvetica-Oblique', fontSize=28,
                        textColor=GREEN, leading=34),
    'cover_body':    st('cb', fontName='Helvetica', fontSize=10,
                        textColor=GREY_500, leading=16),
    'sec_num':       st('sn', fontName='Helvetica-Bold', fontSize=44,
                        textColor=colors.HexColor('#eeeeee'), leading=48),
    'sec_title':     st('stl', fontName='Helvetica-Bold', fontSize=12,
                        textColor=BLACK, leading=17),
    'sec_label':     st('sl', fontName='Helvetica-Bold', fontSize=7,
                        textColor=GREEN, leading=10, letterSpacing=1.8),
    'body':          st('body', fontSize=9.5, textColor=GREY_700, leading=15.5),
    'body_sm':       st('bsm', fontSize=8.5, textColor=GREY_700, leading=13.5),
    'bold':          st('bold', fontName='Helvetica-Bold', fontSize=9.5,
                        textColor=BLACK, leading=15),
    'bullet':        st('bul', fontSize=9, textColor=GREY_700, leading=14, leftIndent=8),
    'quote':         st('q', fontName='Helvetica-Oblique', fontSize=9,
                        textColor=GREY_700, leading=14.5),
    'tname':         st('tn', fontName='Helvetica-Bold', fontSize=8.5,
                        textColor=BLACK, leading=12),
    'trole':         st('tr', fontSize=7.5, textColor=GREY_500, leading=11),
    'tbadge':        st('tb', fontName='Helvetica-Bold', fontSize=7.5,
                        textColor=GREEN, leading=11),
    'cta_h':         st('ch', fontName='Helvetica-Bold', fontSize=20,
                        textColor=WHITE, leading=26, alignment=TA_CENTER),
    'cta_body':      st('cb2', fontSize=9.5,
                        textColor=colors.HexColor('#a0c8b4'),
                        leading=15, alignment=TA_CENTER),
    'cta_link':      st('clink', fontName='Helvetica-Bold', fontSize=9.5,
                        textColor=WHITE, leading=14, alignment=TA_CENTER),
    'footer_txt':    st('ft', fontSize=7, textColor=GREY_500, leading=10,
                        alignment=TA_CENTER),
    'cta_label':     st('cl', fontName='Helvetica-Bold', fontSize=7,
                        textColor=GREEN_MID, leading=10, letterSpacing=2,
                        alignment=TA_CENTER),
}

def sp(h): return Spacer(1, h*mm)
def P(txt, s='body'): return Paragraph(txt, S[s])
def gbullet(txt):
    return Paragraph(f'<font color="#1d5c3a">&#8212;</font>  {txt}', S['bullet'])

class HLine(Flowable):
    def __init__(self, w=None, color=GREY_300, thickness=0.4):
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
            c.setFillColor(GREEN_PALE)
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

def draw_cover(canv, page_w, page_h, lead_name, stage, goal, hours):
    canv.saveState()
    canv.setFillColor(colors.HexColor('#060a07'))
    canv.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    canv.setStrokeColor(colors.HexColor('#1a3a28'))
    canv.setLineWidth(0.6)
    for r in range(20, 160, 18):
        canv.circle(page_w - 28*mm, 38*mm, r*mm, fill=0, stroke=1)
    canv.setStrokeColor(colors.HexColor('#162b1e'))
    canv.setLineWidth(0.4)
    for i in range(-10, 30):
        x = i * 8*mm
        canv.line(x, page_h, x + 60*mm, page_h - 60*mm)
    canv.setStrokeColor(colors.HexColor('#225840'))
    canv.setLineWidth(1.2)
    for offset in [0, 6, 12]:
        canv.arc(-40*mm+offset, page_h-130*mm+offset,
                 110*mm+offset, page_h+20*mm+offset, startAng=220, extent=100)
    canv.setStrokeColor(colors.HexColor('#3a9a64'))
    canv.setLineWidth(2.5)
    canv.arc(-10*mm, page_h-90*mm, 80*mm, page_h+10*mm, startAng=230, extent=60)
    dot_positions = [
        (142*mm, page_h-18*mm, 1.2*mm, '#3a9a64'),
        (148*mm, page_h-24*mm, 0.8*mm, '#2d7a52'),
        (155*mm, page_h-16*mm, 0.6*mm, '#225840'),
        (138*mm, page_h-30*mm, 1.0*mm, '#3a9a64'),
        (22*mm, 50*mm, 1.5*mm, '#225840'),
        (30*mm, 44*mm, 0.8*mm, '#3a9a64'),
    ]
    for x, y, r, col in dot_positions:
        canv.setFillColor(colors.HexColor(col))
        canv.circle(x, y, r, fill=1, stroke=0)
    canv.setStrokeColor(colors.HexColor('#1d5c3a'))
    canv.setLineWidth(0.8)
    canv.line(ML, page_h-58*mm, page_w-MR, page_h-58*mm)
    canv.setFillColor(WHITE)
    canv.setFont('Helvetica-Bold', 8.5)
    canv.drawString(ML, page_h-16*mm, 'THE5TH CONSULTING')
    canv.setFillColor(colors.HexColor('#4a9a6a'))
    canv.setFont('Helvetica', 7)
    canv.drawString(ML, page_h-22*mm, 'quiz.the5th.consulting')
    canv.setFillColor(colors.HexColor('#3a9a64'))
    canv.setFont('Helvetica-Bold', 7)
    canv.drawRightString(page_w-MR, page_h-16*mm, 'PERSONALISED BLUEPRINT')
    text_y_start = page_h - 76*mm
    canv.setFillColor(colors.HexColor('#3a9a64'))
    canv.setFont('Helvetica-Bold', 7.5)
    canv.drawString(ML, text_y_start, 'YOUR PERSONALISED BLUEPRINT')
    canv.setFillColor(WHITE)
    canv.setFont('Helvetica-Bold', 32)
    canv.drawString(ML, text_y_start - 14*mm, f'{lead_name}, here is your')
    canv.setFillColor(colors.HexColor('#3a9a64'))
    canv.setFont('Helvetica-Oblique', 32)
    canv.drawString(ML, text_y_start - 26*mm, 'personalised blueprint.')
    canv.setStrokeColor(colors.HexColor('#1d5c3a'))
    canv.setLineWidth(0.5)
    canv.line(ML, text_y_start - 30*mm, ML + 80*mm, text_y_start - 30*mm)
    canv.setFillColor(colors.HexColor('#8a9e92'))
    canv.setFont('Helvetica', 9.5)
    canv.drawString(ML, text_y_start - 37*mm,
                    'Based on your 20 quiz answers, The5th AI has mapped exactly')
    canv.drawString(ML, text_y_start - 43*mm,
                    'where you are and the fastest path to your income goal.')
    stat_y = text_y_start - 60*mm
    stats = [('STAGE', stage.title()), ('6-MONTH GOAL', goal), ('HOURS / WEEK', f'{hours} hrs')]
    col_w = (page_w - ML - MR) / 3
    for i, (label, val) in enumerate(stats):
        x = ML + i * col_w
        if i > 0:
            canv.setStrokeColor(colors.HexColor('#1d3a2a'))
            canv.setLineWidth(0.4)
            canv.line(x - 2*mm, stat_y - 8*mm, x - 2*mm, stat_y + 4*mm)
        canv.setFillColor(colors.HexColor('#4a7a5a'))
        canv.setFont('Helvetica-Bold', 6.5)
        canv.drawString(x, stat_y + 4*mm, label)
        canv.setFillColor(WHITE)
        canv.setFont('Helvetica-Bold', 11)
        canv.drawString(x, stat_y - 3*mm, val)
    canv.setFillColor(colors.HexColor('#2a4a34'))
    canv.setFont('Helvetica', 7)
    canv.drawString(ML, 14*mm, 'Confidential  |  Created exclusively for you  |  Do not distribute')
    canv.restoreState()

def page_later(canv, doc):
    canv.saveState()
    canv.setFillColor(BLACK)
    canv.rect(0, PAGE_H - 10*mm, PAGE_W, 10*mm, fill=1, stroke=0)
    canv.setFillColor(WHITE)
    canv.setFont('Helvetica-Bold', 6.5)
    canv.drawString(ML, PAGE_H - 6.5*mm, 'THE5TH CONSULTING')
    canv.setFillColor(colors.HexColor('#888888'))
    canv.setFont('Helvetica', 6.5)
    canv.drawRightString(PAGE_W - MR, PAGE_H - 6.5*mm, 'Your Personalised Blueprint')
    canv.setStrokeColor(GREY_300)
    canv.setLineWidth(0.4)
    canv.line(ML, MB - 4*mm, PAGE_W - MR, MB - 4*mm)
    canv.setFillColor(GREY_500)
    canv.setFont('Helvetica', 6.5)
    canv.drawString(ML, MB - 9*mm, 'support@10kroadmap.org')
    canv.drawRightString(PAGE_W - MR, MB - 9*mm, f'{doc.page - 1}')
    canv.restoreState()

def sec_head(num, title):
    data = [[P(f'{num:02d}', 'sec_num'), [sp(2), P(title, 'sec_title')]]]
    t = Table(data, colWidths=[14*mm, CW - 14*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
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

class PDFRequest(BaseModel):
    name: str
    stage: Optional[str] = 'launched'
    goal: Optional[str] = '$5K-$10K / month'
    hours: Optional[str] = '10-20'
    video_url: Optional[str] = 'https://quiz.the5th.consulting/video/v1'
    roadmap: str

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
    story = []
    story.append(sp(4))

    section_defs = [
        ('YOUR SITUATION RIGHT NOW',  1, 'body',    None,       None),
        ('YOUR SIGNATURE OFFER',       2, 'body',    GREEN_PALE, GREEN),
        ('YOUR LEAD MAGNET IDEA',      3, 'body_sm', GOLD_PALE,  GOLD),
        ('YOUR DIGITAL PRODUCT IDEA',  4, 'body_sm', GREY_100,   GREY_300),
        ('7-DAY CONTENT PLAN',         5, 'body_sm', None,       None),
        ('30-DAY ACTION PLAN',         6, 'body_sm', None,       None),
        ('YOUR PRICING STRATEGY',      7, 'body',    GOLD_PALE,  GOLD),
        ('YOUR BIGGEST OPPORTUNITY',   8, 'body',    GREEN_PALE, GREEN),
    ]

    for sec_key, num, text_style, bg, accent in section_defs:
        text = sections.get(sec_key, '')
        if not text:
            continue
        story.append(KeepTogether([sec_head(num, sec_key), sp(3)]))

        if sec_key == '7-DAY CONTENT PLAN':
            day_rows = []
            for line in text.split('\n'):
                line = line.strip()
                if not line: continue
                if '**Day' in line or line.lower().startswith('day '):
                    parts = line.replace('**','').split(':', 1)
                    day_rows.append((parts[0].strip(), parts[1].strip() if len(parts)>1 else ''))
            if day_rows:
                tdata = [[
                    Paragraph(d.upper(), ParagraphStyle('dl2', fontName='Helvetica-Bold',
                        fontSize=7.5, textColor=GREEN, leading=11)),
                    Paragraph(c, S['body_sm'])
                ] for d, c in day_rows]
                rt = Table(tdata, colWidths=[28*mm, CW - 28*mm])
                rt.setStyle(TableStyle([
                    ('ROWBACKGROUNDS', (0,0), (-1,-1), [GREY_100, WHITE]),
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
                (GREEN_PALE, GREEN), (GOLD_PALE, GOLD),
                (colors.HexColor('#eef0f8'), colors.HexColor('#3a4abf')),
                (colors.HexColor('#f8eef4'), colors.HexColor('#9a1a6a')),
            ]
            for i, (wk, actions) in enumerate(week_rows):
                wbg, wacc = wk_colors[i % 4]
                items = []
                for j, act in enumerate([a for a in actions if a.strip()]):
                    items.append(Paragraph(f'<font color="#1d5c3a"><b>{j+1}</b></font>  {act}', S['body_sm']))
                    items.append(sp(1.5))
                wdata = [[
                    Paragraph(wk, ParagraphStyle('wkl', fontName='Helvetica-Bold',
                        fontSize=8.5, textColor=wacc, leading=13)),
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
        story.append(HLine())
        story.append(sp(6))

    # Testimonials
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
                '<font color=”#1d5c3a” size=”18”><b>“</b></font>',
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
                    'res', fontName='Helvetica-Bold', fontSize=7.5,
                    textColor=GREEN, leading=11,
                    backColor=GREEN_PALE,
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
            ('BACKGROUND', (0,0), (-1,-1), WHITE),
            ('BOX', (0,0), (0,0), 0.4, GREY_300),
            ('BOX', (1,0), (1,0), 0.4, GREY_300),
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

    # Video CTA
    video_url = req.video_url
    cta_content = [
        sp(2),
        P('ONE MORE THING', 'cta_label'),
        sp(4),
        P('Your personalised video is ready.', 'cta_h'),
        sp(3),
        P('We created a short video based on exactly where you are, because you deserve more than a generic answer.', 'cta_body'),
        sp(5),
        Paragraph(f'<link href="{video_url}"><u>{video_url}</u></link>', S['cta_link']),
        sp(3),
        P('support@10kroadmap.org  |  quiz.the5th.consulting', 'footer_txt'),
        sp(2),
    ]
    cta_t = Table([[cta_content]], colWidths=[CW])
    cta_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLACK),
        ('LEFTPADDING', (0,0), (-1,-1), 10*mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 10*mm),
        ('TOPPADDING', (0,0), (-1,-1), 6*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6*mm),
        ('LINEABOVE', (0,0), (-1,0), 2, GREEN),
    ]))
    story.append(cta_t)

    story.append(sp(8))

    # About section
    about_content = [
        sp(2),
        Paragraph('ABOUT INDRODIP GHOSH', S['sec_label']),
        sp(4),
        Paragraph('Founder, The5th Consulting', ParagraphStyle(
            'about_role', fontName='Helvetica-Bold', fontSize=11,
            textColor=BLACK, leading=16)),
        sp(3),
        Paragraph(
            'Indrodip Ghosh is the founder of The5th Consulting, a digital coaching business '
            'helping women over 40 monetize their life experience and expertise into consistent '
            'digital income. His flagship methodology, the Client-To-Cash Method, has helped '
            'hundreds of coaches, consultants, and experts package their knowledge into '
            'high-ticket offers and build predictable revenue.',
            S['body']
        ),
        sp(3),
        Paragraph(
            'Before founding The5th, Indrodip spent years in the coaching and consulting industry, '
            'studying what separates coaches who struggle from those who build sustainable businesses. '
            'The answer was never about talent. It was always about positioning, offer clarity, '
            'and the courage to charge what their expertise is worth.',
            S['body']
        ),
        sp(4),
        HLine(color=GREEN, thickness=0.5),
        sp(4),
        Paragraph('THE5TH CONSULTING', S['sec_label']),
        sp(3),
        Table([[
            [
                Paragraph('10K Roadmap Accelerator', ParagraphStyle(
                    'prod', fontName='Helvetica-Bold', fontSize=9,
                    textColor=BLACK, leading=13)),
                sp(1),
                Paragraph('Flagship 1:1 high-ticket coaching program for coaches and consultants ready to build a $10K/month business.', S['body_sm']),
            ],
            [
                Paragraph('The5th Community', ParagraphStyle(
                    'prod2', fontName='Helvetica-Bold', fontSize=9,
                    textColor=BLACK, leading=13)),
                sp(1),
                Paragraph('Monthly membership with live coaching calls, resources, and a community of women building digital income.', S['body_sm']),
            ],
        ]], colWidths=[CW/2 - 3*mm, CW/2 - 3*mm]),
        sp(4),
        Paragraph(
            'quiz.the5th.consulting  |  support@10kroadmap.org  |  whop.com/joined/10kroadmap-org/',
            S['footer_txt']
        ),
        sp(2),
    ]

    about_t = Table([[about_content]], colWidths=[CW])
    about_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f7f4')),
        ('LEFTPADDING', (0,0), (-1,-1), 8*mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 8*mm),
        ('TOPPADDING', (0,0), (-1,-1), 8*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8*mm),
        ('LINEABOVE', (0,0), (-1,0), 2, GREEN),
    ]))
    story.append(about_t)

    # Build doc
    first_name = req.name.split()[0] if req.name else 'there'
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT, bottomMargin=MB + 10*mm,
    )
    cover_frame = Frame(ML, MB, CW, PAGE_H - MT - MB, id='cover')
    content_frame = Frame(ML, MB + 10*mm, CW, PAGE_H - 10*mm - MB - 10*mm, id='content')

    def make_cover_cb(name, stg, gl, hrs):
        def cb(canv, doc):
            draw_cover(canv, PAGE_W, PAGE_H, name, stg, gl, hrs)
        return cb

    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[cover_frame],
                     onPage=make_cover_cb(first_name, req.stage, req.goal, req.hours)),
        PageTemplate(id='Content', frames=[content_frame], onPage=page_later),
    ])
    doc.build([NextPageTemplate('Content'), PageBreak()] + story)
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{first_name}-blueprint.pdf"'}
    )

@app.get('/health')
def health():
    return {'status': 'ok'}
