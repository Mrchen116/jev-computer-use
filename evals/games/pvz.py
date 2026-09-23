"""Agent-authored Garden Defenders adapter; game state is read-only, input is real UI.

Requires an open playwright-cli session on https://seth-xh.github.io/pvz/.
No generic runner extension is implied. See README.md beside this file.
"""
import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

SOURCE = Path(__file__).resolve().parents[2] / 'skills/jev-computer-use/scripts'
sys.path.insert(0, str(SOURCE))
from jev_computer_use.models import JevClient

OBSERVE = '''() => game && ({time:game.time,state:game.state,sun:game.sun,
wave:game.wave,kills:game.kills,usedMowers:game.usedMowers,planted:game.planted,
paused,speed,plants:game.plants.map(p=>({id:p.id,type:PLANTS[p.type].id,
row:p.row,col:p.col,hp:Math.round(p.hp)})),
zombies:game.zombies.map(z=>({id:z.id,type:z.type,row:z.row,
col:+((z.x-FIELD.x)/FIELD.cw-.5).toFixed(2),hp:Math.round(z.hp),eating:z.eating})),
suns:game.suns.map(s=>({id:s.id,value:s.value})),
cooldowns:game.cooldowns,catalog:PLANTS.map(p=>({id:p.id,cost:p.cost})),
visible:!document.hidden})'''
GUIDANCE = '''Win all three waves with THREE STARS: no mower use. Zombies move from
column 9 toward the house at column -1; shooters only fire rightward in their row.
Develop about 5 sunflowers early in rear columns 0-1, distributed across rows.
Priority: defend an attacked row lacking a shooter before adding more economy;
then increase economy while safe; reinforce rows under heavy attack. One pea can
handle a lone normal zombie if placed early. Plant shooters at col 2-3 before
zombies pass them. Do not duplicate shooters in a safe row while another attacked
row has none. Use a wall ahead of shooters to buy time; cherry blast reaches 1.75
columns and adjacent rows, so place it NEAR enemies, never far behind them.
Plant actions collect visible suns first, so separate collection is unnecessary
when you can make a useful planting. Wait is valid during cooldowns. Choose ONE
complete offered action; do not try to coordinate separate answers.'''


def view(state):
    """Normalize coordinates and group facts, without ranking or choosing actions."""
    result = {k: v for k, v in state.items() if k not in ('plants','zombies','cooldowns','catalog')}
    result['rows'] = [{'row':r,'plants':[p for p in state['plants'] if p['row']==r],
                       'enemies':[z for z in state['zombies'] if z['row']==r]}
                      for r in range(5)]
    result['seeds'] = [{'name':p['id'],'cost':p['cost'],'cooldown_seconds':round(state['cooldowns'][i],1)}
                       for i,p in enumerate(state['catalog'])]
    return result


def actions(state):
    # Host's simple loadout and placement zones keep whole actions below 255.
    # Within these zones Jev, not code, chooses the row, plant and timing.
    zones = {0:range(2),1:range(2,4),2:range(4,6),4:range(9)}
    menu = {'wait':{'label':'Wait; do not spend resources.'},
            'help':{'label':'Yield to host: this action set or strategy needs revision.'}}
    if state['suns']:
        menu['collect'] = {'label':'Collect all visible sun; do not plant.'}
    available = state['sun'] + sum(s['value'] for s in state['suns'])
    occupied = {(p['row'],p['col']) for p in state['plants']}
    for t, cols in zones.items():
        plant = state['catalog'][t]
        if available < plant['cost'] or state['cooldowns'][t] > 0:
            continue
        for r in range(5):
            for c in cols:
                if (r,c) not in occupied:
                    menu[f'p_{t}_{r}_{c}'] = {'label':f'Collect sun, then plant {plant["id"]} at row {r}, col {c}; cost {plant["cost"]}.',
                                             'type':t,'row':r,'col':c,'name':plant['id']}
    return menu


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli',required=True)
    parser.add_argument('--session',default='jev-pvz')
    parser.add_argument('--key-file',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--period',type=float,default=2)
    parser.add_argument('--seconds',type=float,default=240)
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    os.chmod(args.output,0o700)
    def cli(*words):
        p = subprocess.run([args.cli,'-s='+args.session,*words],text=True,capture_output=True,timeout=60)
        if p.returncode or '### Error' in p.stdout:
            raise RuntimeError(p.stdout+p.stderr)
        return p.stdout
    def observe():
        return json.loads(cli('eval',OBSERVE,'--raw'))
    def save_status(status):
        temporary=args.output/'progress.tmp'
        temporary.write_text(json.dumps(status,ensure_ascii=False,indent=2))
        temporary.replace(args.output/'progress.json')
    client = JevClient(args.key_file.read_text().strip())
    history, timings = [], []
    reason = 'budget'
    cli('reload')
    cli('run-code',"async (page) => { await page.locator('#startBtn').waitFor({state:'visible'}); await page.locator('#garden').scrollIntoViewIfNeeded(); }")
    cli('video-start',str(args.output/'game.webm'),'--size=1280x900')
    started = time.monotonic()
    try:
        cli('run-code',"async (page) => { await page.locator('#startBtn').click(); await page.locator('#homeOverlay').waitFor({state:'hidden'}); }")
        while time.monotonic()-started < args.seconds and len(history)<150:
            tick=time.monotonic()
            state=observe()
            if state['state'] != 'playing':
                reason=state['state']; break
            if state['paused'] or not state['visible']:
                reason='interface_not_running'; break
            if (args.output/'STOP').exists():
                reason='host_stop'; break
            menu=actions(state)
            payload={'model':'jev-latest','state':{'task':'Win first adventure level with three stars and zero mower use.',
                'guidance':GUIDANCE,'observation':view(state),'history':history,'warnings':[]},
                'questions':{'next_action':{'type':'choice','instructions':['Choose one complete useful action now.'],
                            'criteria':{k:v['label'] for k,v in menu.items()}}}}
            observation_seconds=time.monotonic()-tick
            answer,jev_seconds=client.ask(payload)
            key=answer['answers']['next_action']['choice']; action=menu[key]
            if key=='help':
                reason='help'; break
            execute_started=time.monotonic()
            if key=='collect':
                cli('press','c')
            elif key.startswith('p_'):
                # Focus and scroll before keyboard input; collect removes sun click occlusion.
                # Recheck eligibility only; do not choose a substitute action silently.
                script='''async (page) => {
                  const a=ACTION;
                  await page.locator('#garden').scrollIntoViewIfNeeded();
                  await page.locator('#garden').focus();
                  await page.keyboard.press('c');
                  const legal=await page.evaluate(a => game.state==='playing' && !paused &&
                    !game.plants.some(p=>p.row===a.row && p.col===a.col) &&
                    game.sun>=PLANTS[a.type].cost && game.cooldowns[a.type]<=0,a);
                  if(!legal) return {executed:false};
                  const alreadySelected=await page.evaluate(t=>selected===t,a.type);
                  if(!alreadySelected) await page.keyboard.press(String(a.type+1));
                  const b=await page.locator('#garden').boundingBox();
                  await page.mouse.click(b.x+(238+(a.col+.5)*115)/1440*b.width,
                                         b.y+(149+(a.row+.78)*117)/810*b.height);
                  return {executed:true};
                }'''.replace('ACTION',json.dumps(action))
                cli('run-code',script)
            execute_seconds=time.monotonic()-execute_started
            after=observe()
            if key.startswith('p_'):
                outcome='succeeded' if after['planted']>state['planted'] else 'not_planted'
            elif key=='collect':
                outcome='succeeded' if not ({s['id'] for s in state['suns']} & {s['id'] for s in after['suns']}) else 'uncertain'
            else:
                outcome='waited'
            cycle=time.monotonic()-tick
            warnings=['cycle_overrun'] if cycle>args.period else []
            entry={'time':round(state['time'],1),'action':action['label'],'outcome':outcome}
            history.append(entry)
            timing={'observe_s':observation_seconds,'jev_s':jev_seconds,'execute_s':execute_seconds,
                    'verify_s':time.monotonic()-execute_started-execute_seconds,'cycle_s':cycle}
            timings.append(timing)
            with (args.output/'history.jsonl').open('a') as f:
                f.write(json.dumps({'request':payload,'response':answer,'after':after,'timing':timing,'outcome':outcome})+'\n')
            progress={'phase':'playing','step':len(history),'game_time':round(after['time'],1),
                      'wave':after['wave'],'kills':after['kills'],'mowers':after['usedMowers'],
                      'history':history,'warnings':warnings,'usage':client.usage,
                      'history_location':str(args.output/'history.jsonl')}
            save_status(progress)
            print(json.dumps({k:v for k,v in progress.items() if k not in ('history','history_location')}),flush=True)
            if cycle<args.period:
                time.sleep(args.period-cycle)
        final=observe()
        cli('screenshot')
        summary={'reason':reason,'final':final,'wall_seconds':time.monotonic()-started,
                 'calls':client.calls,'usage':client.usage,'history':history,
                 'timing_mean':{k:statistics.mean(t[k] for t in timings) for k in timings[0]} if timings else {}}
        (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
        save_status({**summary,'phase':'yielded','history_location':str(args.output/'history.jsonl'),
                     'takeover':{'session':args.session,'url':'https://seth-xh.github.io/pvz/'}})
        print(json.dumps({k:v for k,v in summary.items() if k not in ('history','final')},indent=2),flush=True)
    finally:
        client.close()
        cli('video-stop')

if __name__=='__main__':
    main()
