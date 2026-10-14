from dataclasses import dataclass
from enum import Enum

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"

class Portfolio:
    def __init__(self, cash):
        self.cash = cash
        self.reserved_cash = 0
        self.positions = dict()
        self.reserved_positions = dict()

    def reserve_cash(self, amount):
        if self.cash - self.reserved_cash < amount:
            raise ValueError("Insufficient Available Cash")
        self.reserved_cash += amount

    def release_cash(self, amount):
        if self.reserved_cash < amount:
            raise ValueError("Insufficient reserved cash")
        self.reserved_cash -= amount

    def reserve_positions(self, asset, quantity):
        if self.positions.get(asset, 0) - self.reserved_positions.get(asset, 0) < quantity:
            raise ValueError("Insufficient holdings")
        if asset not in self.reserved_positions:
            self.reserved_positions[asset] = 0
        self.reserved_positions[asset] += quantity

    def release_positions(self, asset, quantity):
        if self.reserved_positions.get(asset, 0) < quantity:
            raise ValueError("Insufficient reserved holdings")
        self.reserved_positions[asset] -= quantity

    def buy(self, asset, quantity, price):
        cost = quantity*price

        if self.cash < cost: raise ValueError("Insufficient balance")

        self.cash -= cost

        if asset not in self.positions:
            self.positions[asset] = 0
        self.positions[asset] += quantity

    def sell(self, asset, quantity, price):
        if quantity > self.positions.get(asset, 0): raise ValueError("Insufficient holding!!")
        revenue = quantity*price
        self.cash += revenue

        self.positions[asset] -= quantity

    def consume_reserved_cash(self, amount):
        if self.reserved_cash < amount:
            raise ValueError("Insufficient reserved cash")
        self.reserved_cash -= amount
        self.cash -= amount

    def consume_reserved_positions(self, asset, quantity):
        if self.reserved_positions.get(asset, 0) < quantity:
            raise ValueError("Insufficient Reserved Holdings")
        self.reserved_positions[asset] -= quantity
        self.positions[asset] -= quantity

    def execute_buy(self, asset, quantity, trade_price, reserved_price):
        self.consume_reserved_cash(trade_price*quantity)
        self.release_cash(quantity*(reserved_price-trade_price))

        if asset not in self.positions:
            self.positions[asset] = 0
        self.positions[asset] += quantity

    def execute_sell(self, asset, quantity, trade_price):
        self.consume_reserved_positions(asset, quantity)
        self.cash += quantity*trade_price

class Trader:
    def __init__(self, name, cash):
        self.name = name
        self.portfolio = Portfolio(cash)


@dataclass
class Trade:
    buyer : Trader
    seller: Trader
    asset: str
    quantity: int
    price: float


@dataclass
class Order:
    trader: Trader
    asset: str
    side: OrderSide
    original_quantity: int
    price: float
    order_id: int = 0
    status: OrderStatus = OrderStatus.OPEN
    remaining_quantity: int = 0

    def __post_init__(self):
        self.remaining_quantity = self.original_quantity

    def validate(self):
        if self.original_quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        if self.price <= 0:
            raise ValueError("Price must be greater than zero")
        if not isinstance(self.asset, str) or not self.asset.strip():
            raise ValueError("Asset must be a non-empty")
        if not isinstance(self.side, OrderSide):
            raise ValueError("Invalid order side")

    def cancel(self):
        if self.status not in (OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED):
            raise ValueError("Order cannot be cancelled")
        self.status = OrderStatus.CANCELLED

class OrderBook:
    def __init__(self, asset):
        self.asset = asset
        self.buy_orders = []
        self.sell_orders = []
        self.trades = []
        
    def add_order(self, order):
        if order.side == OrderSide.BUY:
            self.buy_orders.append(order)
        else:
            self.sell_orders.append(order)

    def remove_order(self, order_id):
        for order in self.buy_orders:
            if order.order_id == order_id:
                self.buy_orders.remove(order)
                return
        for order in self.sell_orders:
            if order.order_id == order_id:
                self.sell_orders == order_id
                return

        raise ValueError("Order not found!!")

    def sort_orders(self):
        self.buy_orders = sorted(self.buy_orders, key = lambda order: (-order.price, order.order_id))
        self.sell_orders = sorted(self.sell_orders, key = lambda order: (order.price, order.order_id))

    def match_orders(self):
        self.sort_orders()

        while self.buy_orders and self.sell_orders:
            best_buy = self.buy_orders[0]
            best_sell = self.sell_orders[0]
            if best_buy.price < best_sell.price:
                break
                
            trade_quantity = min(best_buy.remaining_quantity, best_sell.remaining_quantity)

            trade = Trade(
                buyer = best_buy.trader,
                seller = best_sell.trader,
                asset = best_buy.asset,
                quantity = trade_quantity,
                price = best_sell.price
            )

            self.trades.append(trade)

            best_buy.trader.portfolio.execute_buy(
                best_buy.asset,
                trade_quantity,
                best_sell.price,
                best_buy.price
            )

            best_sell.trader.portfolio.execute_sell(
                best_sell.asset,
                trade_quantity,
                best_sell.price
            )
            best_buy.remaining_quantity -= trade_quantity
            best_sell.remaining_quantity -= trade_quantity

            if best_buy.remaining_quantity == 0:
                best_buy.status = OrderStatus.FILLED
            else:
                best_buy.status = OrderStatus.PARTIALLY_FILLED

            if best_sell.remaining_quantity == 0:
                best_sell.status = OrderStatus.FILLED
            else:
                best_sell.status = OrderStatus.PARTIALLY_FILLED

            if best_buy.remaining_quantity == 0:
                self.buy_orders.pop(0)

            if best_sell.remaining_quantity == 0:
                self.sell_orders.pop(0)

class OrderBookManager:
    def __init__(self):
        self.order_books = dict()

    def get_order_book(self, asset):
        if asset not in self.order_books:
            self.order_books[asset] = OrderBook(asset)
        return self.order_books[asset]

class Exchange:
    def __init__(self):
        self.order_book_manager = OrderBookManager()
        self.next_order_id = 1
        self.orders = dict()

    def submit_order(self, order):
        order.validate()
        person_portfolio = order.trader.portfolio
        if order.side == OrderSide.SELL:
            if order.original_quantity > person_portfolio.positions.get(order.asset, 0) - person_portfolio.reserved_positions.get(order.asset, 0):
                raise ValueError("Insufficient Holdings!!")
            person_portfolio.reserve_positions(order.asset, order.original_quantity)
        else:
            cost = order.original_quantity * order.price
            if cost > person_portfolio.cash - person_portfolio.reserved_cash:
                raise ValueError("Insufficient Balance!!")
            person_portfolio.reserve_cash(cost)

        order.order_id = self.next_order_id
        self.next_order_id += 1

        order_book = self.order_book_manager.get_order_book(order.asset)
        order_book.add_order(order)
        self.orders[order.order_id] = order
        order_book.match_orders()

    def cancel_order(self, order_id):
        if order_id not in self.orders:
            raise ValueError("Order not found!!")

        order = self.orders[order_id]
        order_book = self.order_book_manager.get_order_book(order.asset)
        order.cancel()

        order_book.remove_order(order_id)

        if order.side == OrderSide.BUY:
            order.trader.portfolio.release_cash(order.remaining_quantity * order.price)
        else:
            order.trader.portfolio.release_positions(
                order.asset, order.remaining_quantity
            )

if __name__=="__main__":
    pass
    # alice = Trader("Alice", 10000)
    # bob = Trader("Bob", 10000)
    # charlie = Trader("Charlie", 10000)
    # david = Trader("David", 10000)
    # david.portfolio.positions["TECH"] = 5

    # ex = Exchange()

    # order1 = Order(
    #     trader = alice,
    #     asset = "TECH",
    #     side=OrderSide.BUY,
    #     quantity = 3, 
    #     price=100
    # )
    # ex.submit_order(order1)
    # order2 = Order(
    #     trader=bob,
    #     asset="GOLD",
    #     side=OrderSide.BUY,
    #     quantity=3, 
    #     price=100
    # )
    # ex.submit_order(order2)

    # order3 = Order(
    #     trader = charlie,
    #     asset = "TECH",
    #     side=OrderSide.BUY,
    #     quantity = 3, 
    #     price=100
    # )
    # ex.submit_order(order3)
    # order4 = Order(
    #     trader = david,
    #     asset = "TECH",
    #     side=OrderSide.SELL,
    #     quantity = 5, 
    #     price=100
    # )
    # ex.submit_order(order4)


    # print("\n========== PORTFOLIOS ==========")

    # print("\nAlice:")
    # print("Cash:", alice.portfolio.cash)
    # print("Reserved Cash:", alice.portfolio.reserved_cash)
    # print("Positions:", alice.portfolio.positions)
    # print("Reserved Positions:", alice.portfolio.reserved_positions)

    # print("\nBob:")
    # print("Cash:", bob.portfolio.cash)
    # print("Reserved Cash:", bob.portfolio.reserved_cash)
    # print("Positions:", bob.portfolio.positions)
    # print("Reserved Positions:", bob.portfolio.reserved_positions)

    # print("\nCharlie:")
    # print("Cash:", charlie.portfolio.cash)
    # print("Reserved Cash:", charlie.portfolio.reserved_cash)
    # print("Positions:", charlie.portfolio.positions)
    # print("Reserved Positions:", charlie.portfolio.reserved_positions)

    # print("\nDavid:")
    # print("Cash:", david.portfolio.cash)
    # print("Reserved Cash:", david.portfolio.reserved_cash)
    # print("Positions:", david.portfolio.positions)
    # print("Reserved Positions:", david.portfolio.reserved_positions)


    # print("\n========== ORDER BOOK ==========")

    # print("\nBUY ORDERS:")
    # for order in ex.order_book.buy_orders:
    #     print(
    #         f"ID={order.order_id}, "
    #         f"Trader={order.trader.name}, "
    #         f"Asset={order.asset}, "
    #         f"Quantity={order.quantity}, "
    #         f"Price={order.price}"
    #     )

    # print("\nSELL ORDERS:")
    # for order in ex.order_book.sell_orders:
    #     print(
    #         f"ID={order.order_id}, "
    #         f"Trader={order.trader.name}, "
    #         f"Asset={order.asset}, "
    #         f"Quantity={order.quantity}, "
    #         f"Price={order.price}"
    #     )

    # print("\n========== TRADES ==========")

    # for trade in ex.order_book.trades:
    #     print(
    #         f"Buyer={trade.buyer.name}, "
    #         f"Seller={trade.seller.name}, "
    #         f"Asset={trade.asset}, "
    #         f"Quantity={trade.quantity}, "
    #         f"Price={trade.price}"
    #     )


    # print("\n========== ASSETS ==========")
    # print(ex.order_book.assets)