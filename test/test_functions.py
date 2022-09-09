from asyncore import read
import pandas as pd
from function_source.functions import *
from pandas.testing import assert_frame_equal



def test_read_csv():
    df = ReadCSVandCleanDF("./csv_for_test/testfile1.csv")
    d = {
        "timestamp":['2022-06-15 09:23:00', '2022-06-15 09:25:00', '2022-06-15 09:27:00'], \
        "store":["Chesterfield", "Chesterfield", "Chesterfield"], \
        "basket_items": ['Regular Flavoured iced latte - Caramel - 2.75, Regular Flavoured iced latte - Vanilla - 2.75, Regular Flavoured iced latte - Hazelnut - 2.75, Large Flavoured iced latte - Hazelnut - 3.25, Large Flat white - 2.45', 'Large Flavoured iced latte - Vanilla - 3.25', 'Large Flavoured iced latte - Hazelnut - 3.25, Regular Flavoured latte - Hazelnut - 2.55, Large Flavoured latte - Hazelnut - 2.85, Regular Flavoured latte - Hazelnut - 2.55, Large Latte - 2.45'], \
        "total_price": [13.95, 3.25, 13.65], \
        "cash_or_card": ['CARD', 'CASH', 'CARD']\
        }
    df1 = pd.DataFrame(data=d, index=["3340786902", "7210250588", "6409276043"])
    df1.index.name = 'transaction_hash_id'
    assert_frame_equal(df, df1)


def test_exploded_items():
    df = ExplodedItems(ReadCSVandCleanDF("./csv_for_test/testfile1.csv"))
    d = {
        0:['Regular Flavoured iced latte - Caramel', 'Regular Flavoured iced latte - Vanilla', 'Regular Flavoured iced latte - Hazelnut', 'Large Flavoured iced latte - Hazelnut', 'Large Flat white', 'Large Flavoured iced latte - Vanilla', 'Large Flavoured iced latte - Hazelnut', 'Regular Flavoured latte - Hazelnut', 'Large Flavoured latte - Hazelnut', 'Regular Flavoured latte - Hazelnut', 'Large Latte'], \
        1:['2.75', '2.75', '2.75', '3.25', '2.45', '3.25', '3.25', '2.55', '2.85', '2.55', '2.45']
    }
    df1 = pd.DataFrame(data=d, index=['3340786902', '3340786902', '3340786902', '3340786902', '3340786902', '7210250588', '6409276043', '6409276043', '6409276043', '6409276043', '6409276043'])
    df1.index.name = "transaction_hash_id"
    assert_frame_equal(df, df1)


def test_store_df():
    store_id = LoadStore(ReadCSVandCleanDF("./csv_for_test/testfile1.csv"), 1)
    assert store_id == "2895903154"


def test_product_df():
    product_list = LoadProduct(ExplodedItems(ReadCSVandCleanDF("./csv_for_test/testfile1.csv")), 1)
    d = {
        "product_name": ['Regular Flavoured iced latte - Caramel', 'Regular Flavoured iced latte - Vanilla', 'Regular Flavoured iced latte - Hazelnut', 'Large Flavoured iced latte - Hazelnut', 'Large Flat white', 'Large Flavoured iced latte - Vanilla', 'Regular Flavoured latte - Hazelnut', 'Large Flavoured latte - Hazelnut', 'Large Latte'], \
        "price": ['2.75', '2.75', '2.75', '3.25', '2.45', '3.25', '2.55', '2.85', '2.45'], \
        "product_id": ['4870177303', '5330105066', '2720354948', '1046796418', '1135483680', '4754352824', '1021488178', '4944274648', '7209298201']
    }
    df1 = pd.DataFrame(data=d)
    assert_frame_equal(product_list, df1)


def test_transaction_df():
    transaction = LoadTransactionDF(ReadCSVandCleanDF("./csv_for_test/testfile1.csv"), LoadStore(ReadCSVandCleanDF("./csv_for_test/testfile1.csv"), 1), 1)
    print(transaction)
    d = {
        'transaction_hash_id': ['3340786902', '7210250588', '6409276043'], \
        'timestamp': ['2022-06-15 09:23:00', '2022-06-15 09:25:00', '2022-06-15 09:27:00'], \
        'store_id': ['2895903154', '2895903154', '2895903154'], \
        'total_price': [13.95, 3.25, 13.65], \
        'payment_method': ["CARD", 'CASH', 'CARD']
    }
    df1 = pd.DataFrame(data=d)
    return assert_frame_equal(df1, transaction)


def test_basket_df():
    basket_items = LoadBasketItemsDF(ExplodedItems(ReadCSVandCleanDF("./csv_for_test/testfile1.csv")), LoadProduct(ExplodedItems(ReadCSVandCleanDF("./csv_for_test/testfile1.csv")), 1), 1)
    d = {
        "transaction_hash_id": ['3340786902', '3340786902', '3340786902', '3340786902', '3340786902', '6409276043', '6409276043', '6409276043', '6409276043','7210250588'], \
        "product_id": ['4870177303', '5330105066', '2720354948', '1046796418', '1135483680', '1021488178', '1046796418', '4944274648', '7209298201', '4754352824'], \
        "quantity": [1, 1, 1, 1, 1, 2, 1, 1, 1, 1]
    }
    df1 = pd.DataFrame(data=d)
    assert_frame_equal(basket_items, df1)