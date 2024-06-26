import datetime
import time
import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta

symbol = "[DJI30]"
in_position = False
stop_loss = 500.0  # Assuming stop_loss is 500 points (not 00005.0)
lot = 0.01
# Choose the deviation
deviation = 1
# ohlc variables
timeframe = mt5.TIMEFRAME_M5
start_pos = 0
end_pos = 100
# bb variables
window_size = 20
num_std_dev = 2.0


def send_order(symbol, lot, buy, sell, sl, tp, id_position, comment="", magic=0):
    # establish connection to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()

        # Initialize the bound between MT5 and Python
    mt5.initialize()

    """
    FILLING NE FONCTIONNE PAS SUR LE DOW
    -------------------------------------------------------
    # Extract filling_mode
    filling_type = mt5.symbol_info(symbol).filling_mode
    -------------------------------------------------------
    """


    """ OPEN A TRADE """
    if buy and id_position == None:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": mt5.symbol_info_tick(symbol).ask,
            "deviation": 10,
            "magic": magic,
            "comment": comment,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC,
            "sl": sl,
            "tp": tp,
        }
        print(mt5.order_send(request))
        result = mt5.order_send(request)
        return result

    if sell and id_position == None:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_SELL,
            "price": mt5.symbol_info_tick(symbol).bid,
            "deviation": 10,
            "magic": magic,
            "comment": comment,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC,
            "sl": sl,
            "tp": tp,
        }
        print(mt5.order_send(request))
        result = mt5.order_send(request)
        return result

    """ CLOSE A TRADE """
    if buy and id_position != None:
        request = {
            "position": id_position,
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_SELL,
            "price": mt5.symbol_info_tick(symbol).bid,
            "deviation": 10,
            "magic": magic,
            "comment": comment,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC},

        result = mt5.order_send(request)
        return result

    if sell and id_position != None:
        request = {
            "position": id_position,
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": mt5.symbol_info_tick(symbol).ask,
            "deviation": 10,
            "magic": magic,
            "comment": comment,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC}

        result = mt5.order_send(request)
        mt5.shutdown()
        return result


def is_market_open():
    now = datetime.datetime.now()
    market_open_time = now.replace(hour=14, minute=30, second=0, microsecond=0)
    market_close_time = now.replace(hour=18, minute=30, second=0, microsecond=0)

    if market_open_time <= now <= market_close_time:
        return True
    else:
        return False


def get_ohlc_data(symbol, timeframe, start_pos, end_pos):
    # Connexion à MetaTrader 5
    if not mt5.initialize():
        print("initialize() a échoué")
        return

    # Récupère les données OHLC du Dow Jones
    dow_data = mt5.copy_rates_from_pos(symbol, timeframe, start_pos, end_pos)

    # Ferme la connexion à MetaTrader 5
    mt5.shutdown()

    # Convertit les données en DataFrame pandas
    df = pd.DataFrame(dow_data)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    # Sélectionne uniquement les colonnes OHLC
    df = df[['open', 'high', 'low', 'close']]

    return df


def calculate_bollinger_bands(df, window_size, num_std_dev):
    # Calculer les bandes de Bollinger en utilisant pandas_ta
    bollinger_bands = ta.bbands(df['close'], length=window_size, std=num_std_dev)

    # Ajouter les bandes de Bollinger au DataFrame
    df['upper_band'] = bollinger_bands['BBU_20_2.0']
    df['middle_band'] = bollinger_bands['BBM_20_2.0']
    df['lower_band'] = bollinger_bands['BBL_20_2.0']

    return df

def checking_for_position():
    global in_position
    # if market is close
    """ and (is_market_open() == True)"""
    while (in_position == False):
        """
        # Attendre que le dernier chiffre des minutes soit 0 ou 5
        print("Attente que la dernière chiffre des minutes soit un 5 ou un 0...")
        while True:
            current_time = datetime.datetime.now()
            last_digit_of_minute = current_time.minute % 10
    
            if last_digit_of_minute == 0 or last_digit_of_minute == 5:
                if current_time.second == 0:
                    print("La dernière chiffre des minutes est un 5 ou un 0. Commencement de la boucle !")
                    break
            else:
                time.sleep(1)  # Attendre 1 seconde
                
        """

        # collect new data for the new candle
        ohlc_df = get_ohlc_data(symbol, timeframe, start_pos, end_pos)
        last_open = ohlc_df['open'].iloc[-2]
        last_close = ohlc_df['close'].iloc[-2]
        last_high = ohlc_df['high'].iloc[-2]
        last_low = ohlc_df['low'].iloc[-2]

        last_body = last_open - last_close

        # Si bougie baissière
        if last_body < 0:
            last_body = abs(last_body)
            upper_wick = last_high - last_open
            lower_wick = last_close - last_low
        # Si bougie haussière
        else:
            upper_wick = last_high - last_close
            lower_wick = last_open - last_low

        # Utilisation de la fonction pour calculer les Bollinger Bands
        # bollinger_bands_df = calculate_bollinger_bands(ohlc_df, window_size, num_std_dev)
        # upper_band = round(bollinger_bands_df['upper_band'].iloc[-1], 2)
        # lower_band = round(bollinger_bands_df['lower_band'].iloc[-1], 2)
        # sma = round(bollinger_bands_df['SMA'].iloc[-2], 2)

        bollinger_bands_df = calculate_bollinger_bands(ohlc_df, window_size, num_std_dev)

        lower_band = round(bollinger_bands_df['lower_band'].iloc[-1], 2)
        sma = round(bollinger_bands_df['middle_band'].iloc[-2], 2)
        upper_band = round(bollinger_bands_df['upper_band'].iloc[-1], 2)

        print("Fermeture de la dernière bougie en M5 :")
        print("higher:", last_high)
        print("lower:", last_low)
        print("open:", last_open)
        print("Close:", last_close)
        print("body:", last_body)
        print("upper wick:", upper_wick)
        print("lower wick", lower_wick)

        print("\nBollinger Bands pour la dernière bougie en 5 minutes :")
        print("Bande haute:", upper_band)
        print("Bande basse:", lower_band)
        print("Moyenne mobile:", sma)
        # --------------------------------------------------------------
        # sl = last_high + stop_loss

        # sell order
        # send_order(symbol, lot, False, True, sl, sma, None, "sell order", 0)
        #---------------------------------------------------------------

        # Vérifie si la dernière bougie en M5 sort des bandes supérieure ou inférieure

        # position vendeuse
        if last_close > upper_band:
            # Attendre 5 minutes avant de récupérer les nouvelles données (signal)
            time.sleep(300)

            # collect new data for the new candle
            ohlc_df = get_ohlc_data(symbol, timeframe, start_pos, end_pos)
            last_open = ohlc_df['open'].iloc[-2]
            last_close = ohlc_df['close'].iloc[-2]
            last_high = ohlc_df['high'].iloc[-2]
            last_low = ohlc_df['low'].iloc[-2]

            last_body = last_open - last_close

            # Si bougie baissière
            if last_body < 0:
                last_body = abs(last_body)
                upper_wick = last_high - last_open
                lower_wick = last_close - last_low
            # Si bougie haussière
            else:
                upper_wick = last_high - last_close
                lower_wick = last_open - last_low

            # Utilisation de la fonction pour calculer les Bollinger Bands
            bollinger_bands_df = calculate_bollinger_bands(ohlc_df, window_size, num_std_dev)
            upper_band = round(bollinger_bands_df['upper_band'].iloc[-1], 2)
            lower_band = round(bollinger_bands_df['lower_band'].iloc[-1], 2)
            sma = round(bollinger_bands_df['SMA'].iloc[-2], 2)

            # condition pour avoir un marteau (signal d'entrée)
            if ((upper_wick * 3 >= last_body) and (lower_wick <= last_body)) or (
                    (lower_wick * 3 >= last_body) and (upper_wick <= last_body)):
                # condition pour que le marteau ne touche pas la bande supérieur des BB
                if not ((last_low <= upper_band) or (last_close <= upper_band)):
                    # condition pour que le RR >=2
                    sl = last_high + stop_loss
                    tp = last_close - sma * 2
                    if tp >= sl:
                        send_order(symbol, lot, False, True, sl, sma, None, "sell order", 0)
                        in_position = True
                        return

        # position acheteuse
        elif last_close < lower_band:
            # Attendre 5 minutes avant de récupérer les nouvelles données (signal)
            time.sleep(300)

            # collect new data for the new candle
            ohlc_df = get_ohlc_data(symbol, timeframe, start_pos, end_pos)
            last_open = ohlc_df['open'].iloc[-2]
            last_close = ohlc_df['close'].iloc[-2]
            last_high = ohlc_df['high'].iloc[-2]
            last_low = ohlc_df['low'].iloc[-2]

            last_body = last_open - last_close

            # Si bougie baissière
            if last_body < 0:
                last_body = abs(last_body)
                upper_wick = last_high - last_open
                lower_wick = last_close - last_low
            # Si bougie haussière
            else:
                upper_wick = last_high - last_close
                lower_wick = last_open - last_low

            # Utilisation de la fonction pour calculer les Bollinger Bands
            bollinger_bands_df = calculate_bollinger_bands(ohlc_df, window_size, num_std_dev)
            upper_band = round(bollinger_bands_df['upper_band'].iloc[-1], 2)
            lower_band = round(bollinger_bands_df['lower_band'].iloc[-1], 2)
            sma = round(bollinger_bands_df['SMA'].iloc[-2], 2)

            # condition pour avoir un marteau (signal d'entrée)
            if ((upper_wick * 3 >= last_body) and (lower_wick <= last_body)) or (
                    (lower_wick * 3 >= last_body) and (upper_wick <= last_body)):
                # condition pour que le marteau ne touche pas la bande inférieure des BB
                if not ((last_high >= lower_band) or (last_close >= lower_band)):
                    # condition pour que le RR >=2
                    sl = last_low - stop_loss
                    tp = last_close + sma * 2
                    if tp >= sl:
                        # Place buy order
                        send_order(symbol, lot, True, False, sl, sma, None, "buy order", 0)
                        in_position = True
                        return
        # est-ce que le prog attends la prochaine bougie 5min ?
        else:
            time.sleep(240)  # Attendre 4min #MAX FAIS MIEUX STP

checking_for_position()

if in_position:

    print("break even blablabla")

# CLOSE AUTOMATICALLY
# while datetime.datetime.now() < datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month,
#                                                   datetime.datetime.now().day, 21, 55):
#     print("ordre de fermeture de position")

# TODO:
#      - to fix timing between the 5min candles to collect datas
#      - in position (modif ordre SL -> BE == niveau d'entrée)
#      - close automatically (close position)
