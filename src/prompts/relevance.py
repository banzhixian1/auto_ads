from __future__ import annotations


RELEVANCE_SYSTEM_PROMPT = """
你是 Amazon 广告投放助手。你的任务是判断候选搜索词是否适合当前商品投放。
你需要过滤掉其它品牌/型号专用词、明显不匹配的属性词、与商品用途不相关的词。
判断时优先看搜索意图，而不是只看标题里是否偶然出现 stroller、hook、clip 等单词。
""".strip()

product_title = """Stroller Hooks, 6.3" Large Stroller Clip, 2 Pack Stroller Hooks for Hanging Bags and Shopping, Stroller Accessories for Mommy, Large Carabiner"""

product_image = "https://media-amazon.jijiaplus.com/images/I/31xKu-P+vAL._SL75_.jpg"

product_features = [
    "6.3 inch large stroller clip",
    "2 pack stroller hooks",
    "large carabiner style",
    "for hanging diaper bags, shopping bags, purses, and mommy accessories",
]


search_term1 = {
    "search_term": "uppababy vista upper adapter",
    "search_term_zh": "UPPAbaby Vista 上层适配器",
    "title1": "UPPAbaby Upper Adapter for Vista, Vista V2, and Vista V3 Strollers/ Compatible with Bassinet, Toddler Seat, Aria, Mesa V2, or Mesa Max Infant Car Seats / Quick + Secure Attachment / 1 Set",
    "title2": "Upper Adapter Accessories Compatible with UPPAbaby Vista, Vista V2, Vista V3 Strollers/Bassinet, Toddler Sea, Infant Car Seats (Aria, Mesa V2, Mesa Max) - Not Compatible with Other Models",
    "title3": "Upper Adapter Compatible with UPPAbaby Vista and Vista V2 and Vista V3 Strollers/Bassinet, Toddler Seat, Aria, Mesa V2, or Mesa Max Infant-Secure (Car Seats Accessories 1Set+2 Pcs Stroller Hooks)",
    "note": "用户补充样本。搜索意图是 UPPAbaby Vista 专用上层适配器，标题里偶尔带 hooks，但主需求不是推车挂钩。",
    "expected_decision": "no",
}

search_term2 = {
    "search_term": "coolice rechargeable fan",
    "search_term_zh": "Coolice 充电风扇",
    "title1": "Camping Fan with Remote Control - 12000mAh Rechargeable Battery Powered Fan, Camping Fans for Tents with LED light & Hanging Hook, Rechargeable Battery Operated Ceiling Fans for Tent RV Bed, Green",
    "title2": "Misting Fan, Portable Camping Fans with 9oz Water Tank, 24000mAh Rechargeable Fan with 4 Speed, Battery Powered Fans with 120H Cooling, Last 5H Mist, 2 Mist Modes, Light, Outsides/Summer Essential",
    "title3": "Clip on Fan 65 Hours Portable Desk Fan Rechargeable with LED Lights & Hooks 12000 Capacity Battery Operated Fan with Clips Small Desk Fan Mini Fans for Tents Travel Outdoor Camping Golf Cart Stroller",
    "note": "用户补充样本。搜索意图是充电风扇/露营风扇，hook/stroller 只是部分风扇的安装方式。",
    "expected_decision": "no",
}

search_term3 = {
    "search_term": "uppababy adapter vista v2",
    "search_term_zh": "UPPAbaby Vista V2 适配器",
    "title1": "UPPAbaby Upper Adapter for Vista, Vista V2, and Vista V3 Strollers/ Compatible with Bassinet, Toddler Seat, Aria, Mesa V2, or Mesa Max Infant Car Seats / Quick + Secure Attachment / 1 Set",
    "title2": "Upper Adapter Compatible with UPPAbaby Vista and Vista V2 and Vista V3 Strollers/Bassinet, Toddler Seat, Aria, Mesa V2, or Mesa Max Infant-Secure (Car Seats Accessories 1Set+2 Pcs Stroller Hooks)",
    "title3": "Upper Adapter Accessories Compatible with UPPAbaby Vista, Vista V2, Vista V3 Strollers/Bassinet, Toddler Sea, Infant Car Seats (Aria, Mesa V2, Mesa Max) - Not Compatible with Other Models",
    "note": "用户补充样本。品牌和型号专用适配器词，不是通用大号挂包夹。",
    "expected_decision": "no",
}

search_term4 = {
    "search_term": "disney wet bag",
    "search_term_zh": "迪士尼湿袋",
    "title1": "Bumkins Disney Waterproof Wet Bag for Baby, Travel, Swim Suit, Cloth Diapers, Pump Parts, Pool, Beach, Gym Clothes, Toiletry, Hook to Stroller, Daycare, Zip Reusable Wetdry Packing, Minnie Mouse Icon",
    "title2": "Bumkins Disney Waterproof Wet Bag for Baby, Travel, Swim Suit, Cloth Diapers, Pump Parts, Pool, Beach, Gym Clothes, Toiletry, Hook to Stroller, Daycare, Zip Reusable Wetdry Pack, Princess Magic Pink",
    "title3": """Disney Minnie Mouse EVA Gummy Tote Bag - Waterproof Rubber Beach Bag, Pink Minnie Design, Large 16.5" Carry-All for Pool, Travel & Everyday Use""",
    "note": "用户补充样本。搜索意图是 Disney/Bumkins 湿袋或沙滩包，和挂钩只是弱关联。",
    "expected_decision": "no",
}

search_term5 = {
    "search_term": "doona bag for stroller",
    "search_term_zh": "Doona 推车包",
    "title1": "Baby Uma Stroller Hooks for Bags (2 Pack) - Universal Stroller Clips and Hooks, Non-Slip with One-Hand Opening, 11 lb Weight Capacity, Baby Travel Essential",
    "title2": "Baby & Beyond Essential Bag, Compatible with Doona Car Seat Stroller, with additional hooks and straps to be compatible with any universal stroller, Converts into Tote Diaper Bag",
    "title3": "Storage Bag for Doona Infant Car Seat Stroller, Large Capacity Diaper Bag, Wearable Backpack, Stroller Organizer, Easy Access Zipper, Water-Repellent Lightweight Baby Travel Essentials Organizer",
    "note": "用户补充样本。搜索意图偏 Doona 专用推车包/收纳包，可能需要挂钩但不是直接购买挂钩。",
    "expected_decision": "no",
}

search_term6 = {
    "search_term": "frizcol fan",
    "search_term_zh": "FRIZCOL 风扇",
    "title1": "FRIZCOL Portable Stroller Fan, Use As Power Bank, 65H 12000mAh Battery Operated Fan Flexible Tripod Baby Car Seat Fans with Timming, Personal Mini Handheld/Desk/Small Clip On Fans For Stroller",
    "title2": "Clip on Fan 65 Hours Portable Desk Fan Rechargeable with LED Lights & Hooks 12000 Capacity Battery Operated Fan with Clips Small Desk Fan Mini Fans for Tents Travel Outdoor Camping Golf Cart Stroller",
    "title3": "FRIZCOL 3-in-1 Camping Fan - Portable Fans Rechargeable - 24000mAh Battery Powered Fan with Light & Remote for Indoor, Outdoor, Tent, Travel, Fishing, Jobsite, Gifts for Men Dad Him - Green",
    "note": "用户补充样本。品牌风扇词，主需求不是推车挂钩。",
    "expected_decision": "no",
}

search_term7 = {
    "search_term": "frizcol fan",
    "search_term_zh": "FRIZCOL 风扇",
    "title1": "FRIZCOL Portable Stroller Fan, Use As Power Bank, 65H 12000mAh Battery Operated Fan Flexible Tripod Baby Car Seat Fans with Timming, Personal Mini Handheld/Desk/Small Clip On Fans For Stroller",
    "title2": "Clip on Fan 65 Hours Portable Desk Fan Rechargeable with LED Lights & Hooks 12000 Capacity Battery Operated Fan with Clips Small Desk Fan Mini Fans for Tents Travel Outdoor Camping Golf Cart Stroller",
    "title3": "FRIZCOL 3-in-1 Camping Fan - Portable Fans Rechargeable - 24000mAh Battery Powered Fan with Light & Remote for Indoor, Outdoor, Tent, Travel, Fishing, Jobsite, Gifts for Men Dad Him - Green",
    "note": "用户补充样本。保留重复词，用来观察模型对重复样本的判断是否稳定。",
    "expected_decision": "no",
}

search_term8 = {
    "search_term": "stroller hooks",
    "search_term_zh": "推车挂钩",
    "title1": "Baby Uma Stroller Hooks for Bags (2 Pack) - Universal Stroller Clips and Hooks, Non-Slip with One-Hand Opening, 11 lb Weight Capacity, Baby Travel Essential",
    "title2": "PBnJ Baby Stroller Hooks, 6.6\" Extra Large Carabiner Clip, 2 Pack - Heavy Duty Stroller Clips for Hanging Bags, Patented Foam Handle Mommy Hook, Stroller Accessories for Shopping Purse Grocery Bag",
    "title3": "NxeAnnQi 4 Pack Premium Non-Slip Stroller Hooks, Adjustable Carabiner Clips, Multifunctional Baby Stroller Accessories for Diaper Bags/Purses, Universal Fit for Strollers, Bikes, Wheelchairs & Walkers",
    "note": "真实 ABA 样本。2026-05-23 周报，search_rank=49900。核心品类词，和商品标题、图片形态高度一致。",
    "source": "aba_brand_search_words_weeks",
    "report_date": "2026-05-23",
    "search_rank": 49900,
    "click_share": 34.63,
    "conversion_share": 31.26,
    "expected_decision": "yes",
}

search_term9 = {
    "search_term": "stroller hooks for bags",
    "search_term_zh": "挂包用推车挂钩",
    "title1": "Baby Uma Stroller Hooks for Bags (2 Pack) - Universal Stroller Clips and Hooks, Non-Slip with One-Hand Opening, 11 lb Weight Capacity, Baby Travel Essential",
    "title2": "PBnJ baby Stroller Hooks 2 Pack Organizer Clip Travel Purse Shopping Diaper Bags",
    "title3": "PBnJ Baby Stroller Hooks, 6.6\" Extra Large Carabiner Clip, 2 Pack - Heavy Duty Stroller Clips for Hanging Bags, Patented Foam Handle Mommy Hook, Stroller Accessories for Shopping Purse Grocery Bag",
    "note": "真实 ABA 样本。2026-05-23 周报，search_rank=273500。明确表示用于把包挂在婴儿车上，是主商品的直接需求。",
    "source": "aba_brand_search_words_weeks",
    "report_date": "2026-05-23",
    "search_rank": 273500,
    "click_share": 41.73,
    "conversion_share": 38.75,
    "expected_decision": "yes",
}

search_term10 = {
    "search_term": "mommy hook",
    "search_term_zh": "妈妈挂钩 / 推车妈妈挂钩",
    "title1": "PBnJ Baby Stroller Hooks, 6.6\" Extra Large Carabiner Clip, 2 Pack - Heavy Duty Stroller Clips for Hanging Bags, Patented Foam Handle Mommy Hook, Stroller Accessories for Shopping Purse Grocery Bag",
    "title2": "2 Pack Stroller Hooks,6.3\" Large Stroller Clips,Stroller Hook for Hanging Diaper Bags and Shopping,Universal Stroller Accessories for Mommy,Large Carabiner Clip Heavy Duty",
    "title3": "Stroller Hooks, 6.3\" Large Stroller Clip, 2 Pack Stroller Hooks for Hanging Bags and Shopping, Stroller Accessories for Mommy, Large Carabiner",
    "note": "真实 ABA 样本。2026-05-23 周报，search_rank=840907。Mommy hook 在 ABA 结果中对应推车挂钩类商品，但模型仍要留意是否被识别为品牌词。",
    "source": "aba_brand_search_words_weeks",
    "report_date": "2026-05-23",
    "search_rank": 840907,
    "click_share": 63.1,
    "conversion_share": 57.15,
    "expected_decision": "yes",
}

search_term11 = {
    "search_term": "stroller clips",
    "search_term_zh": "推车夹 / 推车挂夹",
    "title1": "Baby Uma Stroller Hooks for Bags (2 Pack) - Universal Stroller Clips and Hooks, Non-Slip with One-Hand Opening, 11 lb Weight Capacity, Baby Travel Essential",
    "title2": "PBnJ Baby Stroller Hooks, 6.6\" Extra Large Carabiner Clip, 2 Pack - Heavy Duty Stroller Clips for Hanging Bags, Patented Foam Handle Mommy Hook, Stroller Accessories for Shopping Purse Grocery Bag",
    "title3": "Stroller Hooks 2 Pcs Large Carabiner Clips for Hanging Diaper Bags, Purse Grocery, and Shopping Bags. Heavy Duty Universal Climbing Clips Best Mommy Accessories for Outdoor, Camping and Hiking.",
    "note": "真实 ABA 样本。2026-05-23 周报，search_rank=117925。clip 和 hook 在该品类中高度同义，适合观察模型是否能识别同义词。",
    "source": "aba_brand_search_words_weeks",
    "report_date": "2026-05-23",
    "search_rank": 117925,
    "click_share": 39.44,
    "conversion_share": 33.87,
    "expected_decision": "yes",
}

search_term12 = {
    "search_term": "large carabiner clip",
    "search_term_zh": "大号登山扣夹",
    "title1": "SURDOCA Stroller Hooks, Large Stroller Hooks for Bags, Universal Stroller Clips and Hooks, Mommy Hook for Stroller Heavy Duty, Stroller Accessories for Mom",
    "title2": "Stroller Hooks 2 Pcs Large Carabiner Clips for Hanging Diaper Bags, Purse Grocery, and Shopping Bags. Heavy Duty Universal Climbing Clips Best Mommy Accessories for Outdoor, Camping and Hiking.",
    "title3": "Stroller Hooks, 6.3\" Large Stroller Clip, 2 Pack Stroller Hooks for Hanging Bags and Shopping, Stroller Accessories for Mommy, Large Carabiner",
    "note": "真实 ABA 样本。2026-05-23 周报，search_rank=87339。与商品标题中的 large carabiner 直接匹配，但词本身泛化，需要模型判断投放风险。",
    "source": "aba_brand_search_words_weeks",
    "report_date": "2026-05-23",
    "search_rank": 87339,
    "click_share": 35.09,
    "conversion_share": 25.9,
    "expected_decision": "yes",
}

search_term13 = {
    "search_term": "stroller organizer bag",
    "search_term_zh": "推车收纳包",
    "title1": "Caraa Womens Stroller Pack Blush One Size",
    "title2": "Momcozy Universal Stroller Organizer with Insulated Cup Holder Detachable Phone Bag & Shoulder Strap, Fits for Stroller Like Uppababy, Baby Jogger, Britax, BOB, Umbrella and Pet Stroller",
    "title3": "Guiseapue Universal Stroller Organizer with Cup Holder: Baby Essentials, Stroller Caddy Accessories with Detachable Phone Bag, Non-Slip Straps, Fits for Uppababy, Baby Jogger, New Moms Baby Gifts",
    "note": "真实 ABA 样本。2026-05-23 周报，search_rank=258086。相邻品类但主需求是收纳包，不是挂钩；适合测试模型是否会过度放行 stroller 相关词。",
    "source": "aba_brand_search_words_weeks",
    "report_date": "2026-05-23",
    "search_rank": 258086,
    "click_share": 66.17,
    "conversion_share": 16.67,
    "expected_decision": "no",
}

search_term14 = {
    "search_term": "stroller fan",
    "search_term_zh": "推车风扇",
    "title1": "Gaiatop Mini Portable Stroller Fan, Battery Operated Small Clip on, Detachable 3 Speed Rechargeable, 360 Degree Rotate Flexible Tripod Better Cooling for Car Seat Crib Treadmill Travel Black",
    "title2": "Momcozy 8000mAh Portable Stroller Fan | 27H Ultra-long Battery Life | Detachable 4 Speed 360 Degree Rotate | 2 Modes LED Night Light, USB Rechargeable Handheld Cooling Fan for Travel, Car Seat, Bedroom",
    "title3": "AMACOOL Battery Operated Stroller Fan, Baby Travel Essentials for Beach Disney, Newborn Boy & Girl Showers Gifts Registry Search, Rechargeable Clip On Fan for Car Seat Wagon Crib Bike Treadmill",
    "note": "真实 ABA 样本。2026-05-23 周报，search_rank=710。高热度但主商品是推车风扇，应该过滤。",
    "source": "aba_brand_search_words_weeks",
    "report_date": "2026-05-23",
    "search_rank": 710,
    "click_share": 47.26,
    "conversion_share": 34.75,
    "expected_decision": "no",
}

search_term15 = {
    "search_term": "clip on stroller fan",
    "search_term_zh": "夹式推车风扇",
    "title1": "Gaiatop Portable Clip on Fan Battery Operated, Small Powerful 3 Speed Quiet 360 Degree Rotate, USB Rechargeable Mini Personal Cooling Fan for Desk Table Home Office Stroller Camping Women Gifts Black Blue",
    "title2": "Momcozy Portable Stroller Fan with Clip | 4-Speed Mini-Fan for Carrier | Personal Fans Ultra Light 0.26lb | Gaps <=4.5mm | Handheld Cooling | Rechargeable Rotate for Diaper Backpack/Table/Chair",
    "title3": "Hotsales Clip-On Portable Fan, 13500 RPM Rechargeable Handheld Mini Fan with LED Display, 360 Degree Rotating Detachable Clip, Stroller Fan for Baby, Compact Travel Essentials/Lash, Summer Gifts for Women",
    "note": "真实 ABA 样本。2026-05-23 周报，search_rank=119920。包含 clip/stroller，但主商品仍是风扇。",
    "source": "aba_brand_search_words_weeks",
    "report_date": "2026-05-23",
    "search_rank": 119920,
    "click_share": 46.63,
    "conversion_share": 29.25,
    "expected_decision": "no",
}

search_term16 = {
    "search_term": "wet bag",
    "search_term_zh": "湿袋 / 防水湿干袋",
    "title1": "Tiny Twinkle Mess Proof Wet Bags | 2-Pack Reusable Waterproof Wet Bags for Swimsuits | Baby Clothes | Travel & Diaper Bag (Black, Green Checkers)",
    "title2": "ALVABABY 2pcs Cloth Diaper Wet Dry Bags Waterproof Reusable with Two Zippered Pockets Travel Beach Pool Daycare Soiled Baby Items Yoga Gym Bag for Swimsuits or Wet Clothes L2933",
    "title3": "Fokongna Wet Dry Bag - Waterproof Travel Bag, Large Zipper Pouch for Swimsuits, Diapers, Toiletries, Makeup for Women & Girls",
    "note": "真实 ABA 样本。2026-05-23 周报，search_rank=16883。搜索意图是湿袋/防水收纳袋，和推车挂钩不匹配。",
    "source": "aba_brand_search_words_weeks",
    "report_date": "2026-05-23",
    "search_rank": 16883,
    "click_share": 20.07,
    "conversion_share": 10.79,
    "expected_decision": "no",
}


RELEVANCE_TEST_CASES = [
    search_term1,
    search_term2,
    search_term3,
    search_term4,
    search_term5,
    search_term6,
    search_term7,
    search_term8,
    search_term9,
    search_term10,
    search_term11,
    search_term12,
    search_term13,
    search_term14,
    search_term15,
    search_term16,
]


def _case_titles(case: dict) -> list[str]:
    return [
        str(case.get(f"title{index}", "")).strip()
        for index in range(1, 4)
        if str(case.get(f"title{index}", "")).strip()
    ]


def _format_case_for_prompt(
    index: int,
    case: dict,
    include_review_notes: bool = False,
) -> str:
    lines = [
        f"{index}. search_term: {case.get('search_term', '')}",
        f"   中文备注: {case.get('search_term_zh', '无')}",
    ]
    titles = _case_titles(case)
    if titles:
        lines.append("   该搜索词下的商品标题参考:")
        for title_index, title in enumerate(titles, start=1):
            lines.append(f"   - title{title_index}: {title}")
    if include_review_notes:
        lines.append(f"   人工备注: {case.get('note', '无')}")
    return "\n".join(lines)


def build_relevance_prompt(
    product_title: str,
    product_features: list[str] | None = None,
    candidate_terms: list[str] | None = None,
    candidate_cases: list[dict] | None = None,
    include_review_notes: bool = False,
) -> str:
    """
    拼装相关性判断提示词。

    candidate_terms 用于兼容旧调用；candidate_cases 用于当前测试集，可带前三商品标题和中文备注。
    include_review_notes 默认关闭，避免把人工预期判断喂给模型。
    """
    product_features = product_features or []
    candidate_terms = candidate_terms or []
    candidate_cases = candidate_cases or []

    if candidate_cases:
        candidates_text = "\n\n".join(
            _format_case_for_prompt(index, case, include_review_notes=include_review_notes)
            for index, case in enumerate(candidate_cases, start=1)
        )
    else:
        candidates_text = ", ".join(candidate_terms) or "无"

    return (
        f"商品标题：{product_title}\n"
        f"商品特征：{', '.join(product_features) or '无'}\n"
        "商品图片：已随消息一起提供。若图片无法读取，请以商品标题和商品特征为主。\n\n"
        "判断标准：\n"
        "1. 适合投放：搜索意图是在购买推车挂钩、推车挂包夹、stroller/pram/buggy/pushchair hooks、"
        "大号 carabiner stroller clip，或明确用于挂 diaper bag / shopping bag / purse 的推车挂钩。\n"
        "2. 不适合投放：其它品牌或型号专用配件、风扇、湿袋、收纳包、推车本体、车座适配器等相邻但主品类不同的词。\n"
        "3. 泛词需要谨慎：如果词很宽泛但仍能覆盖当前商品，例如 large carabiner clip，可以给出是否建议投放及风险。\n"
        "4. 不要因为参考标题里出现 hook、stroller、clip 就直接通过；必须判断搜索词本身的主需求。\n\n"
        f"候选搜索词：\n{candidates_text}\n\n"
        "请逐个判断是否适合投放。必须按输入顺序返回 JSON 数组，不要输出 JSON 以外的文本。\n"
        "每个元素包含以下字段：\n"
        "- search_term: 原搜索词\n"
        "- search_term_zh: 搜索词中文备注\n"
        "- use: true 或 false\n"
        "- match_type: direct / broad_relevant / adjacent_mismatch / brand_or_model_mismatch / category_mismatch\n"
        "- reason: 用中文解释为什么使用或不使用，需要引用搜索意图、商品标题/图片/参考标题中的关键证据\n"
        "- risk: 简短说明投放风险，没有则写“低”\n"
    )


def build_relevance_messages(
    candidate_cases: list[dict] | None = None,
    include_image: bool = True,
    include_review_notes: bool = False,
) -> list[dict]:
    prompt = build_relevance_prompt(
        product_title=product_title,
        product_features=product_features,
        candidate_cases=candidate_cases or RELEVANCE_TEST_CASES,
        include_review_notes=include_review_notes,
    )
    user_content = []
    if include_image and product_image:
        user_content.append({"type": "image", "image": product_image})
    user_content.append({"type": "text", "text": prompt})
    return [
        {
            "role": "system",
            "content": [{"type": "text", "text": RELEVANCE_SYSTEM_PROMPT}],
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]


def screen_relevance_with_llm(
    candidate_cases: list[dict] | None = None,
    model_name: str | None = None,
    timeout: int = 120,
    include_image: bool = True,
) -> str:
    """
    调用 src.apis.llm.inference，让模型筛选候选词并解释每个词是否投放。

    注意：src.apis.llm 会读取 configs/apis.ini；本地没有 api_key 时调用会失败。
    """
    from src.apis.llm import inference

    messages = build_relevance_messages(
        candidate_cases=candidate_cases or RELEVANCE_TEST_CASES,
        include_image=include_image,
    )
    return inference(messages=messages, model_name=model_name, timeout=timeout)
