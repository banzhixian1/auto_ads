import math

def weighted_aba_metrics(click_list,
                         conv_list,
                         decay=0.3):
    """
    ABA搜索词加权分析函数（点击份额 + 转化份额 + 出单效率）

    参数：
    click_list: list[float]  每周点击份额（最新周在第0位）
    conv_list:  list[float]  每周转化份额（最新周在第0位）
    decay:      float        指数衰减系数 λ，默认0.3

    返回：
    dict:
        weighted_click_share
        weighted_conv_share
        efficiency (转化/点击)
        weights
    """

    if len(click_list) != len(conv_list):
        raise ValueError("click_list 和 conv_list 长度必须一致")

    n = len(click_list)

    # 生成指数权重（越新的权重越大）
    weights = [math.exp(-decay * i) for i in range(n)]

    # 归一化
    weight_sum = sum(weights)

    norm_weights = [w / weight_sum for w in weights]

    # 加权点击/转化
    weighted_click = sum(c * w for c, w in zip(click_list, norm_weights))
    weighted_conv = sum(c * w for c, w in zip(conv_list, norm_weights))

    # 出单效率（你定义的核心指标）
    efficiency = (
        weighted_conv / weighted_click
        if weighted_click != 0 else 0
    )

    return {
        "weighted_click_share": weighted_click,
        "weighted_conv_share": weighted_conv,
        "efficiency": efficiency,
        "weights": norm_weights
    }