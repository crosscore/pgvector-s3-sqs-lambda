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
1. プロジェクトディレクトリを作成。
2. venvを作成し、アクティベート：

```bash
python3 -m venv lambda_env
source lambda_env/bin/activate  # Linuxの場合
```

3. 必要なライブラリをインストール：

```bash
pip install -r requirements.txt
```

4. Lambdaに必要なファイルをコピー：

```bash
mkdir lambda_package
cp pdf_to_pgvector.py config.py lambda_package/
cp -r lambda_env/lib/python3.11/site-packages/* lambda_package/
```

5. 不要なファイルを削除（テストファイルやドキュメンテーションなど）：

```bash
find lambda_package -type d -name "tests" -exec rm -rf {} +
find lambda_package -type d -name "docs" -exec rm -rf {} +
```

6. zipファイルを作成：

```bash
cd lambda_package
zip -r ../lambda_function.zip .
cd ..
```

7. zipファイルのサイズを確認：

```bash
ls -lh lambda_function.zip
```

50MB以上の場合は、以下の方法でさらに最適化する：
- 使用していないライブラリがあれば削除。
- psycopg2-binaryの代わりにpsycopg2を使用し、必要な共有ライブラリを手動でパッケージ化。
- 大きなライブラリ（例：openai）を個別のLambdaレイヤーとしてデプロイ。



An error occurred (InvalidClientTokenId) when calling the GetQueueAttributes operation: The security token included in the request is invalid. の解決策：

1. 認証情報の期限切れ：
   アクセスキーとシークレットキーが期限切れになっている可能性があります。IAMコンソールで現在の認証情報の状態を確認し、必要であれば新しいキーペアを生成してください。

2. 認証情報の不一致：
   `~/.aws/credentials` ファイルの認証情報が、実際のAWSアカウントと一致していない可能性があります。ファイルの内容を確認し、必要であれば更新してください。

3. リージョンの不一致：
   コマンドで指定しているキューのURLと、設定されているリージョンが一致していることを確認してください。

4. IAMユーザーの権限：
   使用しているIAMユーザーがSQSの操作に必要な権限を持っていることを確認してください。

5. AWSCLIのバージョン：
   AWS CLIが最新版であることを確認してください。古いバージョンを使用している場合、認証に問題が生じる可能性があります。

6. 時計の同期：
   ローカルマシンの時計がAWSのサーバー時間と大きくずれていないか確認してください。

解決のためのステップ：
1. AWS認証情報の再設定：
   ```
   aws configure
   ```
   このコマンドを実行し、アクセスキーID、シークレットアクセスキー、デフォルトリージョンを再入力してください。

2. 認証情報の確認：
   ```
   aws sts get-caller-identity
   ```
   このコマンドを実行して、現在の認証情報が有効であることを確認してください。

3. SQSへのアクセス確認：
   ```
   aws sqs list-queues
   ```
   このコマンドでSQSキューのリストが取得できるか確認してください。

これらの手順を試してみて、問題が解決しない場合は、IAMユーザーの権限設定やAWSアカウントの状態を詳細に確認する必要があるかもしれません。その場合は、さらに詳しい情報を提供していただければ、より具体的なアドバイスができます。


# AWS SQS
aws sqs receive-message --queue-url <YourQueueURL>

ARNの確認コマンド:
aws sqs get-queue-attributes --queue-url <デッドレターキューのURL> --attribute-names QueueArn

ARNの構造:
arn:aws:sqs:<リージョン>:<アカウントID>:<キュー名>

DeadQueueが設定されていることの確認コマンド：
aws sqs get-queue-attributes --queue-url <キューのURL> --attribute-names RedrivePolicy

{
    "Attributes": {
        "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:ap-northeast-1:524000000000:my-test-pdf-deadqueue.fifo\",\"maxReceiveCount\":30}"
    }
}
