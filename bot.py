import os,requests,time,json,threading
from datetime import datetime
TOKEN="8759300648:AAGkTxZc_tRon-UKwAaagtmJZefnDrdvj9I"
API=f"https://api.telegram.org/bot{TOKEN}"
subscribers=set()
price_history=[]
signal_history=[]
def get_price():
 try:
  r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X?interval=1m&range=1d",timeout=10)
  d=r.json()['chart']['result'][0]
  p=d['meta']['regularMarketPrice']
  return{"price":round(p,2),"high":round(d['meta']['regularMarketDayHigh'],2),"low":round(d['meta']['regularMarketDayLow'],2),"change":round(p-d['meta']['previousClose'],2),"pct":round((p-d['meta']['previousClose'])/d['meta']['previousClose']*100,2)}
 except:return None
def calc_rsi(p,n=14):
 if len(p)<n+1:return 50
 g,l=[],[]
 for i in range(1,len(p)):
  d=p[i]-p[i-1];g.append(max(d,0));l.append(max(-d,0))
 ag=sum(g[-n:])/n;al=sum(l[-n:])/n
 return 50 if al==0 else round(100-(100/(1+ag/al)),1)
def calc_ma(p,n):return round(sum(p[-n:])/n,2) if len(p)>=n else None
def get_signal(price,rsi,ma20,ma50):
 s=0
 if rsi<30:s+=2
 elif rsi<40:s+=1
 elif rsi>70:s-=2
 elif rsi>60:s-=1
 if ma20 and ma50:s+=1 if ma20>ma50 else -1
 if s>=2:return"BUY","🟢",round(price+20,2),round(price-10,2)
 elif s<=-2:return"SELL","🔴",round(price-20,2),round(price+10,2)
 return"KUTISH","⏸","--","--"
def send(chat_id,text,markup=None):
 p={"chat_id":chat_id,"text":text,"parse_mode":"HTML"}
 if markup:p["reply_markup"]=json.dumps(markup)
 try:requests.post(f"{API}/sendMessage",json=p,timeout=10)
 except:pass
def menu():
 return{"keyboard":[["📊 Signal","💰 Narx"],["🤖 AI Tahlil","📈 To'liq tahlil"],["⚡ Auto yoq/o'ch","📋 Tarix"],["ℹ️ Yordam"]],"resize_keyboard":True}
def analyze(chat_id):
 d=get_price()
 if not d:send(chat_id,"❌ Narx olib bo'lmadi.");return
 price=d['price'];price_history.append(price)
 if len(price_history)>50:price_history.pop(0)
 rsi=calc_rsi(price_history);ma20=calc_ma(price_history,20);ma50=calc_ma(price_history,50)
 trend="📈 YUQORI" if len(price_history)>=5 and price>price_history[-5] else "📉 PAST"
 sig,em,tp,sl=get_signal(price,rsi,ma20,ma50)
 e="▲" if d['change']>=0 else "▼"
 now=datetime.now().strftime("%d.%m.%Y %H:%M")
 msg=(f"🥇 <b>XAU/USD</b> | {now}\n\n"
  f"💰 Narx: <b>${price}</b> {e}{d['change']} ({d['pct']}%)\n"
  f"📈 High: ${d['high']} | 📉 Low: ${d['low']}\n\n"
  f"📊 RSI: <b>{rsi}</b> | Trend: <b>{trend}</b>\n"
  f"MA20: <b>{ma20 or'--'}</b> | MA50: <b>{ma50 or'--'}</b>\n\n"
  f"🎯 Signal: <b>{em} {sig}</b>\n"
  f"✅ TP: <b>{tp}</b> | 🛑 SL: <b>{sl}</b>\n\n"
  f"⚠️ <i>Moliyaviy maslahat emas!</i>")
 send(chat_id,msg)
 if sig!="KUTISH":
  signal_history.insert(0,{"time":datetime.now().strftime("%H:%M"),"signal":sig,"price":price,"tp":tp,"sl":sl})
  if len(signal_history)>20:signal_history.pop()
def auto_loop():
 while True:
  time.sleep(300)
  if not subscribers:continue
  d=get_price()
  if not d:continue
  price=d['price'];price_history.append(price)
  if len(price_history)>50:price_history.pop(0)
  rsi=calc_rsi(price_history);ma20=calc_ma(price_history,20);ma50=calc_ma(price_history,50)
  trend="📈 YUQORI" if len(price_history)>=5 and price>price_history[-5] else "📉 PAST"
  sig,em,tp,sl=get_signal(price,rsi,ma20,ma50)
  if sig=="KUTISH":continue
  now=datetime.now().strftime("%H:%M")
  msg=(f"🔔 <b>AVTOMATIK SIGNAL</b> | {now}\n\n"
   f"💰 XAU/USD: <b>${price}</b>\n"
   f"📊 RSI: {rsi} | {trend}\n\n"
   f"🎯 <b>{em} {sig}</b>\n"
   f"✅ TP: <b>{tp}</b> | 🛑 SL: <b>{sl}</b>\n\n"
   f"⚠️ <i>Moliyaviy maslahat emas!</i>")
  for s in list(subscribers):send(s,msg)
def main():
 print("XAUBot ishga tushdi!")
 threading.Thread(target=auto_loop,daemon=True).start()
 offset=0
 while True:
  try:
   r=requests.get(f"{API}/getUpdates?offset={offset}&timeout=30",timeout=35)
   updates=r.json().get("result",[])
  except:time.sleep(3);continue
  for u in updates:
   offset=u["update_id"]+1
   msg=u.get("message",{});chat_id=msg.get("chat",{}).get("id");text=msg.get("text","")
   if not chat_id or not text:continue
   if text in["/start","boshlash"]:send(chat_id,"🥇 <b>XAU/USD Signal Bot</b>\n\nAssalomu alaykum!\n\n📌 Tugmalardan foydalaning 👇",menu())
   elif text in["📊 Signal","/signal"]:analyze(chat_id)
   elif text in["💰 Narx","/narx"]:
    d=get_price()
    if d:send(chat_id,f"💰 <b>XAU/USD</b>\n\n${d['price']} {'▲' if d['change']>=0 else '▼'}{d['change']} ({d['pct']}%)\n📈 {d['high']} | 📉 {d['low']}")
   elif text in["📈 To'liq tahlil","/tahlil","🤖 AI Tahlil"]:analyze(chat_id)
   elif text in["⚡ Auto yoq/o'ch","/auto"]:
    if chat_id in subscribers:subscribers.remove(chat_id);send(chat_id,"⏹ Auto signal O'CHIRILDI",menu())
    else:subscribers.add(chat_id);send(chat_id,"✅ Auto signal YOQILDI!\nHar 5 daqiqada signal olasiz.",menu())
   elif text in["📋 Tarix","/tarix"]:
    if not signal_history:send(chat_id,"📋 Hali signal yo'q.")
    else:
     m="📋 <b>Signal tarixi:</b>\n\n"
     for h in signal_history[:10]:m+=f"{'🟢' if h['signal']=='BUY' else '🔴'} {h['time']} ${h['price']} TP:{h['tp']}\n"
     send(chat_id,m)
   elif text in["ℹ️ Yordam","/help"]:send(chat_id,"ℹ️ <b>Yordam</b>\n\n📊 Signal - BUY/SELL\n💰 Narx - Hozirgi narx\n📈 Tahlil - To'liq tahlil\n⚡ Auto - Avtomatik signal\n📋 Tarix - Oldingi signallar\n\n⚠️ Moliyaviy maslahat emas!",menu())
  time.sleep(1)
if __name__=="__main__":main()
