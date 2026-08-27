from pathlib import Path

root = Path('.')

app = root / 'app/nexora-app.tsx'
text = app.read_text(encoding='utf-8')
if 'const KLYVRO_BUILD = "0.4.6";' not in text:
    raise SystemExit('Klyvro v0.4.7: build marker 0.4.6 not found')
app.write_text(text.replace('const KLYVRO_BUILD = "0.4.6";', 'const KLYVRO_BUILD = "0.4.7";', 1), encoding='utf-8')

package = root / 'package.json'
text = package.read_text(encoding='utf-8')
if '"version": "0.4.6"' not in text:
    raise SystemExit('Klyvro v0.4.7: package version 0.4.6 not found')
package.write_text(text.replace('"version": "0.4.6"', '"version": "0.4.7"', 1), encoding='utf-8')

css = root / 'app/features.css'
text = css.read_text(encoding='utf-8')
marker = '/* Klyvro v0.4.7 real screen sharing */'
if marker not in text:
    text += '''\n\n/* Klyvro v0.4.7 real screen sharing */\n.screen-grid{width:100%;height:100%;min-width:0;min-height:0;padding:12px;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(340px,100%),1fr));grid-auto-rows:minmax(230px,1fr);gap:10px;overflow:auto;background:#0b0e13}.screen-grid .screen-card{min-height:230px;margin:0;border:1px solid rgba(255,255,255,.08);box-shadow:0 14px 40px rgba(0,0,0,.22)}.screen-card.remote{border-color:rgba(99,214,255,.16)}.screen-card.local{border-color:rgba(169,255,104,.18)}.screen-control.active{border-color:rgba(169,255,104,.32);background:rgba(169,255,104,.13)}.screen-control:disabled,.join-voice:disabled,.empty-voice-slot:disabled{opacity:.48;cursor:not-allowed}.voice-stage.sharing>.voice-people{border-left:1px solid var(--line)}\n@media(max-width:650px){.screen-grid{grid-template-columns:1fr;grid-auto-rows:minmax(220px,auto);padding:8px}.voice-stage.sharing>.voice-people{border-left:0}.screen-grid .screen-card{min-height:220px}}\n'''
    css.write_text(text, encoding='utf-8')

print('Klyvro v0.4.7 call/screen-share patch applied')
