# CSV2G

CSV2Gは、CSVファイルのデータを解析し、グラフを作成するPythonアプリケーションです。主に電圧と時間のデータを用いた解析を行い、ステップ応答の検出も行います。

## 機能

- CSVファイルを読み込み、指定された列を解析
- 移動平均によるノイズ除去
- ベースラインからの電圧変化を検出、原点として使用可能
- ステップ応答の判別
- グラフの作成と保存,及び表示

## 使い方

1. このプロジェクトをクローンまたはダウンロードします。
2. 必要な依存関係をインストールします。
   ```bash
   pip install -r requirements.txt
3. アプリケーションを実行します。
   ```bash
   python csv2g-nogui.py
   ```
   または   
   ```bash
   python csv2g-gui.py
   ```
4. GUIからCSVファイルを選択し、解析を実行します。

## 必要なライブラリ
- pandas
- numpy
- matplotlib
- Pillow
- tkinter

依存関係は、requirements.txtに記載されています。

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。詳細はLICENSEファイルを参照してください。

## 作者

三ツ井雅翔（連絡先：[ee224131@meiji.ac.jp],[widwmitsui@gmail.com]）
