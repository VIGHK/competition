import numpy as np
import pandas as pd
from math import log, sqrt

data = {
    '序号': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    '出去玩': ['是', '是', '是', '是', '是', '是', '是', '否', '否', '否'],
    '天气状况': ['好', '一般', '一般', '一般', '一般', '好', '好', '一般', '一般', '一般'],
    '有同伴': ['无', '有', '有', '有', '有', '无', '无', '无', '有', '无'],
    '零花钱': ['多', '多', '少', '少', '少', '多', '多', '多', '少', '少'],
    '特殊节日': ['是', '是', '否', '否', '否', '是', '是', '是', '否', '否'],
    '心情指数': [5, 5, 1, 3, 5, 5, 5, 1, 1, 5]
}
df = pd.DataFrame(data)

#初始化
N = len(df)
weights = np.ones(N) / N

# 弱分类器定义
def weak_classifier(feature, value, data):
    if feature == '心情指数>':
        return data['心情指数'] >= value
    elif feature == '心情指数<':
        return data['心情指数'] <= value
    else:
        return data[feature] == value


# 可能的弱分类器列表
weak_classifiers = [
    ('天气状况', '好'),
    ('天气状况', '一般'),
    ('有同伴', '有'),
    ('有同伴', '无'),
    ('零花钱', '多'),
    ('零花钱', '少'),
    ('特殊节日', '是'),
    ('特殊节日', '否'),
    ('心情指数>', 1),  # 心情指数 >= 1
    ('心情指数>', 2),  # 心情指数 >= 2
    ('心情指数>', 3),  # 心情指数 >= 3
    ('心情指数>', 4),  # 心情指数 >= 4
    ('心情指数<', 5),  # 心情指数 <= 5
    ('心情指数<', 4),  # 心情指数 <= 4
    ('心情指数<', 3),  # 心情指数 <= 3
    ('心情指数<', 2)   # 心情指数 <= 2
]

# AdaBoost迭代
alphas = []
selected_classifiers = []

for round in range(3):
    print(f"\n=== 第 {round + 1} 轮迭代 ===")

    # 计算每个弱分类器的错误率
    errors = []
    for feature, value in weak_classifiers:
        predictions = weak_classifier(feature, value, df)
        error = sum(weights * (predictions != (df['出去玩'] == '是')))
        errors.append(error)
    for i, (f, v) in enumerate(weak_classifiers, start=0):
        print(f"分类器：{f}={v}，错误率:{errors[i]:5f}")

    best_idx = np.argmin(errors)
    best_feature, best_value = weak_classifiers[best_idx]
    best_error = errors[best_idx]
    print(f"最佳弱分类器: {best_feature} = {best_value}, 错误率: {best_error:.5f}")

    alpha = 0.5 * np.log((1 - best_error) / best_error)
    alphas.append(alpha)
    selected_classifiers.append((best_feature, best_value))
    print(f"分类器权重: {alpha:.5f}")

    predictions = weak_classifier(best_feature, best_value, df)
    incorrect = (predictions != (df['出去玩'] == '是'))
    weights *= np.exp(alpha * incorrect)
    print(f"归一因子：{np.sum(weights):5f}")
    weights /= np.sum(weights)
    print("更新后的样本权重:")
    for i, w in enumerate(weights):
        print(f"样本 {i + 1}: {w:.4f}")

# 输出最终强分类器
print("\n=== 最终强分类器 ===")
strong_classifier = " + ".join([f"{alpha:.4f} * h_{i + 1}" for i, alpha in enumerate(alphas)])
print(f"H(x) = sign({strong_classifier})")
print("其中:")
for i, (feature, value) in enumerate(selected_classifiers):
    print(f"h_{i + 1}: {feature} = {value}")