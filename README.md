# thermometer
Thermometer server/client for Raspberry Pi


## Protocol Bufferのコンパイル
使用前に.protoファイルのコンパイルが必要です

```
% ./gen_proto.sh
```

## サーバサイド (Raspberry Pi)側プログラム

### Usage
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
                        Text file to be dumpped (default: None)
  -u, --udp             Enable UDP output (default: False)
  --udp_ip IP           UDP destinatio IP (default: <broadcast>)
  --udp_port Port       UDP destinatio port (default: 28012)
  -d DEVICE, --device DEVICE
                        DS18B20 ID(s). Find all device descriptors if omitted
                        (default: [])
```

### 使用例
#### 10秒毎に計測し、ローカルファイルに出力
```
% ./scripts/ds18b20_logger.py \
  -o therm_result.txt         \ # 出力ファイル名
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
