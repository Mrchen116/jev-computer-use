"""Agent-authored adapter for CrazyGames Tower Defense Clash; real pointer input.

Open the game manually to level 1 or its restart screen before running. The reader
only inspects current engine state; Jev chooses complete build actions and timing.
"""
import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'skills/jev-computer-use/scripts'))
from jev_computer_use.models import JevClient

URL = 'https://www.crazygames.com/game/tower-defense-clash'
FRAME = '/tower-defense-clash/1/'
GUIDANCE = '''Build defenses aggressively when gold permits; wait only when no
affordable useful build remains. Build about six towers early instead of saving
starting gold behind one tower. Castle is near (740,200): ensure coverage near
that endpoint, and spread other towers along the enemy path. Start with multiple
archer towers, then stone for groups or ice for slow. Each build action is COMPLETE:
it opens the site menu, selects the tower and confirms. You choose tower type and
position. Follow the current tutorial first. Do not call later waves early until
defenses are ready. If health drops and this strategy cannot defend, request help.
Coordinates are in game units.'''
EXECUTE = '''async(page)=>{
 const a=ACTION, f=page.frames().find(f=>f.url().includes(FRAME));
 async function click(p){
  const b=await f.locator('canvas').boundingBox();
  const size=await f.evaluate(()=>({w:game.width,h:game.height}));
  const x=b.x+p.x/size.w*b.width,y=b.y+p.y/size.h*b.height;
  await page.mouse.move(x,y);await page.waitForTimeout(150);
  await page.mouse.click(x,y,{delay:150});
 }
 const before=await f.evaluate(()=>SceneGame.instance.levelTowers.length);
 await click(a); await page.waitForTimeout(400);
 if(a.kind==='build'){
  async function point(){return await f.evaluate(type=>{
   const n=btnGameBuildAction.find(b=>b.visible&&b.params?.type===type&&b.params?.action==='build');
   if(!n)return null;const b=n.getBounds();return{x:b.centerX,y:b.centerY};
  },a.type);}
  let p=await point();
  if(!p)return {outcome:'menu_not_open'};
  await click(p);await page.waitForTimeout(400);
  if(await f.evaluate(()=>SceneGame.instance.levelTowers.length)===before){
   p=await point();if(p){await click(p);await page.waitForTimeout(200);}
  }
 }
 return {before,after:await f.evaluate(()=>SceneGame.instance.levelTowers.length)};
}'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', required=True, help='Installed playwright-cli executable (avoid npx per cycle).')
    parser.add_argument('--session', default='jev-clash')
    parser.add_argument('--key-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--period', type=float, default=2)
    parser.add_argument('--seconds', type=float, default=360)
    parser.add_argument('--start-point', nargs=2, type=float, help='Observed start control center in game coordinates; clicked after recording begins.')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    os.chmod(args.output, 0o700)
    reader = Path(__file__).with_name('clash-observe.js').read_text()

    def cli(*words):
        p = subprocess.run([args.cli, '-s='+args.session, *words], capture_output=True, text=True, timeout=60)
        if p.returncode or '### Error' in p.stdout:
            raise RuntimeError(p.stdout+p.stderr)
        return p.stdout

    def observe():
        return json.loads(cli('run-code', 'async(page)=>{const f=page.frames().find(f=>f.url().includes('+json.dumps(FRAME)+'));return await f.evaluate('+reader+');}', '--raw'))

    def status(data):
        temporary = args.output/'progress.tmp'
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        temporary.replace(args.output/'progress.json')

    history, timings = [], []
    client = JevClient(args.key_file.read_text().strip())
    reason, error, final = 'budget', None, None
    started = time.monotonic()
    cli('video-start', str(args.output/'game.webm'), '--size=1280x900')
    try:
        if args.start_point:
            # Host-selected level setup is recorded; it does not select defenses.
            cli('run-code', EXECUTE.replace('ACTION', json.dumps(dict(zip(('x','y'), args.start_point)))).replace('FRAME', json.dumps(FRAME)), '--raw')
            cli('run-code', 'async(page)=>{await page.waitForTimeout(800);}')
        final = observe()
        if final['observation']['life'] <= 0 or not final['observation']['wave']:
            raise RuntimeError('Level not ready; return to host for setup')
        while time.monotonic()-started < args.seconds and len(history)<180:
            tick = time.monotonic()
            state = observe()
            before_observe_seconds = time.monotonic()-tick
            current = state['observation']
            if current['completed'] or current['failed']:
                reason = 'won' if current['completed'] else 'lost'; break
            if current['paused'] or not current['visible'] or current['fastForward']:
                reason = 'interface_not_running_normally'; break
            if (args.output/'STOP').exists():
                reason = 'host_stop'; break
            menu = dict(state['choices'])
            menu.update(wait={'label':'Wait only when no affordable useful construction remains.'},
                        help={'label':'Yield to host: strategy or available actions need revision.'})
            payload = {'model':'jev-latest','state':{'task':'Win the first level with full castle health.',
                'guidance':GUIDANCE,'observation':current,'history':list(history),'warnings':[]},
                'questions':{'action':{'type':'choice','instructions':['Choose one offered action now; follow the current tutorial if present.'],
                                      'criteria':{k:v['label'] for k,v in menu.items()}}}}
            answer, jev_seconds = client.ask(payload)
            selected = answer['answers']['action']['choice']
            if selected == 'help': reason = 'help'; break
            if (args.output/'STOP').exists(): reason = 'host_stop'; break
            execution_start = time.monotonic()
            result = None
            if selected != 'wait':
                code = EXECUTE.replace('ACTION', json.dumps(menu[selected])).replace('FRAME', json.dumps(FRAME))
                result = json.loads(cli('run-code', code, '--raw'))
            execute_seconds = time.monotonic()-execution_start
            observe_start = time.monotonic()
            final = observe()
            after = final['observation']
            if selected == 'wait': outcome = 'waited'
            elif menu[selected].get('kind') == 'build':
                outcome = 'succeeded' if len(after['towers'])>len(current['towers']) else 'not_built'
            elif selected == 'tutorial_target':
                outcome = 'succeeded' if after['tutorial'] != current['tutorial'] else 'not_advanced'
            else: outcome = 'attempted'
            cycle = time.monotonic()-tick
            timing = {'jev_s':jev_seconds,'execute_s':execute_seconds,
                      'observe_s':before_observe_seconds,'verify_s':time.monotonic()-observe_start,'cycle_s':cycle}
            timings.append(timing)
            history.append({'step':len(history)+1,'action':menu[selected]['label'],'outcome':outcome})
            warnings = ['cycle_overrun'] if cycle>args.period else []
            with (args.output/'history.jsonl').open('a') as f:
                f.write(json.dumps({'request':payload,'response':answer,'execution':result,'after':after,'timing':timing,'outcome':outcome})+'\n')
            progress = {'phase':'playing','step':len(history),'life':after['life'],'wave':after['wave'],
                        'towers':len(after['towers']),'history':history,'warnings':warnings,'usage':client.usage,
                        'history_location':str(args.output/'history.jsonl')}
            status(progress)
            print(json.dumps({k:v for k,v in progress.items() if k not in ('history','history_location')}),flush=True)
            if len(history)>=3 and all(h['outcome'] in ('not_built','not_advanced') for h in history[-3:]):
                reason='execution_not_progressing'; break
            if cycle<args.period: time.sleep(args.period-cycle)
        cli('screenshot')
    except Exception as exc:
        reason, error = 'error', str(exc)
    finally:
        seconds = time.monotonic()-started
        client.close()
        try: cli('video-stop')
        except Exception as exc: error = (error or '')+'; video-stop: '+str(exc)
        summary = {'reason':reason,'error':error,'seconds':seconds,'final':final,'calls':client.calls,
                   'usage':client.usage,'history':history,
                   'timing_mean':{k:statistics.mean(t[k] for t in timings) for k in timings[0]} if timings else {}}
        (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
        status({**summary,'phase':'yielded','history_location':str(args.output/'history.jsonl'),
                'takeover':{'session':args.session,'url':URL}})
        print(json.dumps({k:v for k,v in summary.items() if k not in ('history','final')},indent=2),flush=True)
    if error: raise SystemExit(1)


if __name__ == '__main__':
    main()
