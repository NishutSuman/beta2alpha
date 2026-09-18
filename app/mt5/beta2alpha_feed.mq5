//+------------------------------------------------------------------+
//|  beta2alpha_feed.mq5                                              |
//|  Pushes live XAU/USD candles (5m,15m,1h,1d) from MetaTrader 5     |
//|  to the beta2alpha backend. DATA-ONLY: it places NO trades.       |
//|                                                                   |
//|  SETUP:                                                           |
//|   1. Tools > Options > Expert Advisors >                          |
//|        tick "Allow WebRequest for listed URL"                     |
//|        add:  http://127.0.0.1:8011                                |
//|   2. Attach this EA to an XAUUSD chart (any timeframe).           |
//|   3. Allow Algo Trading (the EA does not trade — only reads).     |
//+------------------------------------------------------------------+
#property strict

input string BackendURL  = "http://127.0.0.1:8011/api/mt5/candles";
input string FeedSymbol  = "";     // blank = use the chart's symbol (attach to gold)
input int    PushSeconds = 10;     // push interval (seconds)

ENUM_TIMEFRAMES TFS[4]  = {PERIOD_M5, PERIOD_M15, PERIOD_H1, PERIOD_D1};
string          TFN[4]  = {"5m", "15m", "1h", "1d"};
int             BARS[4] = {500, 1500, 1500, 1000};   // smaller 5m payload = reliable push

string Sym() { return (FeedSymbol == "" ? _Symbol : FeedSymbol); }

int OnInit()
{
   EventSetTimer(PushSeconds);
   PushAll();
   Print("beta2alpha_feed started for ", Sym(), " -> ", BackendURL);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) { EventKillTimer(); }
void OnTimer() { PushAll(); }

void PushAll()
{
   long serverMinusGmt = (long)(TimeTradeServer() - TimeGMT());  // broker server offset from GMT
   for(int i = 0; i < 4; i++)
      PushTF(TFS[i], TFN[i], BARS[i], serverMinusGmt);
}

void PushTF(ENUM_TIMEFRAMES tf, string name, int bars, long serverMinusGmt)
{
   MqlRates r[];
   ArraySetAsSeries(r, true);
   int n = CopyRates(Sym(), tf, 0, bars, r);
   if(n <= 0) return;

   string js = "{\"tf\":\"" + name + "\",\"candles\":[";
   for(int k = n - 1; k >= 0; k--)               // oldest -> newest
   {
      long utc = (long)r[k].time - serverMinusGmt;
      js += "{\"time\":" + IntegerToString(utc)
          + ",\"open\":"  + DoubleToString(r[k].open, 2)
          + ",\"high\":"  + DoubleToString(r[k].high, 2)
          + ",\"low\":"   + DoubleToString(r[k].low, 2)
          + ",\"close\":" + DoubleToString(r[k].close, 2)
          + ",\"volume\":" + IntegerToString((long)r[k].tick_volume) + "}";
      if(k > 0) js += ",";
   }
   js += "]}";
   SendJSON(js);
}

void SendJSON(string js)
{
   char post[];
   int len = StringToCharArray(js, post, 0, -1, CP_UTF8);
   if(len > 0) ArrayResize(post, len - 1);       // drop trailing null

   char result[];
   string rheaders;
   string headers = "Content-Type: application/json\r\n";
   int res = WebRequest("POST", BackendURL, headers, 10000, post, result, rheaders);
   if(res == -1)
      Print("WebRequest failed err=", GetLastError(),
            " — add ", BackendURL, " in Tools>Options>Expert Advisors>Allow WebRequest");
}
//+------------------------------------------------------------------+
