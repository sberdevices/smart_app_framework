from typing import Optional

def pan2service(pan: str) -> Optional[str]:

    if len(pan) < 4:
        return None

    first_digit = int(pan[0:2])

    if first_digit == 50 or first_digit in range(56, 69):
        return "maestro"
    if first_digit in range(51, 55):
        return "mastercard"
    if first_digit == 37:
        return "amex"

    first_digit = int(pan[0])
    if first_digit == 4:
        return "visa"
    if first_digit == 2:
        return "mir"

    return None
