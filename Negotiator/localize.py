def localize(s):
    loc_dict = {
        "price": "цена",
        "deadline":"срок поставки",
        "quality": "качество",
        "warranty": "гарантия",
        "easy": "легко",
        "medium": "средне",
        "hard": "тяжело",
        "seller": "продавец",
        "buyer": "покупатель",
    }
    return loc_dict.get(s,s)

def format_dict(dictionary, nest, desc=''):
    for key, val in dictionary.items():
        desc += f"{"  " * nest}{localize(key).capitalize()}: {val}\n"
    return desc