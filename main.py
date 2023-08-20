import MetaTrader5 as mt5
import pandas as pd
import time
import datetime

in_position = False
stop_loss = 00005.0
# ohlc variables
symbol = "[DJI30]"
timeframe = mt5.TIMEFRAME_M5
start_pos = 0
end_pos = 100
# bb variables
window_size = 20
num_std_dev = 2


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
    # Calcule la moyenne mobile simple (SMA)
    df['SMA'] = df['close'].rolling(window=window_size).mean()

    # Calcule l'écart type
    df['std_dev'] = df['close'].rolling(window=window_size).std()

    # Calcule les bandes de Bollinger supérieure et inférieure
    df['upper_band'] = df['SMA'] + num_std_dev * df['std_dev']
    df['lower_band'] = df['SMA'] - num_std_dev * df['std_dev']

    return df


while (in_position == False) and (is_market_open() == True):
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
        upper_wick = last_high - last_close
        lower_wick = last_open - last_low
    # Si bougie haussière
    else:
        upper_wick = last_high - last_open
        lower_wick = last_low - last_close

    # Utilisation de la fonction pour calculer les Bollinger Bands
    bollinger_bands_df = calculate_bollinger_bands(ohlc_df, window_size, num_std_dev)
    upper_band = round(bollinger_bands_df['upper_band'].iloc[-1], 2)
    lower_band = round(bollinger_bands_df['lower_band'].iloc[-1], 2)
    sma = round(bollinger_bands_df['SMA'].iloc[-2], 2)

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

    stopp = last_high + stop_loss
    tpp = last_close - sma
    print("STOP LOSS:", stopp)
    print("TAKE PROFIT:", last_close - sma * 2)

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
            upper_wick = last_high - last_close
            lower_wick = last_open - last_low
        # Si bougie haussière
        else:
            upper_wick = last_high - last_open
            lower_wick = last_low - last_close

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
                if last_close - sma * 2 >= sl:
                    # condition pour la plage horaire
                    print("on vend !")
                    in_position = True
                    break

    # position acheteuse
    elif last_close < lower_band:
        """
        oui
        """
    else:
        time.sleep(300)

while datetime.datetime.now() < datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month,
                                                  datetime.datetime.now().day, 21, 55):
    print("break even blablabla")
