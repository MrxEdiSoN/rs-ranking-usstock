"""
RS Ranking — NASDAQ v14
安裝：pip install streamlit yfinance pandas requests plotly lxml html5lib
執行：streamlit run rs_ranking.py
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time
import sys
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

APP_DIR=Path(__file__).resolve().parent
DATA_DIR=APP_DIR/"data"
DATASET_OPTIONS={
    "全美精選": "quality",
    "全美上市": "us_all",
    "NASDAQ": "nasdaq",
}

st.set_page_config(page_title="RS Ranking — NASDAQ", page_icon="📈", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{background-color:#0a0a0f!important;color:#e0e0e0!important;font-family:'Inter',sans-serif;}
.stApp{background-color:#0a0a0f!important;}
.top-bar{display:flex;justify-content:space-between;align-items:center;padding:8px 0 16px 0;border-bottom:1px solid #1e1e2e;margin-bottom:16px;}
.top-title{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:#fff;}
.table-wrap{overflow-x:auto;overflow-y:auto;max-height:600px;border:1px solid #1e1e2e;border-radius:6px;}
.rs-table{width:100%;border-collapse:collapse;font-size:12px;}
.rs-table th{position:sticky;top:0;z-index:10;text-align:left;padding:8px 10px;background:#0f0f1a;color:#555;font-weight:600;border-bottom:2px solid #1e1e2e;font-size:11px;letter-spacing:0.5px;white-space:nowrap;}
.rs-table td{padding:7px 10px;border-bottom:1px solid #111827;white-space:nowrap;vertical-align:middle;}
.rs-table tr:hover td{background:#0f172a;}
.ticker-tag{font-family:'JetBrains Mono',monospace;font-weight:700;color:#60a5fa;font-size:13px;}
.sepa-badge{background:#f59e0b22;border:1px solid #f59e0b;color:#f59e0b;padding:1px 5px;border-radius:3px;font-size:10px;margin-left:4px;}
.sp500-badge{background:#22c55e22;border:1px solid #22c55e;color:#22c55e;padding:1px 5px;border-radius:3px;font-size:10px;}
.ndx-badge{background:#3b82f622;border:1px solid #3b82f6;color:#3b82f6;padding:1px 5px;border-radius:3px;font-size:10px;margin-left:2px;}
.ath-badge{background:#f59e0b22;border:1px solid #f59e0b;color:#f59e0b;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:700;}
.w52-badge{background:#a78bfa22;border:1px solid #a78bfa;color:#a78bfa;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:700;}
.break-badge{background:#22c55e22;border:1px solid #22c55e;color:#22c55e;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;}
.retest-badge{background:#f59e0b22;border:1px solid #f59e0b;color:#f59e0b;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;}
.rs-bar-wrap{display:flex;align-items:center;gap:8px;}
.rs-bar-bg{background:#1e1e2e;border-radius:2px;height:6px;width:80px;}
.rs-bar-fill{height:6px;border-radius:2px;}
.pos{color:#22c55e;}.neg{color:#ef4444;}.neu{color:#888;}
.accel-sup{color:#f59e0b;font-size:9px;vertical-align:super;}
.tech-box{background:#0f172a;border:1px solid #1e293b;border-left:3px solid #00d4aa;padding:16px;border-radius:4px;font-size:12px;color:#aaa;line-height:1.9;margin-bottom:12px;}
.tech-box h4{color:#00d4aa;font-size:13px;margin:0 0 8px 0;letter-spacing:1px;}
.tech-box ul{margin:4px 0;padding-left:20px;}
.tech-box li{margin-bottom:4px;}
.stTextInput input{background:#1a1a2e!important;border:1px solid #2d2d4e!important;color:#e0e0e0!important;border-radius:4px!important;font-size:12px!important;}
div[data-testid="stSidebarContent"]{background:#0f0f1a!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 指數成份股
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400)
def get_index_members():
    sp500, ndx = set(), set()
    for attempt in range(2):
        try:
            kwargs = {"attrs":{"id":"constituents"}} if attempt==0 else {}
            tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",**kwargs)
            for t in tables:
                for col in t.columns:
                    if str(col).lower().strip() in ["symbol","ticker"]:
                        cands = t[col].dropna().astype(str).str.strip().str.replace(".","-",regex=False).tolist()
                        if len(cands)>=400: sp500=set(cands); break
                if sp500: break
        except: pass
        if sp500: break
    if len(sp500)<400:
        try:
            r=requests.get("https://slickcharts.com/sp500",headers={"User-Agent":"Mozilla/5.0"},timeout=10)
            for t in pd.read_html(r.text):
                for col in t.columns:
                    if str(col).lower() in ["symbol","ticker"]:
                        c=t[col].dropna().astype(str).str.strip().tolist()
                        if len(c)>=400: sp500=set(c); break
                if sp500: break
        except: pass
    if len(sp500)<400:
        sp500=set(["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","BRK-B","AVGO",
                   "JPM","LLY","UNH","V","XOM","MA","COST","HD","PG","WMT","JNJ","ABBV",
                   "BAC","MRK","ORCL","CRM","CVX","KO","PEP","AMD","ADBE","ACN","TMO","MCD",
                   "CSCO","WFC","ABT","NFLX","LIN","TXN","PM","DHR","INTU","INTC","IBM","GS",
                   "SPGI","AMGN","ISRG","GE","CAT","BKNG","SYK","NOW","VRTX","REGN","PLD",
                   "AXP","BLK","LRCX","KLAC","AMAT","MU","SNDK","WDC","STX","MRVL","ON"])
    try:
        tables=pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")
        for t in tables:
            for col in t.columns:
                if str(col).lower().strip() in ["ticker","symbol"]:
                    cands=t[col].dropna().astype(str).str.strip().str.replace(".","-",regex=False).tolist()
                    if len(cands)>=90: ndx=set(cands); break
            if ndx: break
    except: pass
    if len(ndx)<90:
        ndx=set(["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","COST",
                 "NFLX","AMD","ADBE","QCOM","INTC","INTU","CSCO","AMAT","MU","LRCX",
                 "PANW","KLAC","MRVL","SNPS","CDNS","ASML","ADI","MCHP","ON","FTNT",
                 "CRWD","DXCM","IDXX","ILMN","ISRG","REGN","VRTX","GILD","AMGN","BIIB",
                 "MRNA","BKNG","ABNB","EXPE","SBUX","MDLZ","PEP","ADP","PAYX","FAST",
                 "ODFL","CPRT","CSGP","VRSK","ANSS","CTSH","FISV","PYPL","ADSK",
                 "ZS","DDOG","TTD","WDAY","ROST","DLTR","WBA","KHC","MNST","CEG",
                 "EXC","XEL","FANG","PCAR","HON","GEHC","GFS","CDW","CCEP","SMCI",
                 "ARM","MSTR","SNDK"])
    return sp500, ndx

# ══════════════════════════════════════════════════════════════
# NASDAQ 清單
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400)
def get_nasdaq_tickers(universe="NASDAQ"):
    exchanges=["NASDAQ"] if universe=="NASDAQ" else ["NASDAQ","NYSE","AMEX"]
    headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Accept":"application/json"}
    frames=[]
    try:
        for exchange in exchanges:
            url=f"https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=10000&exchange={exchange}"
            r=requests.get(url,headers=headers,timeout=15)
            r.raise_for_status()
            rows=r.json()["data"]["table"]["rows"]
            part=pd.DataFrame(rows)
            if not part.empty:
                part["Exchange"]=exchange
                frames.append(part)
        if not frames:
            return pd.DataFrame()
        df=pd.concat(frames,ignore_index=True)
        col_map={}
        for c in df.columns:
            cl=c.lower()
            if cl=="symbol": col_map[c]="Ticker"
            elif cl=="name": col_map[c]="Name"
            elif "cap" in cl: col_map[c]="MarketCap"
            elif "sector" in cl: col_map[c]="Sector"
            elif "industry" in cl: col_map[c]="Industry"
            elif cl in ("ipoyear","ipo year"): col_map[c]="IPOYear"
        df=df.rename(columns=col_map)
        for col in ["Ticker","Name","MarketCap","Sector","Industry","IPOYear","Exchange"]:
            if col not in df.columns: df[col]="N/A"
        df=df[["Ticker","Name","MarketCap","Sector","Industry","IPOYear","Exchange"]]
        def parse_cap(v):
            if not v or str(v) in ("","N/A"): return None
            text=str(v).replace("$","").replace(",","").strip().upper()
            mult=1
            if text.endswith("T"): mult=1_000_000_000_000; text=text[:-1]
            elif text.endswith("B"): mult=1_000_000_000; text=text[:-1]
            elif text.endswith("M"): mult=1_000_000; text=text[:-1]
            try: return float(text)*mult
            except: return None
        df["MarketCapNum"]=df["MarketCap"].apply(parse_cap)
        df["Ticker"]=df["Ticker"].astype(str).str.upper().str.replace(".","-",regex=False)
        df=df.drop_duplicates("Ticker")
        return df
    except Exception as e:
        st.error(f"無法取得股票清單：{e}"); return pd.DataFrame()

def is_excluded_instrument(row,exclude_etf=True,exclude_warrant=True,exclude_unit=True,exclude_preferred=True,exclude_right=True):
    ticker=str(row.get("Ticker","")).upper()
    name=str(row.get("Name","")).upper()
    industry=str(row.get("Industry","")).upper()
    if exclude_etf and any(x in name or x in industry for x in ["ETF","FUND","TRUST","ETN"]):
        return True
    if exclude_warrant and (ticker.endswith(("W","WS","WT")) or "WARRANT" in name):
        return True
    if exclude_unit and (ticker.endswith("U") or " UNIT" in name or "UNITS" in name):
        return True
    if exclude_preferred and (ticker.endswith(("P","PR")) or "PREFERRED" in name or "DEPOSITARY" in name):
        return True
    if exclude_right and (ticker.endswith("R") or " RIGHT" in name or "RIGHTS" in name):
        return True
    return False

def get_sector_yf(ticker):
    try:
        info=yf.Ticker(ticker).info
        return info.get("sector") or info.get("sectorDisp") or "N/A"
    except: return "N/A"

# ══════════════════════════════════════════════════════════════
# 成長信號
# ══════════════════════════════════════════════════════════════
def growth_signal(values):
    signals=[]
    for i,v in enumerate(values):
        if v is None: signals.append("—"); continue
        if i==0: signals.append("✅" if v>0 else "❌" if v<0 else "—"); continue
        prev=values[i-1]
        if prev is not None and prev<0 and v>0: signals.append("🔄")
        elif v>0 and prev is not None and v>prev: signals.append("🚀")
        elif v>0 and prev is not None and prev>0 and v<prev: signals.append("↘️")
        elif v>0: signals.append("✅")
        else: signals.append("❌")
    return signals

def margin_signal(values):
    signals=[]
    for i,v in enumerate(values):
        if v is None: signals.append("—"); continue
        if i==0: signals.append("✅" if v>0 else "❌"); continue
        prev=values[i-1]
        if prev is None: signals.append("✅" if v>0 else "❌"); continue
        diff_now=v-prev
        diff_prev=(values[i-1]-values[i-2]) if i>=2 and values[i-2] is not None else None
        if diff_now>0 and diff_prev is not None and diff_now>diff_prev: signals.append("🚀")
        elif diff_now>0: signals.append("✅")
        elif diff_now<0 and v>0: signals.append("⚠️")
        elif diff_now<0: signals.append("❌")
        else: signals.append("—")
    return signals

def consecutive_accel(signals):
    count=0
    for s in reversed(signals):
        if s=="🚀": count+=1
        else: break
    return count

# ══════════════════════════════════════════════════════════════
# 基本面
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400)
def get_yf_financials(ticker):
    try:
        fin=yf.Ticker(ticker).quarterly_financials
        if fin is None or fin.empty: return None,None,None,None,[],{}
        fin=fin.sort_index(axis=1,ascending=False)
        cols=list(fin.columns)
        if len(cols)<2: return None,None,None,None,[],{}
        def get_row(keys):
            for k in keys:
                if k in fin.index: return fin.loc[k]
            return None
        rev_row=get_row(["Total Revenue","Revenue"])
        gp_row=get_row(["Gross Profit"])
        eps_row=get_row(["Basic EPS","Diluted EPS","Basic Earnings Per Share","Diluted Earnings Per Share"])
        ni_row=get_row(["Net Income","Net Income Common Stockholders"])
        bar_data=[]
        for i in range(min(5,len(cols)-1)):
            qname=str(cols[i])[:7]
            rev_qoq=None
            if rev_row is not None:
                rv0,rv1=rev_row.iloc[i],rev_row.iloc[i+1]
                if rv1 and rv1!=0: rev_qoq=round((rv0-rv1)/abs(rv1)*100,1)
            gm=None
            if gp_row is not None and rev_row is not None:
                gp0=gp_row.iloc[i]; rv0=rev_row.iloc[i]
                if rv0 and rv0!=0: gm=round(gp0/rv0*100,1)
            eps_qoq=None
            src=eps_row if eps_row is not None else ni_row
            if src is not None:
                e0,e1=src.iloc[i],src.iloc[i+1]
                if e1 and e1!=0: eps_qoq=round((e0-e1)/abs(e1)*100,1)
            ni_val=None; ni_qoq=None
            if ni_row is not None:
                n0=ni_row.iloc[i]
                if n0 is not None:
                    try: ni_val=round(float(n0)/1e6,1)
                    except: pass
                if i+1<len(cols):
                    n1=ni_row.iloc[i+1]
                    if n0 is not None and n1 is not None and n1!=0:
                        try: ni_qoq=round((float(n0)-float(n1))/abs(float(n1))*100,1)
                        except: pass
            bar_data.append({"quarter":qname,"eps_qoq":eps_qoq,"rev_qoq":rev_qoq,
                             "gross_margin":gm,"net_income":ni_val,"ni_qoq":ni_qoq})
        bar_data=list(reversed(bar_data))
        eps_sigs=growth_signal([d["eps_qoq"] for d in bar_data])
        rev_sigs=growth_signal([d["rev_qoq"] for d in bar_data])
        gm_sigs=margin_signal([d["gross_margin"] for d in bar_data])
        ni_sigs=growth_signal([d["ni_qoq"] for d in bar_data])
        for i,d in enumerate(bar_data):
            d["eps_sig"]=eps_sigs[i] if i<len(eps_sigs) else "—"
            d["rev_sig"]=rev_sigs[i] if i<len(rev_sigs) else "—"
            d["gm_sig"]=gm_sigs[i] if i<len(gm_sigs) else "—"
            d["ni_sig"]=ni_sigs[i] if i<len(ni_sigs) else "—"
        latest=bar_data[-1] if bar_data else {}
        sigs_dict={
            "eps_latest_sig":latest.get("eps_sig","—"),"rev_latest_sig":latest.get("rev_sig","—"),
            "gm_latest_sig":latest.get("gm_sig","—"),"ni_latest_sig":latest.get("ni_sig","—"),
            "eps_accel":consecutive_accel(eps_sigs),"rev_accel":consecutive_accel(rev_sigs),
            "gm_accel":consecutive_accel(gm_sigs),"ni_accel":consecutive_accel(ni_sigs),
        }
        return (latest.get("eps_qoq"),latest.get("rev_qoq"),
                latest.get("gross_margin"),latest.get("net_income"),bar_data,sigs_dict)
    except: return None,None,None,None,[],{}

@st.cache_data(ttl=86400)
def get_eps_records(ticker):
    records=[]
    try:
        fin=yf.Ticker(ticker).quarterly_financials
        if fin is None or fin.empty: return records
        fin=fin.sort_index(axis=1,ascending=False)
        eps_row=None
        for k in ["Basic EPS","Diluted EPS","Basic Earnings Per Share",
                  "Diluted Earnings Per Share","Net Income","Net Income Common Stockholders"]:
            if k in fin.index: eps_row=fin.loc[k]; break
        if eps_row is None: return records
        cols=list(eps_row.index)
        for i in range(min(6,len(cols)-1)):
            e0,e1=eps_row.iloc[i],eps_row.iloc[i+1]
            qoq=round((e0-e1)/abs(e1)*100,1) if e1 and e1!=0 else None
            if e1 is not None and e1<0 and e0 is not None and e0>0: sig="🔄"
            elif qoq and qoq>0:
                prev_qoq=None
                if i+2<len(cols):
                    ep=eps_row.iloc[i+1]; epp=eps_row.iloc[i+2]
                    if epp and epp!=0: prev_qoq=round((ep-epp)/abs(epp)*100,1)
                sig="🚀" if prev_qoq is not None and qoq>prev_qoq else "↘️" if prev_qoq is not None and prev_qoq>0 and qoq<prev_qoq else "✅"
            elif qoq and qoq<0: sig="❌"
            else: sig="—"
            records.append({"季度":str(cols[i])[:10],
                            "EPS":round(float(e0),4) if e0 else None,
                            "上季EPS":round(float(e1),4) if e1 else None,
                            "季增率":f"{qoq:+.1f}%" if qoq is not None else "—","信號":sig})
    except: pass
    return records

# ══════════════════════════════════════════════════════════════
# 技術指標
# ══════════════════════════════════════════════════════════════
def calc_rs(hist):
    try:
        c=hist["Close"].squeeze()
        if len(c)<60: return None
        p12=min(251,len(c)-1); p3=min(63,len(c)-1)
        return (c.iloc[-1]/c.iloc[-p12]-1)*0.6+(c.iloc[-1]/c.iloc[-p3]-1)*0.4
    except: return None

def calc_roc(hist,days):
    try:
        c=hist["Close"].squeeze()
        if len(c)<=days: return None
        return round((c.iloc[-1]/c.iloc[-days]-1)*100,2)
    except: return None

def calc_day_change(hist):
    try:
        c=hist["Close"].squeeze()
        if len(c)<2: return None
        return round((c.iloc[-1]/c.iloc[-2]-1)*100,2)
    except: return None

def calc_volume_ratio(hist):
    try:
        v=hist["Volume"].squeeze()
        if len(v)<21: return None
        today_vol=float(v.iloc[-1]); avg20=float(v.iloc[-21:-1].mean())
        if avg20==0: return None
        return round((today_vol/avg20-1)*100,1)
    except: return None

def check_sepa(hist):
    try:
        c=hist["Close"].squeeze()
        if len(c)<210: return False,{}
        ma50=c.rolling(50).mean().iloc[-1]; ma150=c.rolling(150).mean().iloc[-1]
        ma200=c.rolling(200).mean().iloc[-1]; ma200_1m=c.rolling(200).mean().iloc[-21]
        price=c.iloc[-1]; high52=c[-252:].max(); low52=c[-252:].min()
        conds={"股價>150MA>200MA":bool(price>ma150>ma200),"200MA上升趨勢":bool(ma200>ma200_1m),
               "股價>50MA":bool(price>ma50),"距低點≥30%":bool(price>=low52*1.30),
               "距高點≤25%":bool(price>=high52*0.75)}
        return all(conds.values()),conds
    except: return False,{}

def check_weekly_ma30(hist):
    try:
        c=hist["Close"].squeeze()
        c.index=pd.to_datetime(c.index)
        w=c.resample("W").last().dropna()
        if len(w)<31: return None
        return bool(w.iloc[-1]>w.rolling(30).mean().iloc[-1])
    except: return None

def check_weekly_ma30_status(hist):
    try:
        c=hist["Close"].squeeze(); lo=hist["Low"].squeeze()
        c.index=pd.to_datetime(c.index); lo.index=pd.to_datetime(lo.index)
        wc=c.resample("W").last().dropna(); wl=lo.resample("W").min().dropna()
        wc,wl=wc.align(wl,join="inner")
        if len(wc)<32: return "-",None
        ma30=wc.rolling(30).mean()
        if wc.iloc[-1]<=ma30.iloc[-1]: return "-",None
        n=len(wc); scan=min(52,n-2)
        breakout_i=None
        for event_i in range(n-1,n-scan-1,-1):
            prev_i=event_i-1
            if prev_i<0: break
            wc_cur=wc.iloc[event_i]; wc_prev=wc.iloc[prev_i]
            ma_cur=ma30.iloc[event_i]; ma_prev=ma30.iloc[prev_i]
            if wc_prev<=ma_prev and wc_cur>ma_cur:
                breakout_i=event_i
                break
        if breakout_i is None:
            return "超過52週",None

        breakout_weeks_ago=n-1-breakout_i
        if breakout_i < n-1 and breakout_i >= 2:
            pre_dip_i=breakout_i-2
            dip_i=breakout_i-1
            if wc.iloc[pre_dip_i] > ma30.iloc[pre_dip_i] and wc.iloc[dip_i] <= ma30.iloc[dip_i]:
                return "回測",breakout_weeks_ago

        def first_swing_low_after(start_i):
            for k in range(max(1,start_i+1),n-1):
                if wl.iloc[k] < wl.iloc[k-1] and wl.iloc[k] < wl.iloc[k+1]:
                    return k
            return None

        swing_l_i=first_swing_low_after(breakout_i)

        for event_i in range(n-2,breakout_i,-1):
            weeks_ago=n-1-event_i
            wc_cur=wc.iloc[event_i]
            ma_cur=ma30.iloc[event_i]
            wl_cur=wl.iloc[event_i]
            has_swing_l=swing_l_i is not None and swing_l_i<=event_i
            if has_swing_l and wc_cur>ma_cur and wl_cur<=ma_cur:
                return "回測",weeks_ago
            prev_i=event_i-1
            if prev_i>breakout_i:
                wc_prev=wc.iloc[prev_i]
                ma_prev=ma30.iloc[prev_i]
                prev2_i=prev_i-1
                if prev2_i>=breakout_i:
                    wc_prev2=wc.iloc[prev2_i]
                    ma_prev2=ma30.iloc[prev2_i]
                else:
                    wc_prev2=None
                    ma_prev2=None
                if wc_cur>ma_cur and wc_prev<=ma_prev and wc_prev2 is not None and wc_prev2>ma_prev2:
                    return "回測",weeks_ago
        return "突破",breakout_weeks_ago
    except: return "-",None

def find_fbos_fcoch(hist, wma30_status, wma30_weeks):
    """
    週線首次破結構：
    - 突破：先等待突破週之後形成Pushback SwingL，再由SwingL往左找SwingH，後續突破才是FBOS。
    - 回測：直接由回測週往左找最近SwingH，後續突破才是FChoCH。
    """
    try:
        if wma30_status not in ("突破","回測"): return "-",None,None
        if wma30_weeks is None: return "-",None,None

        c=hist["Close"].squeeze(); hi=hist["High"].squeeze(); lo=hist["Low"].squeeze(); op=hist["Open"].squeeze()
        c.index=pd.to_datetime(c.index); hi.index=pd.to_datetime(hi.index); lo.index=pd.to_datetime(lo.index); op.index=pd.to_datetime(op.index)
        wc=c.resample("W").last().dropna()
        wo=op.resample("W").first().dropna()
        wh=hi.resample("W").max().dropna()
        wl=lo.resample("W").min().dropna()
        wc,wh=wc.align(wh,join="inner")
        wl=wl.reindex(wc.index); wh=wh.reindex(wc.index); wo=wo.reindex(wc.index)
        n=len(wc)
        if n<5: return "-",None,None

        wc_arr=wc.values; wh_arr=wh.values; wl_arr=wl.values; wo_arr=wo.values
        latest_i=n-1

        try:
            event_weeks=int(round(float(wma30_weeks)))
        except:
            return "-",None,None

        event_i=latest_i-event_weeks
        if event_i<2 or event_i>latest_i: return "-",None,None

        def swing_highs(s, e):
            """找s到e範圍內的SwingH，由新到舊（index大的在前）"""
            out = []
            for k in range(max(1, s), min(e, n-1)):
                if wh_arr[k] > wh_arr[k-1] and wh_arr[k] > wh_arr[k+1]:
                    out.append(k)
            return list(reversed(out))  # [0]=最新(最右)

        def swing_lows(s, e):
            """找s到e範圍內的SwingL，由新到舊（index大的在前）"""
            out = []
            for k in range(max(1, s), min(e, n-1)):
                if wl_arr[k] < wl_arr[k-1] and wl_arr[k] < wl_arr[k+1]:
                    out.append(k)
            return list(reversed(out))  # [0]=最新(最右)

        def check_breakout(sh_price, search_from, same_week_confirm_i=None):
            for j in range(search_from, latest_i + 1):
                broke=float(wh_arr[j]) > sh_price or float(wc_arr[j]) > sh_price
                if j==same_week_confirm_i and j>0:
                    prev_open=float(wo_arr[j-1])
                    broke=broke and float(wc_arr[j]) > prev_open
                if broke:
                    return latest_i - j
            return None

        if wma30_status == "突破":
            sl_after = swing_lows(event_i + 1, latest_i)
            if not sl_after:
                return "待出現SwingL", None, None
            sl_i = sl_after[-1]  # 第一個Pushback低點
            sh_before = swing_highs(max(0, sl_i - 30), sl_i)
            if not sh_before:
                return "-", None, None
            sh_i = sh_before[0]  # Pushback前最近SwingH
            shp = round(float(wh_arr[sh_i]), 2)
            weeks_ago = check_breakout(shp, sl_i, same_week_confirm_i=sl_i)
            if weeks_ago is not None:
                return "FBOS", weeks_ago, shp
            return "待突破(BOS)", None, shp

        if wma30_status == "回測":
            sl_near = swing_lows(max(0, event_i - 4), min(n, event_i + 2))
            if sl_near:
                sl_i = sl_near[0]
                sh_before_sl = swing_highs(max(0, sl_i - 30), sl_i)
                if sh_before_sl:
                    sh_i = sh_before_sl[0]
                    shp = round(float(wh_arr[sh_i]), 2)
                    weeks_ago = check_breakout(shp, sl_i, same_week_confirm_i=sl_i)
                    if weeks_ago is not None:
                        return "FChoCH", weeks_ago, shp
            sh_before = swing_highs(max(0, event_i - 30), event_i)
            if not sh_before:
                return "-", None, None
            sh_i = sh_before[0]
            shp = round(float(wh_arr[sh_i]), 2)
            weeks_ago = check_breakout(shp, event_i, same_week_confirm_i=event_i)
            if weeks_ago is not None:
                return "FChoCH", weeks_ago, shp
            return "待突破(CoC)", None, shp

    except:
        return "-",None,None

def calc_ath_and_52w(hist):
    try:
        c=hist["Close"].squeeze(); price=c.iloc[-1]; ath=c.max()
        high52=c[-252:].max(); low52=c[-252:].min()
        dist_ath=round((price/ath-1)*100,1); dist_52h=round((price/high52-1)*100,1)
        dist_52l=round((price/low52-1)*100,1)
        return dist_ath,dist_52h,dist_52l,bool(dist_ath>=-0.5),bool(dist_52h>=-0.5)
    except: return None,None,None,False,False

# ══════════════════════════════════════════════════════════════
# 格式化
# ══════════════════════════════════════════════════════════════
def _color(v):
    if v is None: return "#888"
    return "#22c55e" if v>=0 else "#ef4444"

def _accel_sup(a):
    return f'<span class="accel-sup">×{a}季</span>' if a>=2 else ""

def fmt_roc(v):
    if v is None: return '<span class="neu">—</span>'
    return f'<span class="{"pos" if v>=0 else "neg"}">{v:+.2f}%</span>'

def fmt_sig_val(val,sig,accel=0):
    if val is None: return '<span class="neu">—</span>'
    return f'<span style="color:{_color(val)}">{val:+.1f}%</span> {sig}{_accel_sup(accel)}'

def fmt_gm_sig(val,sig,accel=0):
    if val is None: return '<span class="neu">—</span>'
    return f'<span style="color:{_color(val)}">{val:.1f}%</span> {sig}{_accel_sup(accel)}'

def fmt_ni_sig(val,sig,accel=0):
    if val is None: return '<span class="neu">—</span>'
    unit="B" if abs(val)>=1000 else "M"
    disp=f"{val/1000:.1f}{unit}" if abs(val)>=1000 else f"{val:.0f}M"
    return f'<span style="color:{_color(val)}">{disp}</span> {sig}{_accel_sup(accel)}'

def fmt_vol_ratio(v):
    if v is None: return '<span class="neu">—</span>'
    return f'<span style="color:{_color(v)}">{v:+.1f}%</span>'

def fmt_ath(d,n):
    if d is None: return '<span class="neu">—</span>'
    if n: return '<span class="ath-badge">ATH</span>'
    return f'<span style="color:{_color(d)}">{d:.1f}%</span>'

def fmt_52h(d,n):
    if d is None: return '<span class="neu">—</span>'
    if n: return '<span class="w52-badge">52W高</span>'
    return f'<span style="color:{_color(d)}">{d:.1f}%</span>'

def fmt_wma30_status(status,weeks_ago):
    if status=="突破":
        wk='<span style="background:#60a5fa22;border:1px solid #60a5fa;color:#60a5fa;padding:1px 5px;border-radius:3px;font-size:10px;margin-left:3px">本週</span>' if weeks_ago==0 else f'<span style="color:#888;font-size:10px"> {weeks_ago}週前</span>' if weeks_ago is not None else ""
        return f'<span class="break-badge">突破</span>{wk}'
    elif status=="回測":
        wk='<span style="background:#60a5fa22;border:1px solid #60a5fa;color:#60a5fa;padding:1px 5px;border-radius:3px;font-size:10px;margin-left:3px">本週</span>' if weeks_ago==0 else f'<span style="color:#888;font-size:10px"> {weeks_ago}週前</span>' if weeks_ago is not None else ""
        return f'<span class="retest-badge">回測</span>{wk}'
    elif status=="超過52週":
        return '<span style="color:#777;font-size:10px">超過52週</span>'
    return '<span class="neu">—</span>'

def fmt_fbos(label,weeks_ago,swing_h):
    if label=="-": return '<span class="neu">—</span>'
    if label=="FBOS":
        wk='<span style="background:#60a5fa22;border:1px solid #60a5fa;color:#60a5fa;padding:1px 5px;border-radius:3px;font-size:10px;margin-left:3px">本週</span>' if weeks_ago==0 else f'<span style="color:#888;font-size:10px"> {weeks_ago}週前</span>' if weeks_ago is not None else ""
        return f'<span style="background:#22c55e22;border:1px solid #22c55e;color:#22c55e;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600">FBOS</span>{wk}'
    if label=="FChoCH":
        wk='<span style="background:#60a5fa22;border:1px solid #60a5fa;color:#60a5fa;padding:1px 5px;border-radius:3px;font-size:10px;margin-left:3px">本週</span>' if weeks_ago==0 else f'<span style="color:#888;font-size:10px"> {weeks_ago}週前</span>' if weeks_ago is not None else ""
        return f'<span style="background:#a78bfa22;border:1px solid #a78bfa;color:#a78bfa;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600">FChoCH</span>{wk}'
    if "待突破" in label:
        price_str=f'<span style="color:#f59e0b"> ${swing_h}</span>' if swing_h else ""
        sub="(CoC)" if "CoC" in label else "(BOS)" if "BOS" in label else ""
        sub_str=f'<span style="color:#555;font-size:9px">{sub}</span>' if sub else ""
        return f'<span style="color:#888">待突破{sub_str}</span>{price_str}'
    if "待出現SwingL" in label:
        return '<span style="color:#888">待出現<span style="color:#60a5fa;font-weight:600">SwingL</span></span>'
    return '<span class="neu">—</span>'

def rs_bar(pct):
    pct=max(0,min(99,int(pct)))
    c="#22c55e" if pct>=90 else "#84cc16" if pct>=70 else "#eab308" if pct>=50 else "#ef4444"
    w=int(pct*80/99)
    return f'<div class="rs-bar-wrap"><div class="rs-bar-bg"><div class="rs-bar-fill" style="width:{w}px;background:{c}"></div></div><span style="color:{c};font-weight:700;font-size:12px">{pct}</span></div>'

def cap_fmt(n):
    if n is None: return "—"
    if n>=1e12: return f"${n/1e12:.1f}T"
    if n>=1e9: return f"${n/1e9:.1f}B"
    if n>=1e6: return f"${n/1e6:.1f}M"
    return f"${n:.0f}"

def ma_badge(v):
    if v is None: return '<span class="neu">—</span>'
    return '<span style="color:#22c55e">✅</span>' if v else '<span style="color:#ef4444">❌</span>'

def idx_col(tkr,sp500,ndx):
    b=""
    if tkr in sp500: b+='<span class="sp500-badge">S&P</span>'
    if tkr in ndx: b+=' <span class="ndx-badge">NDX</span>'
    return b.strip() or '<span class="neu">—</span>'

# ══════════════════════════════════════════════════════════════
# 柱狀圖
# ══════════════════════════════════════════════════════════════
def make_bar_chart(quarters,values,signals,title,ni_abs=None):
    if ni_abs is not None:
        amt_vals=[na if na is not None else 0 for na in ni_abs]
        pct_vals=[v if v is not None else 0 for v in values]
        amt_colors=["#22c55e" if na is not None and na>=0 else "#ef4444" if na is not None else "#333" for na in ni_abs]
        pct_colors=["#22c55e" if v is not None and v>=0 else "#ef4444" if v is not None else "#333" for v in values]
        amt_text=[]
        for na in ni_abs:
            if na is None: amt_text.append("—"); continue
            unit="B" if abs(na)>=1000 else "M"
            disp=f"{na/1000:.1f}{unit}" if abs(na)>=1000 else f"{na:.0f}M"
            amt_text.append(disp)
        pct_text=[f"{v:+.1f}%" if v is not None else "—" for v in values]
        annotations=[]
        for i,(s,v) in enumerate(zip(signals,pct_vals)):
            if s not in ("🚀","✅","↘️","⚠️","❌","🔄"): continue
            annotations.append(dict(x=quarters[i],y=v,text=s,showarrow=False,yref="y2",
                                    yshift=24 if v>=0 else -24,font=dict(size=15),xanchor="center"))
        amt_max=max([abs(v) for v in amt_vals] or [1]) or 1
        pct_max=max([abs(v) for v in pct_vals] or [1]) or 1
        fig=go.Figure()
        fig.add_trace(go.Bar(name="金額",x=quarters,y=amt_vals,marker_color=amt_colors,
                             text=amt_text,textposition="outside",textfont=dict(size=9,color="#ccc"),
                             offsetgroup="amount",yaxis="y"))
        fig.add_trace(go.Bar(name="季增率",x=quarters,y=pct_vals,marker_color=pct_colors,
                             text=pct_text,textposition="outside",textfont=dict(size=9,color="#ccc"),
                             offsetgroup="pct",yaxis="y2"))
        fig.update_layout(title=dict(text=title,font=dict(color="#777",size=12),x=0),
                          plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",font=dict(color="#555",size=10),
                          margin=dict(l=10,r=10,t=55,b=20),height=270,
                          xaxis=dict(showgrid=False,tickfont=dict(size=9,color="#555")),
                          yaxis=dict(showgrid=True,gridcolor="#1a1a2e",zeroline=True,zerolinecolor="#333",
                                     tickfont=dict(size=9),title=dict(text="金額(M)",font=dict(size=9,color="#555")),
                                     range=[-amt_max*1.25,amt_max*1.25]),
                          yaxis2=dict(overlaying="y",side="right",showgrid=False,zeroline=True,zerolinecolor="#333",
                                      tickfont=dict(size=9),title=dict(text="季增率%",font=dict(size=9,color="#555")),
                                      range=[-pct_max*1.25,pct_max*1.25]),
                          annotations=annotations,showlegend=True,barmode="group",bargap=0.35,
                          legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,
                                      font=dict(size=9,color="#777")))
        return fig
    else:
        vals=[v if v is not None else 0 for v in values]
        colors=["#22c55e" if v is not None and v>=0 else "#ef4444" if v is not None else "#333" for v in values]
        text=[f"{v:+.1f}%" if v is not None else "—" for v in values]
    annotations=[]
    for i,(s,v) in enumerate(zip(signals,vals)):
        if s not in ("🚀","✅","↘️","⚠️","❌","🔄"): continue
        annotations.append(dict(x=quarters[i],y=v,text=s,showarrow=False,
                                yshift=24 if v>=0 else -24,font=dict(size=15),xanchor="center"))
    fig=go.Figure(go.Bar(x=quarters,y=vals,marker_color=colors,text=text,
                         textposition="outside",textfont=dict(size=9,color="#ccc")))
    fig.update_layout(title=dict(text=title,font=dict(color="#777",size=12),x=0),
                      plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",font=dict(color="#555",size=10),
                      margin=dict(l=10,r=10,t=55,b=20),height=270,
                      xaxis=dict(showgrid=False,tickfont=dict(size=9,color="#555")),
                      yaxis=dict(showgrid=True,gridcolor="#1a1a2e",zeroline=True,
                                 zerolinecolor="#333",tickfont=dict(size=9)),
                      annotations=annotations,showlegend=False,bargap=0.3)
    return fig

def show_bar_charts(bar_data):
    if not bar_data: st.info("暫無季度財務數據"); return
    qs=[d["quarter"] for d in bar_data]
    eps_v=[d["eps_qoq"] for d in bar_data]; eps_s=[d.get("eps_sig","—") for d in bar_data]
    rev_v=[d["rev_qoq"] for d in bar_data]; rev_s=[d.get("rev_sig","—") for d in bar_data]
    gm_v=[d["gross_margin"] for d in bar_data]; gm_s=[d.get("gm_sig","—") for d in bar_data]
    ni_v=[d["ni_qoq"] for d in bar_data]; ni_s=[d.get("ni_sig","—") for d in bar_data]
    ni_abs=[d["net_income"] for d in bar_data]
    eps_accel=consecutive_accel(eps_s); rev_accel=consecutive_accel(rev_s)
    gm_accel=consecutive_accel(gm_s); ni_accel=consecutive_accel(ni_s)
    def al(n,label): return f"{label} 🚀×{n}季加速" if n>=2 else label
    c1,c2=st.columns(2)
    with c1: st.plotly_chart(make_bar_chart(qs,eps_v,eps_s,al(eps_accel,"■ EPS 季增率")),use_container_width=True)
    with c2: st.plotly_chart(make_bar_chart(qs,rev_v,rev_s,al(rev_accel,"■ 營收季增率")),use_container_width=True)
    c3,c4=st.columns(2)
    with c3: st.plotly_chart(make_bar_chart(qs,gm_v,gm_s,al(gm_accel,"🔶 毛利率")),use_container_width=True)
    with c4: st.plotly_chart(make_bar_chart(qs,ni_v,ni_s,al(ni_accel,"💰 淨利潤"),ni_abs=ni_abs),use_container_width=True)
    summary=[]
    if eps_accel>=2: summary.append(f"EPS 連續 **{eps_accel}季** 加速 🚀")
    if rev_accel>=2: summary.append(f"營收 連續 **{rev_accel}季** 加速 🚀")
    if gm_accel>=2: summary.append(f"毛利率 連續 **{gm_accel}季** 改善 🚀")
    if ni_accel>=2: summary.append(f"淨利潤 連續 **{ni_accel}季** 加速 🚀")
    if summary: st.markdown("🔥 **加速亮點：** " + " ｜ ".join(summary))

# ══════════════════════════════════════════════════════════════
# 技術說明
# ══════════════════════════════════════════════════════════════
def show_tech_notes():
    with st.expander("📚 技術說明（點擊展開/收起）",expanded=False):
        st.markdown("""
<div class="tech-box">
<h4>📊 RS Rating 計算方式</h4>
出自 <b>Investor's Business Daily（IBD）</b>，本程式近似計算：<br>
<code>RS原始分數 = 過去12個月漲幅 × 60% + 過去3個月漲幅 × 40%</code><br>
轉換為 <b>0～99 百分位數</b>（RS 99 = 全場最強前1%）
</div>
<div class="tech-box">
<h4>⭐ SEPA 入選條件（Mark Minervini《超級績效》）</h4>
<ul>
<li>① 股價 > 150MA > 200MA</li><li>② 200MA 上升趨勢</li>
<li>③ 股價 > 50MA</li><li>④ 距52週低點 ≥ 30%</li><li>⑤ 距52週高點 ≤ 25%</li>
</ul>
</div>
<div class="tech-box">
<h4>💡 RS突破追入市值建議</h4>
✅ ≥$2B 最佳 ｜ ✅ ≥$1B 可接受 ｜ ⚠️ $300M～$1B 風險高 ｜ ❌ &lt;$300M 不建議
</div>
<div class="tech-box">
<h4>🚀✅↘️⚠️❌🔄 信號說明</h4>
<ul>
<li>🚀 加速成長/改善（增速比上季更快，×N季=連續N季）</li>
<li>✅ 正向成長（正數但未加速）</li>
<li>↘️ 正向但減速（仍是正成長，但增速低於上季）</li>
<li>⚠️ 小幅惡化（例如毛利率仍為正但較上季回落）</li>
<li>❌ 負成長/惡化</li>
<li>🔄 從負轉正（重要反轉信號）</li>
</ul>
</div>
<div class="tech-box">
<h4>📉 W-MA30 狀態（掃描52週）</h4>
<ul>
<li><b>突破</b>：前週收盤低於MA30，當週收盤穿越MA30上方</li>
<li><b>回測</b>：週低點觸及MA30但守住；或跌破後下週收回</li>
<li><b>—</b>：W&gt;MA30不成立或52週內無事件</li>
</ul>
</div>
<div class="tech-box">
<h4>📐 週首次破結構（FBOS / FChoCH）</h4>
以W-MA30事件發生週為起點，只在事件之後搜索：<br>
<b>SwingH</b>：某週High &gt; 前週且 &gt; 後週 ｜ <b>SwingL</b>：某週Low &lt; 前週且 &lt; 後週<br><br>
<b>FBOS</b>（突破/回測）：事件後出現SwingL（Pushback），事件前SwingH被突破<br>
<b>FChoCH</b>（回測）：無SwingL時，直接找事件前SwingH被突破<br>
<b>待突破 $xxx</b>：已識別SwingH但尚未突破，顯示目標價<br>
Sweep（週High超過）或Closure（週收盤超過）皆算觸發
</div>
<div class="tech-box">
<h4>📐 Minervini & O'Neil 標準</h4>
EPS季增率 ≥+25%（理想≥+50%）｜ 營收季增率 ≥+20% ｜ 毛利率穩定改善<br>
RS Rating：O'Neil ≥80 ｜ Minervini ≥90 ｜ 突破成交量 ≥均量40%<br>
停損：-7%~-8%（O'Neil）｜ -10%~-15%（Minervini）
</div>
""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 個股詳細面板
# ══════════════════════════════════════════════════════════════
def show_stock_detail(ticker,hist,sepa_conds,df_row,sp500,ndx):
    st.markdown(f'<div style="border-top:2px solid #00d4aa;margin:20px 0 10px 0;padding-top:12px"><span style="font-size:11px;color:#555;letter-spacing:2px">FUNDAMENTAL TRACKER · {datetime.today().strftime("%Y-%m-%d")}</span></div>',unsafe_allow_html=True)
    try: info=yf.Ticker(ticker).info or {}
    except: info={}
    price=df_row.get("Price","—"); name=info.get("longName") or df_row.get("Name",ticker)
    sector=info.get("sector") or df_row.get("Sector","—"); ind=info.get("industry","—")
    tgt=info.get("targetMeanPrice","—"); tgt_lo=info.get("targetLowPrice","—")
    tgt_hi=info.get("targetHighPrice","—"); n_an=info.get("numberOfAnalystOpinions","—")
    rating=(info.get("recommendationKey","—") or "—").upper().replace("_"," ")
    rs_pct=df_row.get("RS_pct","—")
    try: upside=f"{(float(tgt)/float(price)-1)*100:+.1f}%"
    except: upside="—"
    c1,c2=st.columns([1,3])
    with c1:
        st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:36px;font-weight:900;color:#00d4aa">{ticker}</div>',unsafe_allow_html=True)
        st.markdown(idx_col(ticker,sp500,ndx),unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div style="font-size:18px;font-weight:700;color:#fff;margin-top:8px">{name}</div><div style="font-size:12px;color:#555;margin-top:4px">{sector} / {ind}</div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    for (label,val,sub,border),col in zip(
        [("PRICE",f"${price}","現價 USD","#3b82f6"),
         ("ANALYST TARGET",f"${tgt}",f"上漲空間 {upside}","#f59e0b"),
         ("RATING",rating,f"{n_an} analysts","#8b5cf6"),
         ("RS RATING",str(rs_pct),"全市場百分位","#00d4aa")],st.columns(4)):
        with col:
            st.markdown(f'<div style="background:#0f172a;border:1px solid #1e293b;border-top:3px solid {border};padding:16px;border-radius:4px"><div style="font-size:10px;letter-spacing:2px;color:#555">{label}</div><div style="font-size:22px;font-weight:900;color:#fff">{val}</div><div style="font-size:11px;color:#888">{sub}</div></div>',unsafe_allow_html=True)
    dist_ath=df_row.get("DistATH"); dist_52h=df_row.get("Dist52H")
    dist_52l=df_row.get("Dist52L"); near_ath=df_row.get("NearATH",False); near_52h=df_row.get("Near52H",False)
    wma30_status=df_row.get("WMA30_Status","-"); wma30_weeks=df_row.get("WMA30_Weeks",None)
    fbos_label=df_row.get("FBOS_Label","-"); fbos_weeks=df_row.get("FBOS_Weeks",None); fbos_swing_h=df_row.get("FBOS_SwingH",None)
    st.markdown("<br>",unsafe_allow_html=True)
    for (label,val_html),col in zip(
        [("距歷史高位",fmt_ath(dist_ath,near_ath)),
         ("距52週高點",fmt_52h(dist_52h,near_52h)),
         ("距52週低點",f'<span style="color:#22c55e">{dist_52l:+.1f}%</span>' if dist_52l else "—"),
         ("W>MA30",ma_badge(df_row.get("WeeklyMA30"))),
         ("W-MA30狀態",fmt_wma30_status(wma30_status,wma30_weeks)),
         ("週首次破結構",fmt_fbos(fbos_label,fbos_weeks,fbos_swing_h))],
        st.columns(6)):
        with col:
            st.markdown(f'<div style="background:#0f172a;border:1px solid #1e293b;padding:10px;border-radius:4px;text-align:center"><div style="font-size:10px;color:#555;margin-bottom:4px">{label}</div><div style="font-size:14px;font-weight:700">{val_html}</div></div>',unsafe_allow_html=True)
    st.markdown('<div style="border-left:3px solid #00d4aa;padding-left:12px;margin:20px 0 8px 0"><span style="font-size:11px;letter-spacing:2px;color:#555">// SEPA 條件檢查</span></div>',unsafe_allow_html=True)
    if sepa_conds:
        for (cond,ok),sc in zip(sepa_conds.items(),st.columns(len(sepa_conds))):
            color="#22c55e" if ok else "#ef4444"
            with sc:
                st.markdown(f'<div style="background:#0f172a;border:1px solid #1e293b;padding:10px;border-radius:4px;text-align:center"><div style="font-size:18px">{"✅" if ok else "❌"}</div><div style="font-size:10px;color:{color};margin-top:4px">{cond}</div></div>',unsafe_allow_html=True)
    st.markdown('<div style="border-left:3px solid #00d4aa;padding-left:12px;margin:20px 0 8px 0"><span style="font-size:11px;letter-spacing:2px;color:#555">// ROC 表現</span></div>',unsafe_allow_html=True)
    for (label,key),rc in zip([("1週","ROC_1W"),("3月","ROC_3M"),("6月","ROC_6M"),("9月","ROC_9M"),("12月","ROC_12M")],st.columns(5)):
        val=df_row.get(key); color="#22c55e" if val and val>=0 else "#ef4444"
        with rc:
            st.markdown(f'<div style="background:#0f172a;border:1px solid #1e293b;padding:10px;border-radius:4px;text-align:center"><div style="font-size:10px;color:#555">{label}</div><div style="font-size:16px;font-weight:700;color:{color}">{f"{val:+.2f}%" if val else "—"}</div></div>',unsafe_allow_html=True)
    st.markdown('<div style="border-left:3px solid #00d4aa;padding-left:12px;margin:20px 0 8px 0"><span style="font-size:11px;letter-spacing:2px;color:#555">// 近5季財務趨勢</span></div>',unsafe_allow_html=True)
    bar_data=load_precomputed_bar_data(ticker)
    if not bar_data:
        with st.spinner("載入季度財務數據…"):
            _,_,_,_,bar_data,_=get_yf_financials(ticker)
    show_bar_charts(bar_data)
    st.markdown('<div style="border-left:3px solid #00d4aa;padding-left:12px;margin:20px 0 8px 0"><span style="font-size:11px;letter-spacing:2px;color:#555">// 近6季 EPS 季增紀錄</span></div>',unsafe_allow_html=True)
    with st.spinner("載入EPS紀錄…"):
        eps_records=get_eps_records(ticker)
    if eps_records: st.dataframe(pd.DataFrame(eps_records),use_container_width=True,hide_index=True)
    else: st.info("暫無EPS數據")
    st.markdown('<div style="border-left:3px solid #00d4aa;padding-left:12px;margin:20px 0 8px 0"><span style="font-size:11px;letter-spacing:2px;color:#555">// 分析師目標價</span></div>',unsafe_allow_html=True)
    st.markdown(f'<div style="background:#0f172a;border:1px solid #1e293b;padding:16px;border-radius:4px;font-size:12px;color:#888;line-height:2">▶ 評級：<span style="color:#fff">{rating}</span><br>▶ 目標價：低 <span style="color:#ef4444">${tgt_lo}</span> 均值 <span style="color:#f59e0b">${tgt}</span> 高 <span style="color:#22c55e">${tgt_hi}</span><br>▶ 分析師人數：<span style="color:#fff">{n_an}</span></div>',unsafe_allow_html=True)
    desc=info.get("longBusinessSummary","")
    if desc:
        st.markdown('<div style="border-left:3px solid #00d4aa;padding-left:12px;margin:20px 0 8px 0"><span style="font-size:11px;letter-spacing:2px;color:#555">// 公司簡介</span></div>',unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:12px;color:#aaa;line-height:1.8">{desc[:600]}…</div>',unsafe_allow_html=True)
    st.markdown(f'<div style="margin-top:32px;padding-top:12px;border-top:1px solid #1e293b;font-size:10px;color:#333;letter-spacing:2px">⚡ DATA · yfinance · {datetime.today().strftime("%Y-%m-%d")}</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 主分析流程
# ══════════════════════════════════════════════════════════════
class _CliStatus:
    def __init__(self,label=""):
        self.label=label
    def text(self,msg): print(msg)
    def warning(self,msg): print(f"WARNING: {msg}")
    def empty(self): pass
    def progress(self,value): pass

def _write_parquet(df,path):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    df.to_parquet(path,index=False)

def _read_parquet(path):
    path=Path(path)
    if not path.exists(): return None
    return pd.read_parquet(path)

def save_analysis_outputs(df,sp500,ndx,as_of=None,dataset_key="quality"):
    as_of=as_of or datetime.now().strftime("%Y-%m-%d")
    latest_dir=DATA_DIR/"latest"
    daily_dir=DATA_DIR/"daily"/dataset_key
    latest_name="rs_latest.parquet" if dataset_key=="quality" else f"rs_latest_{dataset_key}.parquet"
    meta_name="meta.parquet" if dataset_key=="quality" else f"meta_{dataset_key}.parquet"
    _write_parquet(df,latest_dir/latest_name)
    _write_parquet(df,daily_dir/f"{as_of}.parquet")
    meta=pd.DataFrame([{"as_of":as_of,"updated_at":datetime.now().isoformat(timespec="seconds"),"rows":len(df),"dataset":dataset_key}])
    _write_parquet(meta,latest_dir/meta_name)
    (latest_dir/"sp500.txt").write_text("\n".join(sorted(sp500)),encoding="utf-8")
    (latest_dir/"ndx100.txt").write_text("\n".join(sorted(ndx)),encoding="utf-8")
    cutoff=datetime.now()-timedelta(days=190)
    for old in daily_dir.glob("*.parquet"):
        try:
            if datetime.strptime(old.stem,"%Y-%m-%d")<cutoff:
                old.unlink()
        except Exception:
            continue

def save_fundamentals(df,detail_df=None,as_of=None):
    as_of=as_of or datetime.now().strftime("%Y-%m")
    cols=["Ticker","EPS_QoQ","Rev_QoQ","GrossMargin","NetIncome","EPS_Sig","Rev_Sig","GM_Sig","NI_Sig","EPS_Accel","Rev_Accel","GM_Accel","NI_Accel"]
    out=df[[c for c in cols if c in df.columns]].copy()
    _write_parquet(out,DATA_DIR/"latest"/"fundamentals_latest.parquet")
    _write_parquet(out,DATA_DIR/"fundamentals"/f"{as_of}.parquet")
    if detail_df is not None and not detail_df.empty:
        _write_parquet(detail_df,DATA_DIR/"latest"/"fundamentals_detail_latest.parquet")
        _write_parquet(detail_df,DATA_DIR/"fundamentals"/f"{as_of}_detail.parquet")

def load_precomputed_bar_data(ticker):
    detail=_read_parquet(DATA_DIR/"latest"/"fundamentals_detail_latest.parquet")
    if detail is None or detail.empty or "Ticker" not in detail.columns:
        return []
    rows=detail[detail["Ticker"].astype(str).str.upper()==str(ticker).upper()].copy()
    if rows.empty:
        return []
    rows=rows.sort_values("order")
    return [
        {
            "quarter":r.get("quarter"),
            "eps_qoq":r.get("eps_qoq"),
            "rev_qoq":r.get("rev_qoq"),
            "gross_margin":r.get("gross_margin"),
            "net_income":r.get("net_income"),
            "ni_qoq":r.get("ni_qoq"),
            "eps_sig":r.get("eps_sig","—"),
            "rev_sig":r.get("rev_sig","—"),
            "gm_sig":r.get("gm_sig","—"),
            "ni_sig":r.get("ni_sig","—"),
        }
        for _,r in rows.iterrows()
    ]

def load_precomputed_outputs(dataset_key="quality"):
    latest_name="rs_latest.parquet" if dataset_key=="quality" else f"rs_latest_{dataset_key}.parquet"
    meta_name="meta.parquet" if dataset_key=="quality" else f"meta_{dataset_key}.parquet"
    df=_read_parquet(DATA_DIR/"latest"/latest_name)
    if df is None: return None
    fundamentals=_read_parquet(DATA_DIR/"latest"/"fundamentals_latest.parquet")
    if fundamentals is not None and "Ticker" in fundamentals.columns:
        fund_cols=[c for c in fundamentals.columns if c!="Ticker"]
        df=df.drop(columns=[c for c in fund_cols if c in df.columns],errors="ignore")
        df=df.merge(fundamentals,on="Ticker",how="left")
    for col,default in [
        ("EPS_QoQ",None),("Rev_QoQ",None),("GrossMargin",None),("NetIncome",None),
        ("EPS_Sig","—"),("Rev_Sig","—"),("GM_Sig","—"),("NI_Sig","—"),
        ("EPS_Accel",0),("Rev_Accel",0),("GM_Accel",0),("NI_Accel",0),
    ]:
        if col not in df.columns: df[col]=default
    sp500=set()
    ndx=set()
    sp_path=DATA_DIR/"latest"/"sp500.txt"
    ndx_path=DATA_DIR/"latest"/"ndx100.txt"
    if sp_path.exists(): sp500=set(sp_path.read_text(encoding="utf-8").splitlines())
    if ndx_path.exists(): ndx=set(ndx_path.read_text(encoding="utf-8").splitlines())
    meta=_read_parquet(DATA_DIR/"latest"/meta_name)
    updated=""
    if meta is not None and not meta.empty:
        updated=str(meta.iloc[0].get("updated_at",""))
    return df,{}, {},sp500,ndx,updated

def run_analysis(max_stocks,min_cap_b,universe,min_price,min_avg_dollar_vol_m,min_listing_years,
                 exclude_etf,exclude_warrant,exclude_unit,exclude_preferred,exclude_right,
                 include_fundamentals=True,ui=True):
    nasdaq_df=get_nasdaq_tickers(universe)
    if nasdaq_df.empty:
        if ui: st.error("無法取得股票清單")
        else: print("無法取得股票清單")
        return None
    sp500,ndx=get_index_members()
    min_cap=min_cap_b*1_000_000_000
    filtered=nasdaq_df[nasdaq_df["MarketCapNum"]>=min_cap] if min_cap>0 else nasdaq_df
    filtered=filtered[
        ~filtered.apply(
            lambda r:is_excluded_instrument(
                r,exclude_etf,exclude_warrant,exclude_unit,exclude_preferred,exclude_right
            ),
            axis=1,
        )
    ]
    if min_listing_years>0 and "IPOYear" in filtered.columns:
        current_year=datetime.today().year
        ipo_year=pd.to_numeric(filtered["IPOYear"],errors="coerce")
        filtered=filtered[ipo_year.isna() | ((current_year-ipo_year)>=min_listing_years)]
    tickers=filtered["Ticker"].tolist()[:max_stocks]
    total=len(tickers)
    end=datetime.today(); start=end-timedelta(days=700)
    progress=st.progress(0) if ui else _CliStatus("progress")
    status=st.empty() if ui else _CliStatus("status")
    results=[]
    for i in range(0,total,20):
        batch=tickers[i:i+20]
        try:
            raw=yf.download(" ".join(batch),start=start,end=end,
                            group_by="ticker",auto_adjust=True,progress=False,threads=True)
            for tkr in batch:
                try:
                    hist=raw[tkr].dropna() if len(batch)>1 else raw.dropna()
                    if hist.empty or len(hist)<80: continue
                    close=hist["Close"].squeeze()
                    volume=hist["Volume"].squeeze()
                    latest_price=float(close.iloc[-1])
                    avg_dollar_vol=float((close.tail(20)*volume.tail(20)).mean())
                    if min_price>0 and latest_price<min_price: continue
                    if min_avg_dollar_vol_m>0 and avg_dollar_vol<(min_avg_dollar_vol_m*1_000_000): continue
                    rs=calc_rs(hist)
                    if rs is None: continue
                    sepa_ok,sepa_conds=check_sepa(hist)
                    wma30=check_weekly_ma30(hist)
                    wma30_status,wma30_weeks=check_weekly_ma30_status(hist)
                    fbos_label,fbos_weeks,fbos_swing_h=find_fbos_fcoch(hist,wma30_status,wma30_weeks)
                    dist_ath,dist_52h,dist_52l,near_ath,near_52h=calc_ath_and_52w(hist)
                    vol_ratio=calc_volume_ratio(hist)
                    row=nasdaq_df[nasdaq_df["Ticker"]==tkr]
                    cap_num=row["MarketCapNum"].values[0] if not row.empty else None
                    sector=row["Sector"].values[0] if not row.empty else "N/A"
                    if str(sector).strip() in ("N/A","","nan","None"): sector=get_sector_yf(tkr)
                    results.append({
                        "Ticker":tkr,"Name":row["Name"].values[0] if not row.empty else tkr,
                        "Sector":sector,"CapNum":cap_num,"RS_raw":rs,
                        "SEPA":sepa_ok,"SEPA_conds":sepa_conds,"WeeklyMA30":wma30,
                        "WMA30_Status":wma30_status,"WMA30_Weeks":wma30_weeks,
                        "FBOS_Label":fbos_label,"FBOS_Weeks":fbos_weeks,"FBOS_SwingH":fbos_swing_h,
                        "SP500":tkr in sp500,"NDX100":tkr in ndx,
                        "Price":round(latest_price,2),
                        "AvgDollarVol20":avg_dollar_vol,
                        "DayChange":calc_day_change(hist),
                        "ROC_1W":calc_roc(hist,5),"ROC_3M":calc_roc(hist,63),
                        "ROC_6M":calc_roc(hist,126),"ROC_9M":calc_roc(hist,189),
                        "ROC_12M":calc_roc(hist,252),
                        "DistATH":dist_ath,"Dist52H":dist_52h,"Dist52L":dist_52l,
                        "NearATH":near_ath,"Near52H":near_52h,"VolRatio":vol_ratio,"hist":hist,
                    })
                except: continue
        except Exception as e: status.warning(f"批次錯誤：{e}")
        progress.progress(min((i+20)/total,1.0))
        status.text(f"下載價格數據 {min(i+20,total)} / {total}")
        time.sleep(0.2)
    progress.empty(); status.empty()
    if not results: return None
    df=pd.DataFrame([{k:v for k,v in r.items() if k not in ("hist","SEPA_conds")} for r in results])
    df=df.sort_values("RS_raw",ascending=False).reset_index(drop=True)
    df["Rank"]=df.index+1; n=len(df); df["RS_pct"]=((n-df["Rank"])/n*99).astype(int)
    if include_fundamentals:
        status2=st.empty() if ui else _CliStatus("fundamentals")
        eps_l,rev_l,gm_l,ni_l=[],[],[],[]
        eps_sig_l,rev_sig_l,gm_sig_l,ni_sig_l=[],[],[],[]
        eps_acc_l,rev_acc_l,gm_acc_l,ni_acc_l=[],[],[],[]
        for idx,tkr in enumerate(df["Ticker"].tolist()):
            status2.text(f"抓取基本面 {idx+1}/{n}：{tkr}")
            e,r,g,ni,_,sigs=get_yf_financials(tkr)
            eps_l.append(e); rev_l.append(r); gm_l.append(g); ni_l.append(ni)
            eps_sig_l.append(sigs.get("eps_latest_sig","—")); rev_sig_l.append(sigs.get("rev_latest_sig","—"))
            gm_sig_l.append(sigs.get("gm_latest_sig","—")); ni_sig_l.append(sigs.get("ni_latest_sig","—"))
            eps_acc_l.append(sigs.get("eps_accel",0)); rev_acc_l.append(sigs.get("rev_accel",0))
            gm_acc_l.append(sigs.get("gm_accel",0)); ni_acc_l.append(sigs.get("ni_accel",0))
            time.sleep(0.08)
        status2.empty()
        df["EPS_QoQ"]=eps_l; df["Rev_QoQ"]=rev_l; df["GrossMargin"]=gm_l; df["NetIncome"]=ni_l
        df["EPS_Sig"]=eps_sig_l; df["Rev_Sig"]=rev_sig_l; df["GM_Sig"]=gm_sig_l; df["NI_Sig"]=ni_sig_l
        df["EPS_Accel"]=eps_acc_l; df["Rev_Accel"]=rev_acc_l; df["GM_Accel"]=gm_acc_l; df["NI_Accel"]=ni_acc_l
    hist_map={r["Ticker"]:r["hist"] for r in results}
    sepa_map={r["Ticker"]:r["SEPA_conds"] for r in results}
    return df,hist_map,sepa_map,sp500,ndx

def build_daily_dataset():
    datasets=[
        ("quality",{"max_stocks":8000,"min_cap_b":1,"universe":"全美上市","min_price":10.0,"min_avg_dollar_vol_m":10.0,"min_listing_years":1}),
        ("us_all",{"max_stocks":8000,"min_cap_b":0,"universe":"全美上市","min_price":0.0,"min_avg_dollar_vol_m":0.0,"min_listing_years":0}),
        ("nasdaq",{"max_stocks":8000,"min_cap_b":0,"universe":"NASDAQ","min_price":0.0,"min_avg_dollar_vol_m":0.0,"min_listing_years":0}),
    ]
    for dataset_key,params in datasets:
        print(f"building dataset: {dataset_key}")
        result=run_analysis(
            exclude_etf=True,
            exclude_warrant=True,
            exclude_unit=True,
            exclude_preferred=True,
            exclude_right=True,
            include_fundamentals=False,
            ui=False,
            **params,
        )
        if not result:
            print(f"WARNING: {dataset_key} dataset build failed")
            continue
        df,_,_,sp500,ndx=result
        save_analysis_outputs(df,sp500,ndx,dataset_key=dataset_key)
        print(f"saved {dataset_key} dataset: {len(df)} rows")

def build_fundamentals_dataset():
    bundle=load_precomputed_outputs()
    if bundle:
        df=bundle[0].copy()
    else:
        result=run_analysis(
            max_stocks=8000,
            min_cap_b=1,
            universe="全美上市",
            min_price=10.0,
            min_avg_dollar_vol_m=10.0,
            min_listing_years=1,
            exclude_etf=True,
            exclude_warrant=True,
            exclude_unit=True,
            exclude_preferred=True,
            exclude_right=True,
            include_fundamentals=False,
            ui=False,
        )
        if not result:
            raise SystemExit("base dataset build failed")
        df=result[0]
    eps_l,rev_l,gm_l,ni_l=[],[],[],[]
    eps_sig_l,rev_sig_l,gm_sig_l,ni_sig_l=[],[],[],[]
    eps_acc_l,rev_acc_l,gm_acc_l,ni_acc_l=[],[],[],[]
    detail_rows=[]
    tickers=df["Ticker"].dropna().astype(str).tolist()
    for idx,tkr in enumerate(tickers):
        print(f"fundamentals {idx+1}/{len(tickers)}: {tkr}")
        e,r,g,ni,bar_data,sigs=get_yf_financials(tkr)
        eps_l.append(e); rev_l.append(r); gm_l.append(g); ni_l.append(ni)
        eps_sig_l.append(sigs.get("eps_latest_sig","—")); rev_sig_l.append(sigs.get("rev_latest_sig","—"))
        gm_sig_l.append(sigs.get("gm_latest_sig","—")); ni_sig_l.append(sigs.get("ni_latest_sig","—"))
        eps_acc_l.append(sigs.get("eps_accel",0)); rev_acc_l.append(sigs.get("rev_accel",0))
        gm_acc_l.append(sigs.get("gm_accel",0)); ni_acc_l.append(sigs.get("ni_accel",0))
        for order,d in enumerate(bar_data):
            row={"Ticker":tkr,"order":order}
            row.update(d)
            detail_rows.append(row)
        time.sleep(0.08)
    fund=pd.DataFrame({
        "Ticker":tickers,
        "EPS_QoQ":eps_l,"Rev_QoQ":rev_l,"GrossMargin":gm_l,"NetIncome":ni_l,
        "EPS_Sig":eps_sig_l,"Rev_Sig":rev_sig_l,"GM_Sig":gm_sig_l,"NI_Sig":ni_sig_l,
        "EPS_Accel":eps_acc_l,"Rev_Accel":rev_acc_l,"GM_Accel":gm_acc_l,"NI_Accel":ni_acc_l,
    })
    save_fundamentals(fund,pd.DataFrame(detail_rows))
    print(f"saved fundamentals dataset: {len(fund)} rows")

if "--build-daily" in sys.argv:
    build_daily_dataset()
    sys.exit(0)

if "--build-fundamentals" in sys.argv:
    build_fundamentals_dataset()
    sys.exit(0)

# ══════════════════════════════════════════════════════════════
# 主頁面
# ══════════════════════════════════════════════════════════════
today_str=datetime.today().strftime("%Y%m%d")
st.markdown(f'<div class="top-bar"><div class="top-title">📈 RS Ranking — NASDAQ</div><div style="color:#555;font-size:11px">資料日期：{today_str}</div></div>',unsafe_allow_html=True)

st.sidebar.header("⚙️ 設定")
dataset_label=st.sidebar.selectbox("資料包",list(DATASET_OPTIONS.keys()),index=0)
dataset_key=DATASET_OPTIONS[dataset_label]
if st.session_state.get("dataset_key")!=dataset_key:
    for k in ("df","hist_map","sepa_map","sp500","ndx","updated"):
        st.session_state.pop(k,None)
    st.session_state["dataset_key"]=dataset_key
    st.rerun()
universe=st.sidebar.selectbox("手動分析股票池",["NASDAQ","全美上市"],index=1)
min_cap_b=st.sidebar.selectbox("最低市值篩選",[0,0.3,0.5,1,2,5,10],format_func=lambda x:"不限" if x==0 else f"≥ ${x}B",index=3)
min_price=st.sidebar.number_input("最低股價",min_value=0.0,value=10.0,step=1.0)
min_avg_dollar_vol_m=st.sidebar.number_input("20日平均成交額(M)",min_value=0.0,value=10.0,step=1.0)
min_listing_years=st.sidebar.slider("最低上市年期",0,10,1,1)
max_stocks=st.sidebar.slider("最多分析股票數",50,8000,300,50)
st.sidebar.caption("資料包切換會讀 GitHub Actions 預計算結果；下方條件只影響手動重新分析。")
with st.sidebar.expander("排除品種",expanded=True):
    exclude_etf=st.checkbox("ETF / Fund / Trust",value=True)
    exclude_warrant=st.checkbox("Warrant",value=True)
    exclude_unit=st.checkbox("Unit",value=True)
    exclude_preferred=st.checkbox("Preferred",value=True)
    exclude_right=st.checkbox("Right",value=True)

if st.sidebar.button("🚀 開始 / 更新分析",type="primary"):
    result=run_analysis(
        max_stocks,min_cap_b,universe,min_price,min_avg_dollar_vol_m,min_listing_years,
        exclude_etf,exclude_warrant,exclude_unit,exclude_preferred,exclude_right
    )
    if result:
        st.session_state["df"]=result[0]; st.session_state["hist_map"]=result[1]
        st.session_state["sepa_map"]=result[2]; st.session_state["sp500"]=result[3]
        st.session_state["ndx"]=result[4]
        st.session_state["updated"]=datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state["sort_col"]="RS_pct"; st.session_state["sort_asc"]=False
        st.rerun()

if "df" not in st.session_state:
    precomputed=load_precomputed_outputs(st.session_state.get("dataset_key","quality"))
    if precomputed:
        st.session_state["df"]=precomputed[0]; st.session_state["hist_map"]=precomputed[1]
        st.session_state["sepa_map"]=precomputed[2]; st.session_state["sp500"]=precomputed[3]
        st.session_state["ndx"]=precomputed[4]; st.session_state["updated"]=precomputed[5]
        st.session_state["sort_col"]="RS_pct"; st.session_state["sort_asc"]=False
        st.rerun()
    st.info(f"👈 暫無「{dataset_label}」GitHub 預計算資料；可先點擊左側「開始/更新分析」以載入數據，或先執行 GitHub Actions")
    show_tech_notes(); st.stop()

df=st.session_state["df"]; hist_map=st.session_state["hist_map"]
sepa_map=st.session_state["sepa_map"]; sp500=st.session_state["sp500"]; ndx=st.session_state["ndx"]
if "sort_col" not in st.session_state: st.session_state["sort_col"]="RS_pct"
if "sort_asc" not in st.session_state: st.session_state["sort_asc"]=False

tab=st.radio("",["📊 全部 RS",f"⭐ SEPA 入選 ({int(df['SEPA'].sum())})"],horizontal=True,label_visibility="collapsed")
st.caption(f"資料包：{dataset_label} | 更新時間：{st.session_state.get('updated','')} | 共分析 {len(df)} 支")

cf1,cf2,cf3,cf4=st.columns([2,2,2,4])
with cf1: search=st.text_input("",placeholder="搜尋代碼…",label_visibility="collapsed")
with cf2:
    cap_opts={"不限":0,"≥ $0.5B":0.5e9,"≥ $1B":1e9,"≥ $2B":2e9,"≥ $5B":5e9,"≥ $10B":10e9,"未知only":-1}
    cap_sel=st.selectbox("市值",list(cap_opts.keys()),label_visibility="collapsed")
with cf3: idx_f=st.multiselect("指數",["S&P500","NASDAQ100"],default=[],label_visibility="collapsed")
with cf4:
    valid_secs=sorted([s for s in df["Sector"].dropna().unique() if str(s) not in ("N/A","nan","None","")])
    sel_sec=st.selectbox("板塊",["全部"]+valid_secs,label_visibility="collapsed")

wma30_filter=st.multiselect(
    "W-MA30狀態篩選",
    ["突破","回測","超過52週","-"],
    default=[],
    placeholder="全部",
    label_visibility="visible",
)
wma30_weeks_range=st.slider(
    "W-MA30事件距今週數",
    min_value=0,
    max_value=52,
    value=(0,52),
    step=1,
)
fbos_filter=st.multiselect(
    "週首次破結構篩選",
    ["FBOS","FChoCH","待出現SwingL","待突破(BOS)","待突破(CoC)","-"],
    default=[],
    placeholder="全部",
    label_visibility="visible",
)

def numeric_filter(label,col,min_value=None,max_value=None,step=None,scale=1.0):
    if col not in df.columns:
        return None
    s=(pd.to_numeric(df[col],errors="coerce")/scale).dropna()
    if s.empty:
        st.caption(f"{label}：暫無可篩選數據")
        return None
    lo=float(s.min()) if min_value is None else float(min_value)
    hi=float(s.max()) if max_value is None else float(max_value)
    if lo==hi:
        st.caption(f"{label}：全部為 {lo:g}")
        return None
    if step is None:
        step=1.0 if hi-lo>20 else 0.1
    return st.slider(label,lo,hi,(lo,hi),step=step)

with st.expander("欄位數值篩選",expanded=False):
    rf1,rf2,rf3=st.columns(3)
    with rf1:
        rs_range=st.slider("RS Rating",0,99,(0,99),1)
        day_range=numeric_filter("當日漲幅","DayChange",step=0.1)
        roc1w_range=numeric_filter("近1週","ROC_1W",step=0.1)
        roc3m_range=numeric_filter("3M ROC","ROC_3M",step=0.1)
    with rf2:
        roc6m_range=numeric_filter("6M ROC","ROC_6M",step=0.1)
        roc12m_range=numeric_filter("12M ROC","ROC_12M",step=0.1)
        eps_range=numeric_filter("EPS季增率","EPS_QoQ",step=0.1)
        rev_range=numeric_filter("營收季增率","Rev_QoQ",step=0.1)
    with rf3:
        gm_range=numeric_filter("毛利率","GrossMargin",step=0.1)
        ni_range=numeric_filter("淨利潤","NetIncome",step=1.0)
        vol_range=numeric_filter("成交量比均20天","VolRatio",step=0.1)
        price_range=numeric_filter("股價","Price",step=0.1)
        cap_range=numeric_filter("市值(B)","CapNum",step=0.1,scale=1_000_000_000)
        dist_ath_range=numeric_filter("距ATH","DistATH",step=0.1)
        dist_52h_range=numeric_filter("距52W高","Dist52H",step=0.1)

def apply_range_filter(source,col,value_range,scale=1.0):
    if value_range is None or col not in source.columns:
        return source
    vals=pd.to_numeric(source[col],errors="coerce")/scale
    return source[vals.between(value_range[0],value_range[1],inclusive="both")]

view_df=df.copy()
if "SEPA" in tab: view_df=view_df[view_df["SEPA"]==True]
if search: view_df=view_df[view_df["Ticker"].str.contains(search.upper(),na=False)]
cap_val=cap_opts[cap_sel]
if cap_val>0: view_df=view_df[view_df["CapNum"]>=cap_val]
elif cap_val==-1: view_df=view_df[view_df["CapNum"].isna()]
if "S&P500" in idx_f: view_df=view_df[view_df["SP500"]==True]
if "NASDAQ100" in idx_f: view_df=view_df[view_df["NDX100"]==True]
if sel_sec!="全部": view_df=view_df[view_df["Sector"]==sel_sec]
if wma30_filter: view_df=view_df[view_df["WMA30_Status"].isin(wma30_filter)]
if wma30_weeks_range!=(0,52):
    wma30_weeks=pd.to_numeric(view_df["WMA30_Weeks"],errors="coerce")
    view_df=view_df[wma30_weeks.between(wma30_weeks_range[0],wma30_weeks_range[1],inclusive="both")]
if fbos_filter: view_df=view_df[view_df["FBOS_Label"].isin(fbos_filter)]
for col,rng,scale in [
    ("RS_pct",rs_range,1.0),("DayChange",day_range,1.0),("ROC_1W",roc1w_range,1.0),
    ("ROC_3M",roc3m_range,1.0),("ROC_6M",roc6m_range,1.0),("ROC_12M",roc12m_range,1.0),
    ("EPS_QoQ",eps_range,1.0),("Rev_QoQ",rev_range,1.0),("GrossMargin",gm_range,1.0),
    ("NetIncome",ni_range,1.0),("VolRatio",vol_range,1.0),("Price",price_range,1.0),
    ("CapNum",cap_range,1_000_000_000),("DistATH",dist_ath_range,1.0),("Dist52H",dist_52h_range,1.0),
]:
    view_df=apply_range_filter(view_df,col,rng,scale)

sort_col=st.session_state["sort_col"]; sort_asc=st.session_state["sort_asc"]
if sort_col in view_df.columns:
    view_df=view_df.sort_values(sort_col,ascending=sort_asc,na_position="last")
st.caption(f"符合條件：{len(view_df)} 支")

# ── 分頁設定 ───────────────────────────────────────────────
PAGE_SIZE = 100
total_rows = len(view_df)
total_pages = max(1, (total_rows + PAGE_SIZE - 1) // PAGE_SIZE)
if "page" not in st.session_state: st.session_state["page"] = 1
# 篩選條件變動時重置到第1頁
filter_key = f"{tab}_{search}_{cap_sel}_{idx_f}_{sel_sec}_{wma30_filter}_{wma30_weeks_range}_{fbos_filter}_{rs_range}_{day_range}_{roc1w_range}_{roc3m_range}_{roc6m_range}_{roc12m_range}_{eps_range}_{rev_range}_{gm_range}_{ni_range}_{vol_range}_{price_range}_{cap_range}_{dist_ath_range}_{dist_52h_range}_{sort_col}_{sort_asc}"
if st.session_state.get("filter_key") != filter_key:
    st.session_state["page"] = 1
    st.session_state["filter_key"] = filter_key
page = st.session_state["page"]

sortable=[("RS_pct","RS Rating"),("DayChange","當日漲幅"),("ROC_1W","近1週"),
          ("ROC_3M","3M"),("ROC_6M","6M"),("ROC_12M","12M"),
          ("EPS_QoQ","EPS季增"),("Rev_QoQ","營收季增"),("GrossMargin","毛利率"),
          ("NetIncome","淨利潤"),("VolRatio","成交量比"),("AvgDollarVol20","20D成交額"),("CapNum","市值"),("Price","股價"),
          ("DistATH","距ATH"),("Dist52H","距52W高"),("WMA30_Weeks","MA30事件")]
st.markdown("**點擊欄位排序：**")
btn_cols=st.columns(len(sortable))
for (ck,cl),bc in zip(sortable,btn_cols):
    is_act=st.session_state["sort_col"]==ck
    arrow=(" ↓" if not st.session_state["sort_asc"] else " ↑") if is_act else ""
    with bc:
        if st.button(f"{cl}{arrow}",key=f"sort_{ck}",type="primary" if is_act else "secondary",use_container_width=True):
            if st.session_state["sort_col"]==ck: st.session_state["sort_asc"]=not st.session_state["sort_asc"]
            else: st.session_state["sort_col"]=ck; st.session_state["sort_asc"]=False
            st.rerun()

header="""<div class="table-wrap"><table class="rs-table"><thead><tr>
<th>#</th><th>代碼</th><th>指數</th><th>當日漲幅</th>
<th>RS RATING</th><th>W&gt;MA30</th><th>W-MA30狀態</th><th>週首次破結構</th>
<th>近1週</th><th>3M ROC</th><th>6M ROC</th><th>12M ROC</th>
<th>EPS季增率</th><th>營收季增率</th><th>毛利率</th><th>淨利潤</th>
<th>成交量比均20天</th><th>20D成交額</th><th>距ATH</th><th>距52W高</th>
<th>PRICE</th><th>市值</th><th>SECTOR</th>
</tr></thead><tbody>"""

# 分頁切片
page_start = (page-1)*PAGE_SIZE
page_end   = min(page*PAGE_SIZE, total_rows)
page_df    = view_df.iloc[page_start:page_end]

rows=""
for rank_i,(_,r) in enumerate(page_df.iterrows(), page_start+1):
    sepa_b='<span class="sepa-badge">SEPA</span>' if r["SEPA"] else ""
    ticker=str(r["Ticker"])
    sec=str(r["Sector"]); sec="—" if sec in ("N/A","nan","None","") else sec[:18]
    rows+=(f'<tr>'
           f'<td style="color:#555">{rank_i}</td>'
           f'<td><span class="ticker-tag">{ticker}</span>{sepa_b}</td>'
           f'<td>{idx_col(r["Ticker"],sp500,ndx)}</td>'
           f'<td>{fmt_roc(r["DayChange"])}</td>'
           f'<td>{rs_bar(r["RS_pct"])}</td>'
           f'<td>{ma_badge(r["WeeklyMA30"])}</td>'
           f'<td>{fmt_wma30_status(r["WMA30_Status"],r["WMA30_Weeks"])}</td>'
           f'<td>{fmt_fbos(r["FBOS_Label"],r["FBOS_Weeks"],r["FBOS_SwingH"])}</td>'
           f'<td>{fmt_roc(r["ROC_1W"])}</td>'
           f'<td>{fmt_roc(r["ROC_3M"])}</td>'
           f'<td>{fmt_roc(r["ROC_6M"])}</td>'
           f'<td>{fmt_roc(r["ROC_12M"])}</td>'
           f'<td>{fmt_sig_val(r["EPS_QoQ"],r["EPS_Sig"],r["EPS_Accel"])}</td>'
           f'<td>{fmt_sig_val(r["Rev_QoQ"],r["Rev_Sig"],r["Rev_Accel"])}</td>'
           f'<td>{fmt_gm_sig(r["GrossMargin"],r["GM_Sig"],r["GM_Accel"])}</td>'
           f'<td>{fmt_ni_sig(r["NetIncome"],r["NI_Sig"],r["NI_Accel"])}</td>'
           f'<td>{fmt_vol_ratio(r["VolRatio"])}</td>'
           f'<td style="color:#888">{cap_fmt(r.get("AvgDollarVol20"))}</td>'
           f'<td>{fmt_ath(r["DistATH"],r["NearATH"])}</td>'
           f'<td>{fmt_52h(r["Dist52H"],r["Near52H"])}</td>'
           f'<td style="color:#e0e0e0">${r["Price"]}</td>'
           f'<td style="color:#555">{cap_fmt(r["CapNum"])}</td>'
           f'<td style="color:#555;font-size:11px">{sec}</td>'
           f'</tr>')

st.markdown(header+rows+"</tbody></table></div>",unsafe_allow_html=True)

# ── 分頁導航 ───────────────────────────────────────────────
st.markdown("<br>",unsafe_allow_html=True)
pc1,pc2,pc3,pc4,pc5=st.columns([1,1,2,1,1])
with pc1:
    if st.button("⏮ 首頁",disabled=page<=1,use_container_width=True):
        st.session_state["page"]=1; st.rerun()
with pc2:
    if st.button("◀ 上頁",disabled=page<=1,use_container_width=True):
        st.session_state["page"]=page-1; st.rerun()
with pc3:
    st.markdown(f'<div style="text-align:center;color:#888;padding-top:6px">第 {page} / {total_pages} 頁　共 {total_rows} 支</div>',unsafe_allow_html=True)
with pc4:
    if st.button("▶ 下頁",disabled=page>=total_pages,use_container_width=True):
        st.session_state["page"]=page+1; st.rerun()
with pc5:
    if st.button("⏭ 末頁",disabled=page>=total_pages,use_container_width=True):
        st.session_state["page"]=total_pages; st.rerun()
st.markdown("<br>",unsafe_allow_html=True)

detail_options=["—"]+view_df["Ticker"].tolist()
selected=st.selectbox(
    "🔍 選擇個股查看詳情",
    detail_options,
    label_visibility="visible",
)
if selected and selected!="—":
    row_data=view_df[view_df["Ticker"]==selected].iloc[0].to_dict()
    with st.expander(f"📋 {selected} 詳細分析",expanded=True):
        show_stock_detail(selected,hist_map.get(selected,pd.DataFrame()),
                         sepa_map.get(selected,{}),row_data,sp500,ndx)

show_tech_notes()

csv=view_df.drop(columns=[c for c in ["hist","SEPA_conds"] if c in view_df.columns]).to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ 下載 CSV",csv,f"rs_ranking_{today_str}.csv","text/csv")
