import time
import datetime
import gdax
import csv
import pandas as pd
import matplotlib.pyplot as plt
import quandl


class Data:

    # This is a dataframe stored as a CSV
    _file = 'data.csv'
    _passphrase = 'xxxxxxxx'
    _API_Key = 'xxxxxxxx'
    _API_Secret = 'xxxxxxxx'

    def __init__(self, csv_file='', ticker_name='', start_unix=1420070400, end_unix=int(time.time()), resample_s=1):
        if csv_file != '':
            df = pd.read_csv(csv_file, parse_dates=False)
            df.to_csv(self._file, index=False)
            self.csv_reformat(resample_s)

        elif ticker_name != '':
            auth_client = gdax.AuthenticatedClient(self._API_Key, self._API_Secret, self._passphrase)

            data = open(self._file, 'a')  # w is for write, a is for append
            i = end_unix

            missed_data_count = 0
            while i > start_unix:
                reply_from_server = auth_client.get_product_historic_rates(ticker_name, str(
                    datetime.datetime.utcfromtimestamp(i).isoformat() + '+00:00'),
                                                                           str(datetime.datetime.utcfromtimestamp(
                                                                               i + 199 * 60).isoformat() + '+00:00'),
                                                                           '60')
                for candle_data in reply_from_server:
                    if candle_data != 'message':
                        candle_data = str(candle_data).replace('[', '')
                        candle_data = str(candle_data).replace(']', '')
                        data.write('\n' + str(candle_data))
                    else:
                        missed_data_count += 1
                        print('missed Data')

                i -= 12000
                print(i)
                time.sleep(0.5)
            data.close()
            print(missed_data_count)
        else:
            df = pd.DataFrame(columns=['Time', 'Low', 'High', 'Open', 'Close', 'Volume'])
            df.to_csv(self._file, index=False)

    # Downsamples data to selected resample period (in seconds) and creates a new file
    def csv_reformat(self, resample_s=1):
        df = pd.read_csv(self._file, parse_dates=False)
        df_resampled = pd.DataFrame(columns=['Time', 'Low', 'High', 'Open', 'Close', 'Volume'])
        if resample_s != 1:
            curr_time = df.loc[0, 'Time']
            for i in range(len(df)):
                if abs(curr_time - df.loc[i, 'Time']) >= resample_s:
                    curr_time = df.loc[i, 'Time']
                    df_resampled = df_resampled.append(df.iloc[[i]])
            df = df_resampled
        df.to_csv(self._file, index=False)

    # Plots a matplotlib graph of the data object
    def plot_graph(self, close=False, minim=False, maxim=False, min_value=False, max_value=False, buy_sell=False, rsi=False):

        df = pd.read_csv(self._file, parse_dates=False)

        ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=5, colspan=1)
        ax2 = plt.subplot2grid((6, 1), (5, 0), rowspan=5, colspan=1, sharex=ax1)

        if 'Close' in df and close:
            ax1.plot(df['Time'], df['Close'])
        if 'Min' in df and minim:
            ax1.scatter(df.index, df['Min'], c='r')
        if 'Max' in df and maxim:
            ax1.scatter(df.index, df['Max'], c='g')
        if 'MinValue' in df and min_value:
            ax2.plot(df['Time'], df['MinValue'], c='r')
        if 'MaxValue' in df and max_value:
            ax2.plot(df['Time'], df['MaxValue'], c='g')
        if 'Buy/Sell' in df and buy_sell:
            ax2.plot(df['Time'], df['Buy/Sell'])
        if 'RSI' in df and rsi:
            ax2.plot(df['Time'], df['RSI'])

        plt.show()

    # Iterates over data and returns the number of missing dates
    def find_missing_data(self, time_step=1000):
        df = pd.read_csv(self._file, parse_dates=False)
        curr_unix_time = time.time()
        missing_entry_count = 0
        entry_found = False

        for i in range(len(df)):
            if abs(df.loc[i, 'Time']-curr_unix_time) > time_step:
                curr_unix_time = df.loc[i, 'Time']
                if not entry_found:
                    missing_entry_count += 1
                else:
                    entry_found = False
            else:
                entry_found = True

        return missing_entry_count

    # Calculates the rsi and adds a column for it, only works with old to recent times
    def calc_rsi(self, n=14, based_on='Close'):
        df = pd.read_csv(self._file, parse_dates=False)
        df['RSI'] = 0.5
        df['Change'] = 0
        df['Change'] = df[based_on] - df[based_on].shift(-1)
        init_total_gain = 0
        init_total_loss = 0

        for j in range(n):
            if df.loc[n - j, 'Change'] > 0:
                init_total_gain += df.loc[n - j, 'Change']
            else:
                init_total_loss -= df.loc[n - j, 'Change']

        init_average_gain = init_total_gain / n
        init_average_loss = init_total_loss / n
        if init_average_loss == 0:
            init_rsi = 1
        else:
            init_rs = init_average_gain / init_average_loss
            init_rsi = (100 - (100 / (1 + init_rs))) / 100
        df.loc[n, 'RSI'] = init_rsi

        prev_avrg_gain = init_average_gain
        prev_avrg_loss = init_average_loss
        for i in range(n + 1, len(df)):
            if df.loc[i, 'Change'] > 0:
                prev_avrg_gain = ((prev_avrg_gain * (n-1)) + df.loc[i, 'Change']) / n
                prev_avrg_loss = ((prev_avrg_loss * (n-1)) / n)
            else:
                prev_avrg_gain = ((prev_avrg_gain * (n-1)) / n)
                prev_avrg_loss = ((prev_avrg_loss * (n-1)) - df.loc[i, 'Change']) / n
            rs = prev_avrg_gain / prev_avrg_loss
            rsi = (100 - (100 / (1 + rs))) / 100
            df.loc[i, 'RSI'] = rsi
        del df['Change']
        df.to_csv(self._file, index=False)

    # Adds columns RSI and Buy/Sell, Buy/Sell = 1 is buy all, =-1 is sell all
    def rsi_bot(self, n=14, buy_rsi=0.3, sell_rsi=0.7, init_holding_fiat=True):
        df = pd.read_csv(self._file, parse_dates=False)
        self.calc_rsi(n=n)
        df['Buy/Sell'] = 0
        holding_fiat = init_holding_fiat
        for i in range(len(df)):
            if (not holding_fiat) and df.loc[i, 'RSI'] > sell_rsi:
                df.loc[i, 'Buy/Sell'] = -1.0
                holding_fiat = True
            elif holding_fiat and df.loc[i, 'RSI'] < buy_rsi:
                df.loc[i, 'Buy/Sell'] = 1.0
                holding_fiat = False
        df.to_csv(self._file, index=False)

    # Tests an algorithm based and returns the assets at the end of the test
    def back_test(self, init_crypto=0, init_fiat=100):
        df = pd.read_csv(self._file, parse_dates=False)
        curr_crypto = init_crypto
        curr_fiat = init_fiat
        for i in range(len(df)):
            if df.loc[i, 'Buy/Sell'] != 0:
                if df.loc[i, 'Buy/Sell'] > 0:
                    curr_crypto += (curr_fiat*df.loc[i, 'Buy/Sell'])/df.loc[i, 'Close']
                    curr_fiat -= (curr_fiat*df.loc[i, 'Buy/Sell'])
                else:
                    curr_fiat -= (curr_crypto * df.loc[i, 'Buy/Sell']) * df.loc[i, 'Close']
                    curr_crypto += (curr_crypto*df.loc[i, 'Buy/Sell'])
        df.to_csv(self._file, index=False)
        return curr_fiat, curr_crypto

    # Identifies the minima and maxima of the graph and assigns values to how min and max they are
    def min_max_values(self):
        df = pd.read_csv(self._file, parse_dates=False)
        df['MinValue'] = 0
        df['MaxValue'] = 0

        prev_min = 0
        next_min = 0
        prev_max = 0
        next_max = 0

        for i in range(len(df)):
            print(i)
            curr_value = df.loc[i, 'Close']

            for j in list(range(i)[::-1]):
                prev_min = 0
                if curr_value > df.loc[j, 'Close']:
                    prev_min = j
                    break
            for k in range(i, len(df)):
                next_min = 0
                if curr_value > df.loc[k, 'Close']:
                    next_min = k-i
                    break

            for j in list(range(i)[::-1]):
                prev_max = 0
                if curr_value < df.loc[j, 'Close']:
                    prev_max = j
                    break
            for k in range(i, len(df)):
                next_max = 0
                if curr_value < df.loc[k, 'Close']:
                    next_max = k-i
                    break

            df.loc[i, 'MinValue'] = prev_min * next_min
            df.loc[i, 'MaxValue'] = prev_max * next_max

            df.to_csv(self._file, index=False)

def main():

    sec_obj = Data(csv_file='data.csv')
    sec_obj.min_max_values()
    # sec_obj.calc_rsi()
    # sec_obj.rsi_bot()
    # print(sec_obj.back_test())
    sec_obj.plot_graph(close=True, max_value=True)



if __name__ == "__main__":
    main()


# To do:
#   Get Min Max values working, and make it based on time
#   Import financial library
#   Adaptive plotting, add subplots for different things
#