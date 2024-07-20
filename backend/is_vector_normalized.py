import os
import time
from openai import OpenAI, AzureOpenAI
import numpy as np
from dotenv import load_dotenv

load_dotenv()

ENABLE_OPENAI = os.getenv("ENABLE_OPENAI", "true").lower() == "true"

if ENABLE_OPENAI:
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    print("Using OpenAI")
else:
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    print("Using Azure OpenAI")

def get_embedding(text):
    if ENABLE_OPENAI:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
    else:
        response = client.embeddings.create(
            input=text,
            deployment_id=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ID")
        )
    vector = response.data[0].embedding
    return vector

def is_normalized(vector):
    norm = np.linalg.norm(vector)
    print(f"norm: {norm}")
    return np.isclose(norm, 1.0)

def negative_inner_product(a, b):
    return -np.dot(a, b)

def cosine_distance(a, b):
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def time_function(func, *args):
    start_time = time.time()
    result = func(*args)
    end_time = time.time()
    return result, end_time - start_time

# メイン処理
text1 = "god"
text2 = "god"

vector1 = get_embedding(text1)
vector2 = get_embedding(text2)

normalized1 = is_normalized(vector1)
normalized2 = is_normalized(vector2)

print(f"ベクトル1が正規化されているか: {normalized1}")
print(f"ベクトル2が正規化されているか: {normalized2}")
print(f"ベクトル1の長さ: {np.linalg.norm(vector1)}")
print(f"ベクトル2の長さ: {np.linalg.norm(vector2)}")

# 負の内積の計算と時間測定
neg_inner_prod, neg_inner_time = time_function(negative_inner_product, vector1, vector2)
print(f"負の内積: {neg_inner_prod}")
print(f"負の内積の計算時間: {neg_inner_time:.6f} 秒")

# コサイン距離の計算と時間測定
cos_dist, cos_time = time_function(cosine_distance, vector1, vector2)
print(f"コサイン距離: {cos_dist}")
print(f"コサイン距離の計算時間: {cos_time:.6f} 秒")

# 時間の比較
if neg_inner_time < cos_time:
    time_diff = (cos_time - neg_inner_time) / neg_inner_time * 100
    print(f"負の内積の計算は、コサイン距離の計算より {time_diff:.2f}% 速いです")
else:
    time_diff = (neg_inner_time - cos_time) / cos_time * 100
    print(f"コサイン距離の計算は、負の内積の計算より {time_diff:.2f}% 速いです")

# 結果の解釈
print("\n結果の解釈:")
print("負の内積: 値が-1に近いほど、ベクトルが類似しています。")
print("コサイン距離: 値が0に近いほど、ベクトルが類似しています。")
