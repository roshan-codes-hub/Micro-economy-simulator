import pytest
from main import Trader, Exchange, Order, OrderSide, OrderStatus

@pytest.fixture
def exchange():
    return Exchange()

@pytest.fixture
def traders():
    alice = Trader("Alice", 1000)
    bob = Trader("Bob", 1000)

    return alice, bob

def test_basic_trade(exchange, traders):
    alice, bob = traders
    bob.portfolio.positions["TECH"] = 10

    order1 = Order(
        trader = alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=5,
        price=100
    )
    order2 = Order(
        trader=bob,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=5,
        price=90
    )

    ex = exchange

    ex.submit_order(order1)
    ex.submit_order(order2)

    assert order1.status == OrderStatus.FILLED
    assert order2.status == OrderStatus.FILLED

    tech_book = ex.order_book_manager.get_order_book("TECH")
    assert alice.portfolio.cash == 550
    assert alice.portfolio.reserved_cash == 0
    assert alice.portfolio.positions["TECH"] == 5

    assert bob.portfolio.cash == 1450
    assert bob.portfolio.positions["TECH"] == 5
    assert bob.portfolio.reserved_positions["TECH"] == 0

    assert len(tech_book.trades) == 1

    trade = tech_book.trades[0]

    assert trade.buyer == alice
    assert trade.seller == bob
    assert trade.asset == "TECH"
    assert trade.quantity == 5
    assert trade.price == 90

    assert len(tech_book.buy_orders) == 0
    assert len(tech_book.sell_orders) == 0

def test_partial_fill(exchange):
    alice = Trader("Alice", 1000)
    bob = Trader("Bob", 1000)
    bob.portfolio.positions["TECH"] = 10

    order1 = Order(
        trader = alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=10,
        price=100
    )
    order2 = Order(
        trader=bob,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=4,
        price=90
    )

    ex = exchange
    
    ex.submit_order(order1)
    ex.submit_order(order2)

    assert order1.status == OrderStatus.PARTIALLY_FILLED
    assert order2.status == OrderStatus.FILLED

    tech_book = ex.order_book_manager.get_order_book("TECH")

    assert alice.portfolio.cash == 640
    assert alice.portfolio.reserved_cash == 600
    assert alice.portfolio.positions["TECH"] == 4
    
    assert bob.portfolio.cash == 1360
    assert bob.portfolio.positions["TECH"] == 6
    assert bob.portfolio.reserved_positions["TECH"] == 0

    assert len(tech_book.trades) == 1

    trade = tech_book.trades[0]
    
    assert trade.buyer == alice
    assert trade.seller == bob
    assert trade.asset == "TECH"
    assert trade.quantity == 4
    assert trade.price == 90
    
    assert len(tech_book.buy_orders) == 1
    assert len(tech_book.sell_orders) == 0

def test_no_match_when_buy_price_below_sell_price(exchange):
    alice = Trader("Alice", 1000)
    bob = Trader("Bob", 1000)
    bob.portfolio.positions["TECH"] = 10

    order1 = Order(
        trader = alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=5,
        price=90
    )
    order2 = Order(
        trader=bob,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=5,
        price=100
    )

    ex = exchange
    
    ex.submit_order(order1)
    ex.submit_order(order2)

    tech_book = ex.order_book_manager.get_order_book("TECH")

    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 450
    assert len(alice.portfolio.positions) == 0
    
    assert bob.portfolio.cash == 1000
    assert bob.portfolio.positions["TECH"] == 10
    assert bob.portfolio.reserved_positions["TECH"] == 5

    assert len(tech_book.trades) == 0

def test_price_time_priority(exchange):
    alice = Trader("Alice", 1000)
    bob = Trader("Bob", 1000)
    charlie = Trader("Charlie", 1000)
    charlie.portfolio.positions["TECH"] = 10

    order1 = Order(
        trader = alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=3,
        price=100
    )
    order2 = Order(
        trader=bob,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=3,
        price=100
    )
    order3 = Order(
        trader=charlie,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=4,
        price=100
    )

    ex = exchange
    
    ex.submit_order(order1)
    ex.submit_order(order2)
    ex.submit_order(order3)

    tech_book = ex.order_book_manager.get_order_book("TECH")

    assert alice.portfolio.cash == 700
    assert alice.portfolio.reserved_cash == 0
    assert alice.portfolio.positions["TECH"] == 3

    assert bob.portfolio.cash == 900
    assert bob.portfolio.reserved_cash == 200
    assert bob.portfolio.positions["TECH"] == 1
    
    assert charlie.portfolio.cash == 1400
    assert charlie.portfolio.positions["TECH"] == 6
    assert charlie.portfolio.reserved_positions["TECH"] == 0

    assert len(tech_book.trades) == 2

    trade1 = tech_book.trades[0]
    
    assert trade1.buyer == alice
    assert trade1.seller == charlie
    assert trade1.asset == "TECH"
    assert trade1.quantity == 3
    assert trade1.price == 100

    trade2 = tech_book.trades[1]
    
    assert trade2.buyer == bob
    assert trade2.seller == charlie
    assert trade2.asset == "TECH"
    assert trade2.quantity == 1
    assert trade2.price == 100

    
    assert len(tech_book.buy_orders) == 1
    assert len(tech_book.sell_orders) == 0

def test_multi_asset_isolation(exchange):
    alice = Trader("Alice", 10000)
    bob = Trader("Bob", 10000)
    charlie = Trader("Charlie", 10000)
    david = Trader("David", 10000)
    david.portfolio.positions["TECH"] = 5

    ex = exchange

    order1 = Order(
        trader = alice,
        asset = "TECH",
        side=OrderSide.BUY,
        original_quantity=  3, 
        price=100
    )
    ex.submit_order(order1)
    order2 = Order(
        trader=bob,
        asset="GOLD",
        side=OrderSide.BUY,
        original_quantity=3, 
        price=100
    )
    ex.submit_order(order2)

    order3 = Order(
        trader = charlie,
        asset = "TECH",
        side=OrderSide.BUY,
        original_quantity=3, 
        price=100
    )
    ex.submit_order(order3)
    order4 = Order(
        trader = david,
        asset = "TECH",
        side=OrderSide.SELL,
        original_quantity = 5, 
        price=100
    )
    ex.submit_order(order4)

    tech_book = ex.order_book_manager.get_order_book("TECH")
    gold_book = ex.order_book_manager.get_order_book("GOLD")

    assert tech_book is not gold_book

    assert tech_book.asset == "TECH"
    assert gold_book.asset == "GOLD"

    assert alice.portfolio.cash == 9700
    assert alice.portfolio.reserved_cash == 0
    assert alice.portfolio.positions["TECH"] == 3

    assert bob.portfolio.cash == 10000
    assert bob.portfolio.reserved_cash == 300
    assert len(bob.portfolio.positions) == 0

    assert charlie.portfolio.cash == 9800
    assert charlie.portfolio.reserved_cash == 100
    assert charlie.portfolio.positions["TECH"] == 2

    assert david.portfolio.cash == 10500
    assert david.portfolio.positions["TECH"] == 0
    assert david.portfolio.reserved_positions["TECH"] == 0

    assert len(tech_book.trades) == 2

    trade1 = tech_book.trades[0]
    
    assert trade1.buyer == alice
    assert trade1.seller == david
    assert trade1.asset == "TECH"
    assert trade1.quantity == 3
    assert trade1.price == 100

    trade2 = tech_book.trades[1]
    
    assert trade2.buyer == charlie
    assert trade2.seller == david
    assert trade2.asset == "TECH"
    assert trade2.quantity == 2
    assert trade2.price == 100

    assert len(tech_book.buy_orders) == 1
    assert len(gold_book.buy_orders) == 1

    assert len(tech_book.sell_orders) == 0
    assert len(gold_book.sell_orders) == 0

def test_buy_rejected_when_insufficient_available_cash(exchange, traders):
    alice, bob = traders

    ex = exchange
    order1 = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=5,
        price=100
    )
    ex.submit_order(order1)
    order2 = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=6,
        price=100
    )

    with pytest.raises(ValueError):
        ex.submit_order(order2)
    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 500
    assert alice.portfolio.positions.get("TECH", 0) == 0
    
def test_sell_rejected_when_insufficient_available_holdings(exchange, traders):
    alice, bob = traders
    alice.portfolio.positions["TECH"] = 5
    alice.portfolio.reserved_positions["TECH"] = 0

    ex = exchange
    order1 = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=4,
        price=100
    )
    ex.submit_order(order1)

    order2 = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=2,
        price=100
    )
    with pytest.raises(ValueError):
        ex.submit_order(order2)
    assert alice.portfolio.cash == 1000
    assert alice.portfolio.positions.get("TECH", 0) == 5
    assert alice.portfolio.reserved_positions.get("TECH", 0) == 4

def test_multiple_partial_fills(exchange, traders):
    alice, bob = traders
    charlie = Trader("Charlie", 1000)

    bob.portfolio.positions["TECH"] = 5
    charlie.portfolio.positions["TECH"] = 5

    ex = exchange

    order1 = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=10,
        price=100
    )
    ex.submit_order(order1)

    assert alice.portfolio.reserved_cash == 1000

    order2 = Order(
        trader=bob,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=4,
        price=90
    )
    assert bob.portfolio.positions.get("TECH", 0) == 5
    assert bob.portfolio.reserved_positions.get("TECH", 0) == 0

    ex.submit_order(order2)

    assert alice.portfolio.cash == 640
    assert alice.portfolio.reserved_cash == 600
    assert alice.portfolio.positions.get("TECH") == 4

    assert bob.portfolio.cash == 1360
    assert bob.portfolio.positions.get("TECH", 0) == 1
    assert bob.portfolio.reserved_positions.get("TECH", 0) == 0

    order3 = Order(
        trader=charlie,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=3,
        price=95
    )
    assert charlie.portfolio.positions.get("TECH", 0) == 5
    assert charlie.portfolio.reserved_positions.get("TECH", 0) == 0

    ex.submit_order(order3)
    assert alice.portfolio.cash == 355
    assert alice.portfolio.reserved_cash == 300
    assert alice.portfolio.positions.get("TECH") == 7

    assert charlie.portfolio.cash == 1285
    assert charlie.portfolio.positions.get("TECH", 0) == 2
    assert charlie.portfolio.reserved_positions.get("TECH", 0) == 0

    tech_book = ex.order_book_manager.get_order_book("TECH")
    assert len(tech_book.trades) == 2

    trade1 = tech_book.trades[0]
    
    assert trade1.buyer == alice
    assert trade1.seller == bob
    assert trade1.asset == "TECH"
    assert trade1.quantity == 4
    assert trade1.price == 90

    trade2 = tech_book.trades[1]
    
    assert trade2.buyer == alice
    assert trade2.seller == charlie
    assert trade2.asset == "TECH"
    assert trade2.quantity == 3
    assert trade2.price == 95

    assert len(tech_book.buy_orders) == 1
    assert len(tech_book.sell_orders) == 0

def test_cancel_unfilled_buy_order(exchange, traders):
    alice, bob = traders

    ex = exchange

    order1 = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=5,
        price=100
    )
    ex.submit_order(order1)
    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 500
    assert alice.portfolio.positions.get("TECH", 0) == 0

    ex.cancel_order(order1.order_id)

    assert order1.status == OrderStatus.CANCELLED
    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 0
    assert alice.portfolio.positions.get("TECH", 0) == 0

    tech_book = ex.order_book_manager.get_order_book("TECH")
    assert len(tech_book.trades) == 0
    assert len(tech_book.buy_orders) == 0
    assert len(tech_book.sell_orders) == 0

def test_new_order_starts_open():
    alice = Trader("Alice", 1000)

    order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=5,
        price=90
    )

    assert order.status == OrderStatus.OPEN

def test_multiple_partial_fills_then_final_fill(exchange):
    alice = Trader("Alice", 1000)
    bob = Trader("Bob", 1000)
    charlie = Trader("Charlie", 1000)
    david = Trader("David", 1000)

    bob.portfolio.positions["TECH"] = 4
    charlie.portfolio.positions["TECH"] = 3
    david.portfolio.positions["TECH"] = 3

    ex = exchange

    # Alice places a 10-share BUY order
    buy_order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=10,
        price=100
    )
    ex.submit_order(buy_order)

    # First partial fill: 4 shares
    sell_order1 = Order(
        trader=bob,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=4,
        price=90
    )
    ex.submit_order(sell_order1)

    assert buy_order.status == OrderStatus.PARTIALLY_FILLED
    assert buy_order.remaining_quantity == 6

    # Second partial fill: 3 shares
    sell_order2 = Order(
        trader=charlie,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=3,
        price=95
    )
    ex.submit_order(sell_order2)

    assert buy_order.status == OrderStatus.PARTIALLY_FILLED
    assert buy_order.remaining_quantity == 3

    # Final fill: remaining 3 shares
    sell_order3 = Order(
        trader=david,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=3,
        price=100
    )
    ex.submit_order(sell_order3)

    # Alice's original order is now completely filled
    assert buy_order.status == OrderStatus.FILLED
    assert buy_order.remaining_quantity == 0

    assert buy_order.original_quantity == 10

    # The order should no longer be in the book
    tech_book = ex.order_book_manager.get_order_book("TECH")

    assert len(tech_book.buy_orders) == 0
    assert len(tech_book.sell_orders) == 0

    # Three executions should have occurred
    assert len(tech_book.trades) == 3

    assert tech_book.trades[0].quantity == 4
    assert tech_book.trades[1].quantity == 3
    assert tech_book.trades[2].quantity == 3

def test_order_tracks_original_and_remaining_quantity():
    order = Order(
        trader=Trader("Alice", 1000),
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=10,
        price=100
    )

    assert order.original_quantity == 10
    assert order.remaining_quantity == 10

def test_order_rejected_when_quantity_is_zero(exchange, traders):
    alice, bob = traders

    order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=0,
        price=100
    )

    with pytest.raises(ValueError):
        exchange.submit_order(order)

    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 0

    tech_book = exchange.order_book_manager.get_order_book("TECH")

    assert len(tech_book.buy_orders) == 0
    assert len(tech_book.sell_orders) == 0
    assert len(tech_book.trades) == 0

def test_order_rejected_when_quantity_is_negative(exchange, traders):
    alice, bob = traders

    order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=-5,
        price=100
    )

    with pytest.raises(ValueError):
        exchange.submit_order(order)

    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 0

    tech_book = exchange.order_book_manager.get_order_book("TECH")

    assert len(tech_book.buy_orders) == 0
    assert len(tech_book.sell_orders) == 0
    assert len(tech_book.trades) == 0

def test_order_rejected_when_price_is_zero(exchange, traders):
    alice, bob = traders

    order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=5,
        price=0
    )

    with pytest.raises(ValueError):
        exchange.submit_order(order)

    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 0

    tech_book = exchange.order_book_manager.get_order_book("TECH")

    assert len(tech_book.buy_orders) == 0
    assert len(tech_book.sell_orders) == 0
    assert len(tech_book.trades) == 0

def test_order_rejected_when_price_is_negative(exchange, traders):
    alice, bob = traders

    order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=5,
        price=-100
    )

    with pytest.raises(ValueError):
        exchange.submit_order(order)

    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 0

    tech_book = exchange.order_book_manager.get_order_book("TECH")

    assert len(tech_book.buy_orders) == 0
    assert len(tech_book.sell_orders) == 0
    assert len(tech_book.trades) == 0

def test_order_rejected_when_asset_is_empty(exchange, traders):
    alice, bob = traders

    order = Order(
        trader=alice,
        asset="",
        side=OrderSide.BUY,
        original_quantity=5,
        price=100
    )

    with pytest.raises(ValueError):
        exchange.submit_order(order)

    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 0

    # The invalid order should not create an order book
    assert "" not in exchange.order_book_manager.order_books

def test_order_rejected_when_side_is_invalid(exchange, traders):
    alice, bob = traders

    order = Order(
        trader=alice,
        asset="TECH",
        side="INVALID",
        original_quantity=5,
        price=100
    )

    with pytest.raises(ValueError):
        exchange.submit_order(order)

    assert alice.portfolio.cash == 1000
    assert alice.portfolio.reserved_cash == 0

    assert exchange.order_book_manager.order_books == {}

def test_cancel_changes_order_status(exchange, traders):
    alice, bob = traders

    order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=5,
        price=100
    )

    exchange.submit_order(order)
    exchange.cancel_order(order.order_id)

    assert order.status == OrderStatus.CANCELLED
    assert order.remaining_quantity == 5

def test_cancel_partially_filled_buy_order(exchange):
    alice = Trader("Alice", 1000)
    bob = Trader("Bob", 1000)

    bob.portfolio.positions["TECH"] = 4

    # Alice buys 10
    buy_order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=10,
        price=100
    )

    exchange.submit_order(buy_order)

    # Bob sells 4
    sell_order = Order(
        trader=bob,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=4,
        price=90
    )

    exchange.submit_order(sell_order)

    # Verify partial fill
    assert buy_order.status == OrderStatus.PARTIALLY_FILLED
    assert buy_order.original_quantity == 10
    assert buy_order.remaining_quantity == 6

    assert alice.portfolio.cash == 640
    assert alice.portfolio.reserved_cash == 600
    assert alice.portfolio.positions["TECH"] == 4

    # Cancel the remaining 6
    exchange.cancel_order(buy_order.order_id)

    # Only the remaining reservation is released
    assert buy_order.status == OrderStatus.CANCELLED
    assert buy_order.remaining_quantity == 6

    assert alice.portfolio.cash == 640
    assert alice.portfolio.reserved_cash == 0
    assert alice.portfolio.positions["TECH"] == 4

    tech_book = exchange.order_book_manager.get_order_book("TECH")

    assert len(tech_book.buy_orders) == 0
    assert len(tech_book.sell_orders) == 0
    assert len(tech_book.trades) == 1

def test_filled_order_cannot_be_cancelled(exchange):
    alice = Trader("Alice", 1000)
    bob = Trader("Bob", 1000)

    bob.portfolio.positions["TECH"] = 5

    buy_order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.BUY,
        original_quantity=5,
        price=100
    )

    sell_order = Order(
        trader=bob,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=5,
        price=90
    )

    exchange.submit_order(buy_order)
    exchange.submit_order(sell_order)

    assert buy_order.status == OrderStatus.FILLED
    assert sell_order.status == OrderStatus.FILLED

    assert alice.portfolio.cash == 550
    assert alice.portfolio.positions["TECH"] == 5

    assert bob.portfolio.cash == 1450
    assert bob.portfolio.positions["TECH"] == 0

    with pytest.raises(ValueError):
        exchange.cancel_order(buy_order.order_id)

    # State must remain unchanged
    assert buy_order.status == OrderStatus.FILLED
    assert buy_order.remaining_quantity == 0

    assert alice.portfolio.cash == 550
    assert alice.portfolio.positions["TECH"] == 5

    tech_book = exchange.order_book_manager.get_order_book("TECH")
    assert len(tech_book.trades) == 1

def test_cancel_unfilled_sell_order(exchange):
    alice = Trader("Alice", 1000)
    alice.portfolio.positions["TECH"] = 10

    ex = exchange
    order = Order(
        trader=alice,
        asset="TECH",
        side=OrderSide.SELL,
        original_quantity=5,
        price=100
    )

    ex.submit_order(order)

    assert alice.portfolio.positions["TECH"] == 10
    assert alice.portfolio.reserved_positions.get("TECH", 0) == 5
    assert order.status == OrderStatus.OPEN

    ex.cancel_order(order.order_id)

    assert alice.portfolio.positions["TECH"] == 10
    assert alice.portfolio.reserved_positions.get("TECH", 0) == 0
    assert order.status == OrderStatus.CANCELLED

    tech_book = ex.order_book_manager.get_order_book("TECH")
    assert not tech_book == True
