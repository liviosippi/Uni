def process_orders(orders: list[dict]) -> dict:
    book = {}
    executions = []

    sorted_orders = sorted(orders, key=lambda x: x['ts'])

    for order in sorted_orders:
        ticker = order['symbol']
        side = order['side']

        if ticker not in book:
            book[ticker] = {'bids': [], 'asks': []}

        bids = book[ticker]['bids']
        asks = book[ticker]['asks']

        # MARKET ORDERS
        if order['px'] == 0:
            if side == 'B':  # market buy

                while order['qty'] > 0 and asks:
                    best_ask = asks[0]
                    traded_vol = min(order['qty'], best_ask['qty'])

                    executions.append({
                        "exec_id": f"e{len(executions)+1:04d}",
                        "ts": order['ts'],
                        "symbol": ticker,
                        "price": best_ask['px'],
                        "qty": traded_vol,
                        "buy_order_id": order['order_id'],
                        "buy_participant_id": order['participant_id'],
                        "sell_order_id": best_ask['order_id'],
                        "sell_participant_id": best_ask['participant_id']
                    })

                    order['qty'] -= traded_vol
                    best_ask['qty'] -= traded_vol

                    if best_ask['qty'] == 0:
                        asks.pop(0)

            else:  # market sell
                # match against individual resting bid orders
                while order['qty'] > 0 and bids:
                    best_bid = bids[0]
                    traded_vol = min(order['qty'], best_bid['qty'])

                    executions.append({
                        "exec_id": f"e{len(executions)+1:04d}",
                        "ts": order['ts'],
                        "symbol": ticker,
                        "price": best_bid['px'],
                        "qty": traded_vol,
                        "buy_order_id": best_bid['order_id'],
                        "buy_participant_id": best_bid['participant_id'],
                        "sell_order_id": order['order_id'],
                        "sell_participant_id": order['participant_id']
                    })

                    order['qty'] -= traded_vol
                    best_bid['qty'] -= traded_vol
                    if best_bid['qty'] == 0:
                        bids.pop(0)

        # LIMIT ORDERS
        else:
            if side == 'B':  # buy limit

                while order['qty'] > 0 and asks and order['px'] >= asks[0]['px']:
                    best_ask = asks[0]
                    traded_vol = min(order['qty'], best_ask['qty'])

                    executions.append({
                        "exec_id": f"e{len(executions)+1:04d}",
                        "ts": order['ts'],
                        "symbol": ticker,
                        "price": best_ask['px'],
                        "qty": traded_vol,
                        "buy_order_id": order['order_id'],
                        "buy_participant_id": order['participant_id'],
                        "sell_order_id": best_ask['order_id'],
                        "sell_participant_id": best_ask['participant_id']
                    })

                    order['qty'] -= traded_vol
                    best_ask['qty'] -= traded_vol
                    if best_ask['qty'] == 0:
                        asks.pop(0)

                # if the buy order isn't totally matched, it creates liquidity
                if order['qty'] > 0:
                    # add the remaining portion of the order to the book
                    bids.append({
                        'px': order['px'],
                        'qty': order['qty'],
                        'order_id': order['order_id'],
                        'participant_id': order['participant_id'],
                        'ts': order['ts']
                    })
                    # sort by descending price, ascending time and order_id
                    bids.sort(key=lambda x: (-x['px'], x['ts'], x['order_id']))

            else:  # sell limit
                # try to cross (take liquidity)
                while order['qty'] > 0 and bids and order['px'] <= bids[0]['px']:
                    best_bid = bids[0]
                    traded_vol = min(order['qty'], best_bid['qty'])

                    executions.append({
                        "exec_id": f"e{len(executions)+1:04d}",
                        "ts": order['ts'],
                        "symbol": ticker,
                        "price": best_bid['px'],
                        "qty": traded_vol,
                        "buy_order_id": best_bid['order_id'],
                        "buy_participant_id": best_bid['participant_id'],
                        "sell_order_id": order['order_id'],
                        "sell_participant_id": order['participant_id']
                    })

                    order['qty'] -= traded_vol
                    best_bid['qty'] -= traded_vol
                    if best_bid['qty'] == 0:
                        bids.pop(0)

                # if the sell order isn't totally matched, it creates liquidity
                if order['qty'] > 0:
                    # add the remaining portion of the order to the book
                    asks.append({
                        'px': order['px'],
                        'qty': order['qty'],
                        'order_id': order['order_id'],
                        'participant_id': order['participant_id'],
                        'ts': order['ts'] # Store timestamp for FIFO sort
                    })
                    # sort by price then time and then order_id
                    asks.sort(key=lambda x: (x['px'], x['ts'], x['order_id']))


    return {"executions": executions, "book": book}