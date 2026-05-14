class InsufficientAmountError(Exception):
    pass


class Wallet:
    def __init__(self, initial_amount=0):
        self.balance = initial_amount

    def spend_cash(self, amount):
        if self.balance < amount:
            message = f"Not enough available to spend {amount}"
            raise InsufficientAmountError(message)
        self.balance -= amount

    def add_cash(self, amount):
        self.balance += amount
