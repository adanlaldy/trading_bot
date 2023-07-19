# 1st condition : condition si une bougie cloture en dehors des bandes BB -> verification si signal (marteau)
import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt

# connexion à MetaTrader 5
if not mt5.initialize():
    print("initialize() a échoué")
    mt5.shutdown()

# demande l'état et les paramètres de connexion
print(mt5.terminal_info())
# récupère les données sur la version MetaTrader 5
print(mt5.version())

# Symbol du Dow Jones (ou tout autre actif que vous souhaitez analyser)
symbol = "EURUSD"  # <----- pas d'accès au DJ sur mt5

# Récupère les données du Dow Jones
dow_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)

# ferme la connexion à MetaTrader 5
mt5.shutdown()

# Convertit les données en DataFrame pandas
df = pd.DataFrame(dow_data)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.set_index('time', inplace=True)

# Calcul des bandes de Bollinger
window = 20  # Fenêtre de calcul pour la moyenne mobile et l'écart-type
df['rolling_mean'] = df['close'].rolling(window=window).mean()
df['rolling_std'] = df['close'].rolling(window=window).std()
df['upper_band'] = df['rolling_mean'] + 2 * df['rolling_std']
df['lower_band'] = df['rolling_mean'] - 2 * df['rolling_std']

# Tracer le graphique avec les bandes de Bollinger
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['close'], label='Dow Jones')
plt.plot(df.index, df['upper_band'], label='Upper Bollinger Band')
plt.plot(df.index, df['lower_band'], label='Lower Bollinger Band')
plt.fill_between(df.index, df['upper_band'], df['lower_band'], alpha=0.2)
plt.xlabel('Date')
plt.ylabel('Prix')
plt.title('Graphique Dow Jones avec les bandes de Bollinger')
plt.legend()
plt.show()

# TODO:
#  - Récupérer les données du Dow Jones en 5 minutes
#  - Modifier le graphique pour avoir des chandeliers japonais
#  - Faire une boucle pour que le programme continue tant que la condition n'est pas remplie
