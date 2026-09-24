"""Generate the final terminal SVG using a green version of ertdfgcvb's ASCII Doom Flame.
Reference: https://play.ertdfgcvb.xyz/#/src/demos/doom_flame_full_color
Loops the typing, blinking cursor, and background flames together.
Requires Pillow. Run: python3 scripts/generate-quote-terminal.py
"""
from pathlib import Path
from random import Random
from math import floor
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
COLS, ROWS, CW, CH = 100, 16, 9, 15
PALETTE = ['#000000', '#042510', '#07501c', '#0b802c', '#1aba43', '#67e65f', '#bafc98', '#efffe0']
FLAME = list(map(int, '011222233334444444455566667'))
rng = Random(24)
noise_values = [[rng.random() for _ in range(32)] for _ in range(32)]
def noise(x,y):
    ix,iy=floor(x),floor(y)
    sx,sy=x-ix,y-iy
    sx=sx*sx*(3-2*sx);sy=sy*sy*(3-2*sy)
    a=noise_values[iy%32][ix%32]*(1-sx)+noise_values[iy%32][(ix+1)%32]*sx
    b=noise_values[(iy+1)%32][ix%32]*(1-sx)+noise_values[(iy+1)%32][(ix+1)%32]*sx
    return a*(1-sy)+b*sy

font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',12)
# One shared palette prevents frame-to-frame color changes from GIF quantization.
palette=[]
for c in PALETTE:
    palette.extend(tuple(int(c[i:i+2],16) for i in (1,3,5)))
palette += [0]*(768-len(palette))
sprites={}
for level in range(8):
    for digit in range(10):
        im=Image.new('P',(CW,CH),level)
        im.putpalette(palette)
        if level:
            draw=ImageDraw.Draw(im)
            draw.fontmode='1'
            draw.text((1,0),str(digit),font=font,fill=min(7,level+1))
        sprites[level,digit]=im

heat=[0]*(COLS*ROWS)
def step(t):
    bottom=COLS*(ROWS-1)
    for x in range(COLS):
        target=floor(5+noise(x*.05,t*.05)*45)
        heat[bottom+x]=min(target,heat[bottom+x]+2)
    for y in range(ROWS):
        for x in range(COLS):
            destination=y*COLS+max(0,min(COLS-1,x+rng.randint(-1,1)))
            source=min(ROWS-1,y+1)*COLS+x
            heat[destination]=max(0,heat[source]-rng.randint(0,4))

frames=[]
for t in range(400):
    step(t)
    if t < 100 or t%2:
        continue
    im=Image.new('P',(COLS*CW,ROWS*CH),0)
    im.putpalette(palette)
    for y in range(ROWS):
        for x in range(COLS):
            value=heat[y*COLS+x]
            level=FLAME[min(value,len(FLAME)-1)]
            if level:
                im.paste(sprites[level,value%10],(x*CW,y*CH))
    frames.append(im)

from base64 import b64encode
from io import BytesIO
from xml.etree import ElementTree as ET

lines = ['The only thing necessary for the triumph', 'of evil is for good men to do nothing.']
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',32)
widths = [font.getlength(line) for line in lines]
assert max(widths)+78+16 < 862
count = len(frames)
images, frame_css = [], []
for i, frame in enumerate(frames):
    data = BytesIO()
    frame.save(data, format='PNG', optimize=True)
    encoded = b64encode(data.getvalue()).decode()
    start, end = i/count*100, (i+1)/count*100
    keys = (f'0%{{visibility:visible}}{end:.5f}%,100%{{visibility:hidden}}' if i == 0 else
            f'0%{{visibility:hidden}}{start:.5f}%{{visibility:visible}}{end:.5f}%{{visibility:hidden}}')
    frame_css.append(f'@keyframes frame{i}{{{keys}}}')
    images.append(f'<image class="flame-frame frame-{i}" x="0" y="104" width="900" height="240" href="data:image/png;base64,{encoded}" style="animation-name:frame{i}"/>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="344" viewBox="0 0 900 344" role="img" aria-labelledby="title description">
<title id="title">The only thing necessary for the triumph of evil is for good men to do nothing.</title>
<desc id="description">A terminal repeatedly types the quote, holding the complete text before each replay. A mint cursor blinks and faded green ASCII flames continue behind it. Footer: Edmond Burke.</desc>
<defs>
  <clipPath id="card"><rect width="900" height="344" rx="18"/></clipPath>
  <clipPath id="line-one"><rect class="reveal-one" x="78" y="111" width="{widths[0]+2}" height="43"/></clipPath>
  <clipPath id="line-two"><rect class="reveal-two" x="78" y="161" width="{widths[1]+2}" height="43"/></clipPath>
  <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop stop-color="white" stop-opacity=".07"/><stop offset="1" stop-color="white" stop-opacity=".165"/></linearGradient>
  <mask id="flame-opacity"><rect y="104" width="900" height="240" fill="url(#fade)"/></mask>
</defs>
<style>
text{{font-family:Menlo,Consolas,monospace}}
.flame-frame{{visibility:hidden;animation-duration:10.5s;animation-timing-function:steps(1,end);animation-iteration-count:infinite}}
{''.join(frame_css)}
.reveal-one{{animation:reveal-one 10.5s linear infinite}}
.reveal-two{{animation:reveal-two 10.5s linear infinite}}
@keyframes reveal-one{{0%{{width:0}}4.7619%{{width:0;animation-timing-function:steps({len(lines[0])},end)}}33.8095%,100%{{width:{widths[0]+2}px}}}}
@keyframes reveal-two{{0%{{width:0}}33.8095%{{width:0;animation-timing-function:steps({len(lines[1])},end)}}61.9048%,100%{{width:{widths[1]+2}px}}}}
.cursor-one{{animation:hide-first 10.5s steps(1,end) infinite}}
@keyframes hide-first{{0%{{visibility:visible}}33.8095%,100%{{visibility:hidden}}}}
.cursor-two{{animation:show-second 10.5s steps(1,end) infinite}}
@keyframes show-second{{0%{{visibility:hidden}}33.8095%,100%{{visibility:visible}}}}
.move-one{{animation:move-one 10.5s linear infinite}}
.move-two{{animation:move-two 10.5s linear infinite}}
@keyframes move-one{{0%{{transform:translateX(0)}}4.7619%{{transform:translateX(0);animation-timing-function:steps({len(lines[0])},end)}}33.8095%,100%{{transform:translateX({widths[0]}px)}}}}
@keyframes move-two{{0%{{transform:translateX(0)}}33.8095%{{transform:translateX(0);animation-timing-function:steps({len(lines[1])},end)}}61.9048%,100%{{transform:translateX({widths[1]}px)}}}}
.blink{{animation:blink .84s steps(1,end) infinite}}
@keyframes blink{{0%,100%{{opacity:1}}58%{{opacity:0}}}}
@media(prefers-reduced-motion:reduce){{.flame-frame,.reveal-one,.reveal-two,.cursor-one,.cursor-two,.move-one,.move-two,.blink{{animation:none!important}}.flame-frame{{visibility:hidden}}.frame-0{{visibility:visible}}.cursor-one,.cursor-two{{display:none}}}}
</style>
<g clip-path="url(#card)">
<rect width="900" height="344" fill="#10151e"/>
<g mask="url(#flame-opacity)">{''.join(images)}</g>
<path d="M0 56H900" stroke="#263041"/>
<circle cx="36" cy="29" r="5" fill="#ff7979"/><circle cx="54" cy="29" r="5" fill="#f3c96a"/><circle cx="72" cy="29" r="5" fill="#8bd5a3"/>
<text x="450" y="33" text-anchor="middle" font-size="11" fill="#7e8da5">~/mavisakalyan</text>
<path d="m41 126 8 10-8 10" fill="none" stroke="#85d9b2" stroke-width="4"/>
<text textLength="{widths[0]}" lengthAdjust="spacingAndGlyphs" clip-path="url(#line-one)" x="78" y="144" font-size="32" fill="#e4edf8">{lines[0]}</text>
<text textLength="{widths[1]}" lengthAdjust="spacingAndGlyphs" clip-path="url(#line-two)" x="78" y="194" font-size="32" fill="#e4edf8">{lines[1]}</text>
<g class="cursor-one"><g class="move-one"><rect class="blink" x="82" y="121" width="12" height="31" fill="#85d9b2"/></g></g>
<g class="cursor-two"><g class="move-two"><rect class="blink" x="82" y="171" width="12" height="31" fill="#85d9b2"/></g></g>
<text x="39" y="311" font-size="11" fill="#62758f">Edmond Burke</text>
</g>
<rect x=".5" y=".5" width="899" height="343" rx="18" fill="none" stroke="#30363d"/>
</svg>'''
ET.fromstring(svg)
output=ROOT/'assets/quote-terminal.svg'
output.write_text(svg)
print(f'Generated final SVG: {output.stat().st_size:,} bytes, {count} looping flame frames, looping typing.')
