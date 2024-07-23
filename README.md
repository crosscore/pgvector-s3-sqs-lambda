# rag-pgvector

1. ファイルハッシュの計算と検証を導入し、同一ファイルの重複ダウンロードを防ぎます。
2. 一時ファイルを使用してダウンロードを行い、成功した場合のみ正式なファイル名に変更します。これにより、部分的なダウンロードによる問題を防ぎます。
3. データベースを使用して、成功したダウンロードの記録を保持します。これにより、プログラムが再起動しても以前のダウンロード状態を把握できます。
4. エラーハンドリングを強化し、予期せぬ例外が発生した場合にもグレースフルに処理します。
5. データベース操作にトランザクションを使用し、データの一貫性を保ちます。

冪等性：同じメッセージを複数回処理しても、結果は同じになります。
耐障害性：部分的なダウンロードや予期せぬエラーに対して適切に対処します。
一貫性：データベースを使用して処理状態を追跡し、重複処理を防ぎます。


AWS Lambdaで使用するzipファイルアーカイブを50MB以内に収める:
1. プロジェクトディレクトリを作成し、そこに移動します。
2. venvを作成し、アクティベートします：

```bash
python3 -m venv lambda_env
source lambda_env/bin/activate  # Linuxの場合
```

3. 必要なライブラリをインストールします：

```bash
pip install -r requirements.txt
```

4. Lambdaに必要なファイルをコピーします：

```bash
mkdir lambda_package
cp pdf_to_pgvector.py config.py lambda_package/
cp -r lambda_env/lib/python3.*/site-packages/* lambda_package/
```

5. 不要なファイルを削除します（テストファイルやドキュメンテーションなど）：

```bash
find lambda_package -type d -name "tests" -exec rm -rf {} +
find lambda_package -type d -name "docs" -exec rm -rf {} +
```

6. zipファイルを作成します：

```bash
cd lambda_package
zip -r ../lambda_function.zip .
cd ..
```

7. zipファイルのサイズを確認します：

```bash
ls -lh lambda_function.zip
```

このコマンドでzipファイルのサイズが表示されます。50MB以上の場合は、以下の方法でさらに最適化できます：

- 使用していないライブラリがあれば削除します。
- psycopg2-binaryの代わりにpsycopg2を使用し、必要な共有ライブラリを手動でパッケージ化します。
- 大きなライブラリ（例：openai）を個別のLambdaレイヤーとしてデプロイすることを検討します。

これらの手順を実行することで、Lambda関数用のzipファイルを作成し、そのサイズが50MB以内であることを確認できます。サイズが大きすぎる場合は、上記の最適化方法を試してみてください。
