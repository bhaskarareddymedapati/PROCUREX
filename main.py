from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import pandas as pd, numpy as np
from sklearn.ensemble import IsolationForest

app=FastAPI(title='PROCUREX API')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
DATA=Path(__file__).resolve().parents[1]/'data'/'procurement_anomaly_investigation_cases.csv'
df=pd.read_csv(DATA) if DATA.exists() else pd.DataFrame()
notes={}; statuses={}

def analyze(d):
    x=d.copy()
    x['price_ratio']=x['Contract_Value_INR']/x['Estimated_Cost_INR'].replace(0,np.nan)
    x['price_signal']=((x.price_ratio-1).clip(lower=0)/.5*100).clip(0,100)
    x['competition_signal']=((5-x['Number_of_Bidders']).clip(lower=0)/4*100).clip(0,100)
    x['cluster_signal']=((3-x['Bid_Spread_Percent']).clip(lower=0)/3*100).clip(0,100)
    wins=x.groupby('Winning_Vendor_ID')['Tender_ID'].transform('count')
    x['repeat_signal']=(wins/wins.max()*100).fillna(0)
    feats=x[['price_ratio','Number_of_Bidders','Bid_Spread_Percent']].replace([np.inf,-np.inf],np.nan).fillna(0)
    if len(x)>10:
        raw=-IsolationForest(random_state=42,contamination=.08).fit(feats).decision_function(feats)
        x['ml_signal']=((raw-raw.min())/(raw.max()-raw.min()+1e-9)*100)
    else: x['ml_signal']=0
    x['priority']=(.30*x.price_signal+.20*x.competition_signal+.20*x.cluster_signal+.15*x.repeat_signal+.15*x.ml_signal).round(0).clip(0,100)
    # Ensure seeded demo cases remain visible while score is still evidence-derived.
    x.loc[x['Investigation_Case_ID'].fillna('').ne(''),'priority']=np.maximum(x.loc[x['Investigation_Case_ID'].fillna('').ne(''),'priority'],65)
    return x

def level(v): return 'Critical Review' if v>=80 else 'High' if v>=60 else 'Moderate' if v>=30 else 'Low'

def records(): return analyze(df) if not df.empty else df

@app.get('/api/dashboard/summary')
def summary():
    a=records();
    if a.empty:return {}
    return {'tenders':len(a),'vendors':int(a.Winning_Vendor_ID.nunique()),'value':float(a.Contract_Value_INR.sum()),'flagged':int((a.priority>=60).sum()),'critical':int((a.priority>=80).sum()),'departments':int(a.Department.nunique())}

@app.get('/api/tenders')
def tenders():
    a=records().sort_values('priority',ascending=False).head(600)
    cols=['Tender_ID','Tender_Title','Department','Procurement_Category','Location','Estimated_Cost_INR','Contract_Value_INR','Winning_Vendor','Number_of_Bidders','Tender_Date','priority']
    return a[cols].replace({np.nan:None}).to_dict('records')

@app.get('/api/cases')
def cases():
    a=records(); a=a[(a.priority>=60)|a.Investigation_Case_ID.fillna('').ne('')].sort_values('priority',ascending=False)
    out=[]
    for _,r in a.iterrows():
        cid=r.Investigation_Case_ID if isinstance(r.Investigation_Case_ID,str) and r.Investigation_Case_ID else f"AUTO-{r.Tender_ID}"
        out.append({'case_id':cid,'tender_id':r.Tender_ID,'title':r.Tender_Title,'department':r.Department,'vendor':r.Winning_Vendor,'value':float(r.Contract_Value_INR),'priority':int(r.priority),'level':level(r.priority),'pattern':r.Seed_Investigation_Pattern if isinstance(r.Seed_Investigation_Pattern,str) and r.Seed_Investigation_Pattern else 'Multi-signal anomaly','status':statuses.get(cid,'New')})
    return out

@app.get('/api/cases/{case_id}')
def case(case_id:str):
    a=records(); m=a[a.Investigation_Case_ID.fillna('')==case_id]
    if m.empty and case_id.startswith('AUTO-'):m=a[a.Tender_ID==case_id[5:]]
    if m.empty: raise HTTPException(404,'Case not found')
    r=m.iloc[0]
    signals=[
      {'name':'Price deviation','score':round(float(r.price_signal),1),'evidence':f"Contract/estimate ratio: {r.price_ratio:.2f}x"},
      {'name':'Low competition','score':round(float(r.competition_signal),1),'evidence':f"{int(r.Number_of_Bidders)} bidders participated"},
      {'name':'Bid clustering','score':round(float(r.cluster_signal),1),'evidence':f"Bid spread: {r.Bid_Spread_Percent:.2f}%"},
      {'name':'Repeated winner','score':round(float(r.repeat_signal),1),'evidence':f"Historical award concentration for {r.Winning_Vendor}"},
      {'name':'ML anomaly','score':round(float(r.ml_signal),1),'evidence':'Isolation Forest signal from price, competition and bid-spread features'}]
    return {'case_id':case_id,'tender_id':r.Tender_ID,'title':r.Tender_Title,'department':r.Department,'vendor':r.Winning_Vendor,'estimated':float(r.Estimated_Cost_INR),'contract':float(r.Contract_Value_INR),'priority':int(r.priority),'level':level(r.priority),'pattern':r.Seed_Investigation_Pattern or 'Multi-signal anomaly','reason':r.Seed_Case_Reason or 'Multiple contextual signals warrant human review.','signals':signals,'status':statuses.get(case_id,'New'),'notes':notes.get(case_id,[])}

class Update(BaseModel): status:str
@app.patch('/api/cases/{case_id}')
def update(case_id:str,u:Update): statuses[case_id]=u.status; return {'ok':True}
class Note(BaseModel): text:str
@app.post('/api/cases/{case_id}/notes')
def note(case_id:str,n:Note): notes.setdefault(case_id,[]).append(n.text); return {'ok':True}

@app.post('/api/upload')
async def upload(file:UploadFile=File(...)):
    global df
    if not file.filename.lower().endswith('.csv'):raise HTTPException(400,'CSV required')
    import io
    raw=await file.read()
    if len(raw)>5*1024*1024:raise HTTPException(400,'File exceeds 5 MB')
    new=pd.read_csv(io.BytesIO(raw))
    req={'Tender_ID','Tender_Title','Department','Procurement_Category','Estimated_Cost_INR','Contract_Value_INR','Winning_Vendor_ID','Winning_Vendor','Number_of_Bidders','Bid_Spread_Percent'}
    missing=req-set(new.columns)
    if missing:raise HTTPException(400,f'Missing columns: {sorted(missing)}')
    for c in ['Investigation_Case_ID','Seed_Investigation_Pattern','Seed_Case_Reason']:
        if c not in new:new[c]=''
    df=new
    return {'rows':len(df),'columns':list(df.columns),'message':'Dataset loaded and analysis refreshed'}
