# thermometer
Thermometer server/client for Raspberry Pi


## 必要パッケージ
* protobuf
* matplotlib
* numpy

## Protocol Bufferのコンパイル
使用前に.protoファイルのコンパイルが必要です

```
% ./gen_proto.sh
```

## サーバ (Raspberry Pi)側プログラム

### scripts/ds18b20_logger.py Usage
```
usage: ds18b20_logger.py [-h] [-m] [-t seconds] [-i seconds] [-o text_file]
                         [-u] [--udp_ip IP] [--udp_port Port] [-d DEVICE]

optional arguments:
  -h, --help            show this help message and exit
  -m, --modprobe        modprobe w1-gpio/w1-therm (default: False)
  -t seconds, --time seconds
                        Set logging time (-1: no timeout) (default: 0.1)
  -i seconds, --interval seconds
                        Sampling Time (default: 1)
  -o text_file, --output text_file
                        Text file to be dumpped.(default: None)
                        Create a file from date and time if a directory is specifed.
  -u, --udp             Enable UDP output (default: False)
  --udp_ip IP           UDP destination IP (default: <broadcast>)
  --udp_port Port       UDP destination port (default: 28012)
  -d DEVICE, --device DEVICE
                        DS18B20 ID(s). Find all device descriptors if omitted
                        (default: [])
```

### 使用例
#### 10秒毎に計測し、ローカルファイルに出力
```
% ./scripts/ds18b20_logger.py \
  -o therm_result.csv         \ # 出力ファイル名
  -i 10                       \ # 計測インターバル
  -t -1                         # 無限に計測
```

#### ローカルフォルダに日付ファイルを作成して出力
```
% ./scripts/ds18b20_logger.py \
  -o log                      \ # logフォルダに日付名でファイルを作成
  -i 10                       \ # 計測インターバル
  -t -1                         # 無限に計測
```

#### 30秒毎に計測し、UDPにブロードキャスト
```
% ./scripts/ds18b20_logger.py \
  --udpd                      \ # UDPに送信。デフォルトはブロードキャスト
  -i 30                       \ # 計測インターバル
  -t -1                         # 無限に計測
```


## クライアント (ホスト)側プログラム

### scripts/ds18b20_client.py Usage
```
usage: ds18b20_client.py [-h] [-i File] [-p] [--csv File] [--udp_ip IP]
                         [--udp_port Port]

optional arguments:
  -h, --help            show this help message and exit
  -i File, --input File
                        Read a recorded data instead of UDP (UDP option is
                        disabled) (default: None)
  -p, --plot            Plot sensed values (default: False)
  --csv File            Output to CSV file (default: None)
  --udp_ip IP           UDP destination IP (0.0.0.0 means any) (default: 0.0.0.0)
  --udp_port Port       UDP destination port (default: 28012)
```

### 使用例
#### UDPで受信したデータをCSVに保存
```
% ./scripts/ds18b20_client.py \
  --csv therm_result.csv         # 出力ファイル名
```

#### UDPで受信したデータをリアルタイムでプロット
```
% ./scripts/ds18b20_client.py \
  -p                             # プロット出力
```

#### 保存したCSVファイルをプロット
```
% ./scripts/ds18b20_client.py \
  -i therm_result.csv           # CSVファイル読み込み
```
