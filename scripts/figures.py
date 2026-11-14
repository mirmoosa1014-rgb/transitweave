"""Generate figures exclusively from committed benchmark data."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

ROOT=Path(__file__).resolve().parents[1]
result=json.loads((ROOT/'results/benchmark.json').read_text());rows=result['rows'];config=result['config']
BG='#071E36';INK='#E5F6FF';DIM='#8FB4C9';CYAN='#7FDBFF';GOLD='#F2C14E';RED='#FF8A7A'
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':BG,'savefig.facecolor':BG,'text.color':INK,'axes.labelcolor':DIM,'xtick.color':DIM,'ytick.color':DIM,'axes.edgecolor':DIM,'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'grid.color':DIM,'grid.alpha':.15})
colors={'raw':GOLD,'detrended':CYAN};families=['quiet','variable','gapped'];depths=[600,1200,2400]
fig,axs=plt.subplots(2,3,figsize=(16,10),layout='constrained')
fig.suptitle('TRANSITWEAVE  /  INJECTION–RECOVERY RECORD\n216 held-out signals · 120 null controls · identical observations for both methods',fontsize=18,x=.03,ha='left')
cmap=LinearSegmentedColormap.from_list('blueprint',[BG,'#3AA7CC',CYAN])
for ax,method,letter in zip(axs[0,:2],['raw','detrended'],['A','B']):
 values=np.array([[100*np.mean([r['recovered'] for r in rows if r['split']=='test' and r['method']==method and r['family']==f and r['depth_ppm']==d]) for d in depths] for f in families])
 im=ax.imshow(values,vmin=0,vmax=100,cmap=cmap,aspect='auto')
 for i in range(3):
  for j in range(3):ax.text(j,i,f'{values[i,j]:.0f}%',ha='center',va='center',color=BG if values[i,j]>55 else INK,fontweight='bold',fontsize=17)
 ax.set_xticks(range(3),depths);ax.set_yticks(range(3),families);ax.set_xlabel('Injected depth · ppm (24 scenarios per cell)');ax.set_title(f'{letter}  /  {method.upper()} · recovered fundamental',loc='left',pad=16)
fig.colorbar(im,ax=list(axs[0,:2]),shrink=.6,label='Recovered above threshold · %')
ax=axs[0,2]
for mi,method in enumerate(['raw','detrended']):
 for fi,family in enumerate(families):
  vals=np.array([r['score']/config['thresholds'][method] for r in rows if r['split']=='null_test' and r['method']==method and r['family']==family]);x=fi*3+mi
  ax.scatter(x+np.linspace(-.2,.2,len(vals)),vals,s=13,color=colors[method],alpha=.65,label=method if fi==0 else None)
ax.axhline(1,color=RED,ls='--',lw=1.3,label='alarm threshold');ax.set_xticks([.5,3.5,6.5],families);ax.set_ylabel('Null score / method threshold');ax.set_title('C  /  FALSE ALARMS REMAIN',loc='left',pad=16);ax.legend(frameon=False,fontsize=9);ax.grid(axis='y')
ax=axs[1,0];tuning=config['tuning'];windows=[str(x['window_days']) for x in tuning];v=[100*x['recovery_rate'] for x in tuning]
ax.bar(windows,v,color=[CYAN if x['window_days']==config['selected_window_days'] else DIM for x in tuning],width=.5)
for i,value in enumerate(v):ax.text(i,value+2,f"{tuning[i]['recovered']}/108",ha='center',color=INK)
ax.set_ylim(0,85);ax.set_ylabel('Validation recovery · %');ax.set_xlabel('Rolling-median window · days');ax.set_title('D  /  CHOOSE BEFORE TESTING',loc='left',pad=16);ax.grid(axis='y')
ax=axs[1,1];seeds=config['seeds']['test']
for fi,family in enumerate(families):
 diffs=[]
 for seed in seeds:
  rates={m:np.mean([r['recovered'] for r in rows if r['split']=='test' and r['method']==m and r['family']==family and r['seed']==seed]) for m in colors}
  diffs.append(100*(rates['detrended']-rates['raw']))
 ax.scatter(fi+np.linspace(-.2,.2,len(diffs)),diffs,s=24,color=CYAN,alpha=.65)
 ax.plot([fi-.3,fi+.3],[np.mean(diffs)]*2,color=GOLD,lw=3)
ax.axhline(0,color=DIM,lw=1);ax.set_xticks(range(3),families);ax.set_ylabel('Recovery difference · percentage points');ax.set_title('E  /  PAIRED SEED DIFFERENCES',loc='left',pad=16);ax.text(.02,.02,'Dots: 24 seeds · gold: mean\nEach seed averages three depths',transform=ax.transAxes,fontsize=9,color=DIM);ax.set_ylim(-40,110);ax.grid(axis='y')
ax=axs[1,2]
rng=np.random.default_rng(77);bootstrap=rng.integers(0,len(seeds),(2000,len(seeds)))
for method in colors:
 means=[];low=[];high=[]
 for depth in depths:
  seed_rates=np.array([np.mean([r['recovered'] for r in rows if r['split']=='test' and r['method']==method and r['depth_ppm']==depth and r['seed']==s]) for s in seeds])
  means.append(seed_rates.mean()*100);interval=np.quantile(seed_rates[bootstrap].mean(axis=1),[.025,.975])*100;low.append(interval[0]);high.append(interval[1])
 ax.plot(depths,means,'o-',color=colors[method],label=method);ax.fill_between(depths,low,high,color=colors[method],alpha=.14)
ax.set_ylim(0,105);ax.set_xticks(depths);ax.set_xlabel('Injected depth · ppm');ax.set_ylabel('Held-out recovery · %');ax.set_title('F  /  FAINT SIGNALS ARE HARDER',loc='left',pad=16);ax.legend(frameon=False);ax.grid(axis='y')
fig.text(.03,-.025,'Synthetic data only. Recovery = score above independent null threshold AND period within 2% of the injected fundamental.\nPanel F bands: 95% percentile bootstrap, resampling entire seeds (2,000 replicates); no real-survey performance claim.',color=DIM,fontsize=10)
fig.savefig(ROOT/'docs/images/research.png',dpi=160,bbox_inches='tight');plt.close(fig)
# A separate diagnostic plate for the saved default case.
demo=next(d for d in json.loads((ROOT/'results/demos.json').read_text()) if d['truth']['family']=='variable' and d['truth']['depth_ppm']==1200)
t=np.array(demo['time']);raw=(np.array(demo['flux'])-1)*1e6
fig,axs=plt.subplots(3,1,figsize=(14,9),layout='constrained');fig.suptitle('ONE STAR, TWO SEARCHES / seed 3001 · synthetic variable star',fontsize=18,ha='left',x=.03)
ax=axs[0];ax.scatter(t,raw,s=5,color=CYAN,alpha=.6,label='observations');ax.plot(t,(np.array(demo['methods']['detrended']['trend'])-1)*1e6,color=GOLD,lw=1.4,label='1.2-day rolling median');ax.set_ylabel('Relative flux · ppm');ax.set_xlabel('Elapsed days');ax.legend(frameon=False,ncol=2);ax.grid()
for ax,method in zip(axs[1:],['raw','detrended']):
 f=demo['methods'][method];ax.plot(f['periods'],f['scores'],color=colors[method],lw=1.4,label=method);ax.axhline(config['thresholds'][method],color=RED,ls='--',label='null-calibrated threshold');ax.axvline(demo['truth']['period_days'],color=INK,ls=':',label='injected period (evaluation only)');ax.set_xlabel('Trial period · days');ax.set_ylabel('Box-search score');ax.legend(frameon=False,ncol=3);ax.grid();ax.set_title(f"{method.title()}: strongest trial {f['period_days']:.3f} days, score {f['score']:.2f}",loc='left',fontsize=11)
fig.savefig(ROOT/'docs/images/signal.png',dpi=150,bbox_inches='tight');plt.close(fig)
