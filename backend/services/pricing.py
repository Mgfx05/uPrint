BW_PRICE = 2
COLOR_PRICE = 10


def calculate_price(pages: int, copies: int, print_type: str = "bw", paper_size: str = "a4"):
    price_per_page = COLOR_PRICE if print_type == "color" else BW_PRICE
    
    if paper_size == "a3":
        price_per_page *= 2

    total = pages * copies * price_per_page

    return {
        "pages": pages,
        "copies": copies,
        "type": print_type,
        "paper_size": paper_size,
        "price_per_page": price_per_page,
        "total_price": total
    }