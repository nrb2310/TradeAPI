#!/usr/bin/env python
# coding: utf-8

# In[24]:


from flask import Flask, Response, request # A web framework for building web applications
from typing import List, Optional  # Provides type hints for function signatures
import mysql.connector # A library for connecting to MySQL databases
from pydantic import BaseModel, Field # A library for data validation and serialization
import json # Provides functions for working with JSON data
import datetime as dt # Allows working with date and time values

app = Flask(__name__) # Creating a Flask application instance


# Define the TradeDetails class representing the details of a trade
class TradeDetails(BaseModel):
    buySellIndicator: str = Field(..., description="A value of BUY for buys, SELL for sells.")
    price: float = Field(..., description="The price of the Trade.")
    quantity: int = Field(..., description="The amount of units traded.")


# Define the Trade class representing a trade object
class Trade(BaseModel):
    asset_class: Optional[str] = Field(alias="asset_class", description="The asset class of the instrument traded. E.g. Bond, Equity, FX...etc")
    counterparty: Optional[str] = Field(default=None, description="The counterparty the trade was executed with. May not always be available")
    instrument_id: str = Field(alias="instrument_id", description="The ISIN/ID of the instrument traded. E.g. TSLA, AAPL, AMZN...etc")
    instrument_name: str = Field(alias="instrument_name", description="The name of the instrument traded.")
    trade_date_time: dt.datetime = Field(alias="trade_date_time", description="The date-time the Trade was executed")
    trade_details: TradeDetails = Field(alias="trade_details", description="The details of the trade, i.e. price, quantity")
    trade_id: str = Field(alias="trade_id", description="The unique ID of the trade")
    trader: str = Field(description="The name of the Trader")


# Function to fetch trades from the database based on given filters
def fetch_trades_from_db(asset_class: Optional[str] = None, start: Optional[dt.datetime] = None, end: Optional[dt.datetime] = None,
                         min_price: Optional[float] = None, max_price: Optional[float] = None, trade_type: Optional[str] = None,
                         page: Optional[int] = None, page_size: Optional[int] = None, sort_by: Optional[str] = None,
                         sort_order: Optional[str] = None):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mysql@2310",
            database="assignment"
        )
        cursor = connection.cursor()

        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        # Add filters to the SQL query based on the provided parameters
        if asset_class:
            query += " AND asset_class = %s"
            params.append(asset_class)
        if start:
            query += " AND trade_date_time >= %s"
            params.append(start)
        if end:
            query += " AND trade_date_time <= %s"
            params.append(end)
        if min_price:
            query += " AND price >= %s"
            params.append(min_price)
        if max_price:
            query += " AND price <= %s"
            params.append(max_price)
        if trade_type:
            query += " AND buySellIndicator = %s"
            params.append(trade_type)
        
        # Add sorting to the SQL query based on the provided parameters
        if sort_by:
            sort_column = "trade_date_time" if sort_by == "trade_date_time" else "trade_details.price"
            sort_order = sort_order or "asc"
            query += f" ORDER BY {sort_column} {sort_order.upper()}"

        # Add pagination to the SQL query based on the provided parameters
        if page is not None and page_size is not None:
            offset = page * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"

        # Execute the SQL query and fetch the results
        cursor.execute(query, tuple(params))

        # Convert the results to a list of Trade objects
        trades = []
        for trade_data in cursor.fetchall():
            trade = Trade(
                asset_class=trade_data[0],
                counterparty=trade_data[1],
                instrument_id=trade_data[2],
                instrument_name=trade_data[3],
                trade_date_time=trade_data[4],
                trade_details=TradeDetails(
                    buySellIndicator=trade_data[5],
                    price=float(trade_data[6]),
                    quantity=trade_data[7]
                ),
                trade_id=trade_data[8],
                trader=trade_data[9],
            )
            trades.append(trade.dict())

        cursor.close()
        connection.close()
        return trades
    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL: {error}")
        return []


# Function to fetch a single trade from the database based on given trade Id
def fetch_trade_by_id(trade_id):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mysql@2310",
            database="assignment"
        )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM trades WHERE trade_id = %s", (trade_id,))
        trade_data = cursor.fetchone()
        if trade_data:
            trade = Trade(
                asset_class=trade_data[0],
                counterparty=trade_data[1],
                instrument_id=trade_data[2],
                instrument_name=trade_data[3],
                trade_date_time=trade_data[4],
                trade_details=TradeDetails(
                    buySellIndicator=trade_data[5],
                    price=float(trade_data[6]),
                    quantity=trade_data[7]
                ),
                trade_id=trade_data[8],
                trader=trade_data[9],
            )
            return trade.dict()
        else:
            return None
        cursor.close()
        connection.close()
    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL: {error}")
        return None


# Function to fetch a trades from the database based on given filters
def filter_trades_by_search(trades, search_query):
    filtered_trades = []
    for trade in trades:
        if (
            search_query.lower() in trade.get("counterparty", "").lower()
            or search_query.lower() in trade.get("instrument_id", "").lower()
            or search_query.lower() in trade.get("instrument_name", "").lower()
            or search_query.lower() in trade.get("trader", "").lower()
        ):
            filtered_trades.append(trade)
    return filtered_trades


# Route for the home page
class HomePage:
        @app.route("/", methods=["GET"])
        def home():
            introduction = """
        Welcome to the Trades API!

        Here are the available endpoints:

        1. Retrieve all trades:
           http://192.168.0.106:8000/trades

        2. Retrieve a trade by ID:
           http://192.168.0.106:8000/trades/<trade_id>

        3. Search trades:
           http://192.168.0.106:8000/trades?search=<search_query>

        4. Filter trades:
           http://192.168.0.106:8000/trades/filter?asset_class=<asset_class>&start=<start_date>&end=<end_date>&min_price=<min_price>&max_price=<max_price>&trade_type=<trade_type>&page=<page>&page_size=<page_size>&sort_by=<sort_by>&sort_order=<sort_order>

        Note: Replace <trade_id>, <search_query>, <asset_class>, <start_date>, <end_date>, <min_price>, <max_price>, <trade_type>, <page>, <page_size>, <sort_by>, and <sort_order> with the desired values.

        """
            return Response(introduction, content_type="text/plain")


# Route for fetching trades
class TradesPage:
    @app.route("/trades", methods=["GET"])
    @app.route("/trades/<trade_id>", methods=["GET"])
    def get_trades(trade_id=None):
        search_query = request.args.get("search")
        asset_class = request.args.get("asset_class")
        start = request.args.get("start")
        end = request.args.get("end")
        min_price = request.args.get("min_price")
        max_price = request.args.get("max_price")
        trade_type = request.args.get("trade_type")
        page = int(request.args.get("page", "0"))
        page_size = int(request.args.get("page_size", "10"))
        sort_by = request.args.get("sort_by")
        sort_order = request.args.get("sort_order")

        # Parse the query parameters to appropriate types
        if trade_id:
            trade = fetch_trade_by_id(trade_id)
            if trade:
                # Serialize the trade objects to JSON
                response = json.dumps(trade, indent=4, default=str)
                # Return the JSON response
                return Response(response, content_type="application/json")
            else:
                return Response("Trade not found", status=404)
        else:
            # Fetch the trades from the database based on the query parameters
            try:
                trades = fetch_trades_from_db(asset_class=asset_class, start=start, end=end,
                                              min_price=min_price, max_price=max_price, trade_type=trade_type,
                                              page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
                if search_query:
                    trades = filter_trades_by_search(trades, search_query)
                response = json.dumps(trades, indent=4, default=str)
                return Response(response, content_type="application/json")
            except Exception as e:
                print(f"Error fetching trades from database: {e}")
                return Response("An error occurred", status=500)


# This section allows you to run the Flask application locally on your machine using the specified IP address and port.
if __name__ == "__main__":
    HomePage()
    TradesPage()
    app.run(host="0.0.0.0", port=8000)


# In[ ]:




