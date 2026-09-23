() => {
 const g=SceneGame.instance, choices={}, texts=[];
 const pos=n=>({x:+n.worldPosition.x.toFixed(1),y:+n.worldPosition.y.toFixed(1)});
 function walk(n){
  if(!n.visible||n.worldVisible===false||n.worldAlpha<=0) return;
  if(typeof n.text==='string') texts.push(n.text);
  for(const c of n.children||[]) walk(c);
 }
 walk(game.world);
 function choice(id,n,label){
  if(!n||!n.visible||n.worldVisible===false||n.worldAlpha<=0||!n.inputEnabled)return;
  const b=n.getBounds(); if(b.centerX<0||b.centerX>game.width||b.centerY<0||b.centerY>game.height)return;
  choices[id]={label,x:b.centerX,y:b.centerY};
 }
 (g.levelBuildSpots||[]).forEach((n,i)=>{
  if(!n.visible||!n.worldVisible||n.worldAlpha<=0||!n.inputEnabled)return;
  const b=n.getBounds();
  for(const type of ['archer','stone','ice','lightning']){
   const price=getTowerParam(1,type,'price');if(playerMoney<price)continue;
   choices['build_'+i+'_'+type]={label:'Build '+type+' tower at ('+Math.round(b.centerX)+','+Math.round(b.centerY)+') for '+price+' gold. Includes opening menu and confirmation.',x:b.centerX,y:b.centerY,kind:'build',type};
  }
 });
 g.levelWaveIndicators.forEach((b,i)=>choice('wave_'+i,b,'Call next enemy wave early'));
 const tt=g.tutorialSteps?.[0];
 if(tt?.target?.worldTransform){const b=tt.target.getBounds();choices.tutorial_target={label:'Follow visible tutorial: '+txtGameTutorialText.text,x:b.centerX,y:b.centerY};}
 const simple=o=>Object.fromEntries(Object.entries(o||{}).filter(([k,v])=>['number','string','boolean'].includes(typeof v)&&!['type','physicsType','rotation','alpha','renderOrderID','TMP','tint','cachedTint','blendMode','z'].includes(k)&&!k.startsWith('_')));
 return {observation:{visible:!document.hidden,money:playerMoney,life:playerLife,wave:txtGameWaveVal.text,running:gameRunning,paused:gamePaused,fastForward:g.fastForward,
 texts,tutorial:tt?{type:tt.type,text:txtGameTutorialText.text}:null,
 enemies:g.levelEnemies.filter(e=>e.visible&&e.exists&&e.life>0).map(e=>({kind:e.enemy,life:e.life,...pos(e)})),
 towers:g.levelTowers.map((t,i)=>({i,kind:t.type,...pos(t.grpTower),stats:simple(t)})),
 completed:grpSceneLevelCompleted.visible&&grpSceneLevelCompleted.alpha>0.9,
 failed:grpSceneLevelFailed.visible&&grpSceneLevelFailed.alpha>0.9},choices,width:game.width,height:game.height};
}
