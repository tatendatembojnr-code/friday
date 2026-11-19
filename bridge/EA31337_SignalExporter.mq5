//+------------------------------------------------------------------+
//|                                    EA31337_SignalExporter.mq5    |
//|        Exports multi-indicator consensus to MQL5/Files for FRIDAY |
//+------------------------------------------------------------------+
#property copyright "Tatenda Tembo"
#property version   "1.00"
#property strict

input string InpOutputFile   = "ea31337_signals.json";
input int    InpPeriodFastMA = 20;
input int    InpPeriodSlowMA = 50;
input int    InpPeriodRSI    = 14;
input ENUM_TIMEFRAMES InpTF  = PERIOD_M15;

datetime g_last_bar = 0;

int OnInit()
{
   ExportSignals();
   return(INIT_SUCCEEDED);
}

void OnTick()
{
   datetime bar_time = iTime(_Symbol, InpTF, 0);
   if(bar_time != g_last_bar)
   {
      g_last_bar = bar_time;
      ExportSignals();
   }
}

void ExportSignals()
{
   int hFast = iMA(_Symbol, InpTF, InpPeriodFastMA, 0, MODE_EMA, PRICE_CLOSE);
   int hSlow = iMA(_Symbol, InpTF, InpPeriodSlowMA, 0, MODE_EMA, PRICE_CLOSE);
   int hRsi  = iRSI(_Symbol, InpTF, InpPeriodRSI, PRICE_CLOSE);
   int hMacd = iMACD(_Symbol, InpTF, 12, 26, 9, PRICE_CLOSE);

   double fast[], slow[], rsi[], macdMain[], macdSig[];
   if(CopyBuffer(hFast, 0, 1, 1, fast) <= 0) return;
   if(CopyBuffer(hSlow, 0, 1, 1, slow) <= 0) return;
   if(CopyBuffer(hRsi,  0, 1, 1, rsi)  <= 0) return;
   if(CopyBuffer(hMacd, 0, 1, 1, macdMain) <= 0) return;
   if(CopyBuffer(hMacd, 1, 1, 1, macdSig)  <= 0) return;

   int bull_votes = 0;
   int bear_votes = 0;
   string strats = "";

   if(fast[0] > slow[0]) { bull_votes++; strats += "\"EMA_Cross\","; }
   else if(fast[0] < slow[0]) { bear_votes++; strats += "\"EMA_Cross\","; }

   if(rsi[0] > 55.0) { bull_votes++; strats += "\"RSI_Momentum\","; }
   else if(rsi[0] < 45.0) { bear_votes++; strats += "\"RSI_Momentum\","; }

   if(macdMain[0] > macdSig[0]) { bull_votes++; strats += "\"MACD_Trend\","; }
   else if(macdMain[0] < macdSig[0]) { bear_votes++; strats += "\"MACD_Trend\","; }

   if(StringLen(strats) > 0)
      strats = StringSubstr(strats, 0, StringLen(strats) - 1);

   string bias = "NEUTRAL";
   int score = 50;
   if(bull_votes > bear_votes)
   {
      bias = "BULLISH";
      score = (int)MathRound((double)bull_votes / 3.0 * 100.0);
   }
   else if(bear_votes > bull_votes)
   {
      bias = "BEARISH";
      score = (int)MathRound((double)bear_votes / 3.0 * 100.0);
   }

   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   string ts = StringFormat("%04d-%02d-%02dT%02d:%02d:%02dZ",
                            dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec);

   string json = StringFormat(
      "{\n  \"%s\": {\n    \"bias\": \"%s\",\n    \"consensus_score\": %d,\n    \"active_strategies\": [%s],\n    \"timestamp\": \"%s\"\n  }\n}\n",
      _Symbol, bias, score, strats, ts
   );

   int handle = FileOpen(InpOutputFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, json);
      FileClose(handle);
   }
}
//+------------------------------------------------------------------+
