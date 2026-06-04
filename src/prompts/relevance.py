RELEVANCE_SYSTEM_PROMPT = """
你是 Amazon 广告投放助手。你的任务是判断候选搜索词是否适合当前商品投放。
过滤掉品牌词、明显不匹配的属性词、与商品用途不相关的词。
""".strip()


def build_relevance_prompt(
    product_title: str,
    product_features: list[str],
    candidate_terms: list[str],
) -> str:
    # 统一拼装相关性判断提示词，后续直接给 LLM 使用
    return (
        f"商品标题：{product_title}\n"
        f"商品特征：{', '.join(product_features) or '无'}\n"
        f"候选搜索词：{', '.join(candidate_terms) or '无'}\n"
        "请逐个判断是否适合投放，并说明原因。"
    )
